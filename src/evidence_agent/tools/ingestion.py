from __future__ import annotations

import json
import math
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
from pydantic import ValidationError

from evidence_agent.contracts.domain import (EventSchema, HumboldtInventorySchema, OccurrenceSchema,)
from evidence_agent.contracts.quality import (IssueSeverity, QualityIssue, QualityReport, SchemaValidationSummary,)


class DwCAIngestionTool:
    """
    Ferramenta determinística responsável por:

    1. Ler os arquivos originais.
    2. Validar estrutura básica.
    3. Avaliar relacionamentos.
    4. Avaliar problemas semânticos.
    5. Produzir a camada Silver.
    6. Persistir o relatório de qualidade.

    A ferramenta NÃO altera os arquivos Bronze.
    """

    REQUIRED_FILES = {
        "eventos": "event.txt",
        "ocorrencias": "occurrence.txt",
        "inventarios": "humboldtecologicalinventory.txt",}

    def __init__(
        self,
        raw_dir: str = "data/bronze_raw",
        processed_dir: str = "data/silver_processed",
        execution_dir: str = "execucoes",
):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.execution_dir = Path(execution_dir)

        self.processed_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.execution_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # LEITURA

    def load_raw_tables(
        self,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        paths = {
            nome: self.raw_dir / arquivo
            for nome, arquivo in self.REQUIRED_FILES.items()
        }

        for nome, path in paths.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"Arquivo obrigatório não encontrado para "
                    f"'{nome}': {path}"
                )

        print(f"📖 Lendo arquivos Bronze: {self.raw_dir}")

        df_events = pd.read_csv(
            paths["eventos"],
            sep="\t",
            low_memory=False,
        )

        df_occurrences = pd.read_csv(
            paths["ocorrencias"],
            sep="\t",
            low_memory=False,
        )

        df_humboldt = pd.read_csv(
            paths["inventarios"],
            sep="\t",
            low_memory=False,
        )

        return (
            df_events,
            df_occurrences,
            df_humboldt,
        )

    # AUXILIARES

    @staticmethod
    def _is_missing(value: Any) -> bool:
        """
        Trata NaN e None como valores ausentes.
        """

        if value is None:
            return True

        try:
            return bool(pd.isna(value))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _json_safe(value: Any) -> Any:
        """
        Converte valores pandas/numpy para valores serializáveis.
        """

        if value is None:
            return None

        if isinstance(value, float) and math.isnan(value):
            return None

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        if isinstance(value, dict):
            return {
                str(k): DwCAIngestionTool._json_safe(v)
                for k, v in value.items()
            }

        if isinstance(value, list):
            return [
                DwCAIngestionTool._json_safe(v)
                for v in value
            ]

        return value

    # UNICIDADE

    def _check_duplicates(
        self,
        df: pd.DataFrame,
        column: str,
    ) -> int:

        if column not in df.columns:
            return 0

        return int(
            df[column]
            .dropna()
            .duplicated()
            .sum()
        )

    # REFERÊNCIAS

    def _check_occurrence_references(
        self,
        df_events: pd.DataFrame,
        df_occurrences: pd.DataFrame,
    ) -> tuple[int, set]:

        event_ids = set(
            df_events["eventID"]
            .dropna()
            .astype(str)
        )

        occurrence_event_ids = set(
            df_occurrences["eventID"]
            .dropna()
            .astype(str)
        )

        unmatched = (
            occurrence_event_ids
            - event_ids
        )

        return len(unmatched), unmatched

    def _check_humboldt_hierarchy(
        self,
        df_events: pd.DataFrame,
        df_humboldt: pd.DataFrame,
    ) -> tuple[int, set]:

        """
        Não assume que Humboldt.id seja necessariamente um eventID.
        Primeiro verificamos correspondência direta.
        Depois a relação pode ser investigada por:

            Humboldt.id
                ↓
            Event.parentEventID
                ↓
            Event.eventID

        A função retorna apenas os IDs que não possuem
        correspondência direta nem como parentEventID.
        """

        event_ids = set(
            df_events["eventID"]
            .dropna()
            .astype(str)
        )

        parent_event_ids = set()

        if "parentEventID" in df_events.columns:
            parent_event_ids = set(
                df_events["parentEventID"]
                .dropna()
                .astype(str)
            )

        humboldt_ids = set(
            df_humboldt["id"]
            .dropna()
            .astype(str)
        )

        unmatched = {
            value
            for value in humboldt_ids
            if value not in event_ids
            and value not in parent_event_ids
        }

        return len(unmatched), unmatched

    # VALIDAÇÃO PYDANTIC

    def _validate_records(
        self,
        df: pd.DataFrame,
        schema_class,
    ) -> SchemaValidationSummary:

        total_invalid = 0

        errors_by_field = Counter()
        errors_by_type = Counter()

        examples = []

        for index, record in enumerate(
            df.to_dict(orient="records")
        ):

            # --------------------------------------------------
            # Pandas utiliza NaN para valores ausentes.
            # Convertemos NaN para None antes da validação.
            # --------------------------------------------------

            normalized_record = {}

            for key, value in record.items():
                if self._is_missing(value):
                    normalized_record[key] = None
                else:
                    normalized_record[key] = value

            try:
                schema_class(**normalized_record)

            except ValidationError as error:
                total_invalid += 1

                for detail in error.errors():

                    field = ".".join(
                        str(item)
                        for item in detail.get("loc", [])
                    )

                    error_type = detail.get(
                        "type",
                        "unknown",
                    )

                    errors_by_field[field] += 1
                    errors_by_type[error_type] += 1

                    if len(examples) < 10:
                        examples.append(
                            {
                                "row_index": index,
                                "field": field,
                                "type": error_type,
                                "message": detail.get(
                                    "msg",
                                    "",
                                ),
                                "input": self._json_safe(
                                    detail.get("input")
                                ),
                            }
                        )

        return SchemaValidationSummary(
            total_invalid_records=total_invalid,
            errors_by_field=dict(errors_by_field),
            errors_by_type=dict(errors_by_type),
            examples=examples,
        )

    # REGRAS SEMÂNTICAS

    def _check_occurrence_semantics(
        self,
        df_occurrences: pd.DataFrame,
    ) -> list[QualityIssue]:

        issues = []

        if {
            "occurrenceStatus",
            "individualCount",
        }.issubset(df_occurrences.columns):

            absent_with_count = (
                (
                    df_occurrences["occurrenceStatus"]
                    .astype(str)
                    .str.lower()
                    == "absent"
                )
                &
                (
                    pd.to_numeric(
                        df_occurrences["individualCount"],
                        errors="coerce",
                    )
                    > 0
                )
            )

            count = int(absent_with_count.sum())

            if count > 0:
                issues.append(
                    QualityIssue(
                        code="ABSENT_WITH_POSITIVE_COUNT",
                        severity=IssueSeverity.WARNING,
                        description=(
                            "Existem registros classificados como "
                            "'absent' com contagem positiva de indivíduos."
                        ),
                        affected_records=count,
                    )
                )

        if {
            "occurrenceStatus",
            "individualCount",
        }.issubset(df_occurrences.columns):

            present_without_count = (
                (
                    df_occurrences["occurrenceStatus"]
                    .astype(str)
                    .str.lower()
                    == "present"
                )
                &
                (
                    df_occurrences["individualCount"].isna()
                )
            )

            count = int(
                present_without_count.sum()
            )

            if count > 0:
                issues.append(
                    QualityIssue(
                        code="PRESENT_WITHOUT_QUANTITATIVE_COUNT",
                        severity=IssueSeverity.INFO,
                        description=(
                            "Existem ocorrências presentes sem "
                            "contagem quantitativa de indivíduos."
                        ),
                        affected_records=count,
                    )
                )

        return issues

    # PROTOCOLOS

    def _inspect_protocols(
        self,
        df_events: pd.DataFrame,
    ) -> QualityIssue | None:

        if "samplingProtocol" not in df_events.columns:
            return QualityIssue(
                code="MISSING_SAMPLING_PROTOCOL",
                severity=IssueSeverity.WARNING,
                description=(
                    "A coluna samplingProtocol não está disponível."
                ),
                affected_records=len(df_events),
            )

        values = (
            df_events["samplingProtocol"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        unique_protocols = sorted(
            values.unique().tolist()
        )

        if len(unique_protocols) > 1:
            return QualityIssue(
                code="MULTIPLE_SAMPLING_PROTOCOLS",
                severity=IssueSeverity.INFO,
                description=(
                    "Mais de um protocolo de amostragem foi "
                    "identificado. A comparabilidade entre protocolos "
                    "deve ser avaliada antes de agregações."
                ),
                affected_records=len(values),
                details={
                    "protocols": unique_protocols,
                },
            )

        return None

    # ESFORÇO

    def _inspect_effort(
        self,
        df_events: pd.DataFrame,
        df_humboldt: pd.DataFrame,
    ) -> list[QualityIssue]:

        issues = []

        event_units = []

        if "sampleSizeUnit" in df_events.columns:
            event_units = sorted(
                df_events["sampleSizeUnit"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        humboldt_units = []

        if "samplingEffortUnit" in df_humboldt.columns:
            humboldt_units = sorted(
                df_humboldt["samplingEffortUnit"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        if event_units or humboldt_units:
            issues.append(
                QualityIssue(
                    code="EFFORT_FIELDS_PRESENT",
                    severity=IssueSeverity.INFO,
                    description=(
                        "Foram identificados campos de esforço em "
                        "diferentes estruturas do dataset. O sistema "
                        "não deve assumir equivalência entre eles "
                        "sem evidência no esquema ou metadados."
                    ),
                    affected_records=0,
                    details={
                        "event_sample_size_units": event_units,
                        "humboldt_sampling_effort_units": humboldt_units,
                    },
                )
            )

        return issues
    
    # COORDENADAS

    def _check_coordinates(
        self,
        df_events: pd.DataFrame,
    ) -> list[QualityIssue]:

        issues = []

        required = {
            "decimalLatitude",
            "decimalLongitude",
        }

        if not required.issubset(df_events.columns):
            return issues

        latitude = pd.to_numeric(
            df_events["decimalLatitude"],
            errors="coerce",
        )

        longitude = pd.to_numeric(
            df_events["decimalLongitude"],
            errors="coerce",
        )

        invalid = (
            (
                latitude.notna()
                &
                ~latitude.between(-90, 90)
            )
            |
            (
                longitude.notna()
                &
                ~longitude.between(-180, 180)
            )
        )

        invalid_count = int(invalid.sum())

        if invalid_count > 0:
            issues.append(
                QualityIssue(
                    code="INVALID_COORDINATES",
                    severity=IssueSeverity.WARNING,
                    description=(
                        "Foram encontradas coordenadas fora dos "
                        "intervalos geográficos válidos."
                    ),
                    affected_records=invalid_count,
                )
            )

        missing_count = int(
            (
                latitude.isna()
                |
                longitude.isna()
            ).sum()
        )

        if missing_count > 0:
            issues.append(
                QualityIssue(
                    code="MISSING_COORDINATES",
                    severity=IssueSeverity.INFO,
                    description=(
                        "Existem eventos sem coordenadas completas."
                    ),
                    affected_records=missing_count,
                )
            )

        return issues

    # VALIDAÇÃO COMPLETA

    def validate_dataset(
        self,
        df_events: pd.DataFrame,
        df_occurrences: pd.DataFrame,
        df_humboldt: pd.DataFrame,
    ) -> QualityReport:

        issues = []

        # Unicidade

        duplicate_events = self._check_duplicates(
            df_events,
            "eventID",
        )

        duplicate_occurrences = self._check_duplicates(
            df_occurrences,
            "occurrenceID",
        )

        if duplicate_events > 0:
            issues.append(
                QualityIssue(
                    code="DUPLICATE_EVENT_ID",
                    severity=IssueSeverity.CRITICAL,
                    description=(
                        "Existem eventIDs duplicados."
                    ),
                    affected_records=duplicate_events,
                )
            )

        if duplicate_occurrences > 0:
            issues.append(
                QualityIssue(
                    code="DUPLICATE_OCCURRENCE_ID",
                    severity=IssueSeverity.CRITICAL,
                    description=(
                        "Existem occurrenceIDs duplicados."
                    ),
                    affected_records=duplicate_occurrences,
                )
            )

        # Ocorrência → Evento

        unmatched_occ_count, unmatched_occ = (
            self._check_occurrence_references(
                df_events,
                df_occurrences,
            )
        )

        if unmatched_occ_count > 0:
            issues.append(
                QualityIssue(
                    code="UNMATCHED_OCCURRENCE_REFERENCE",
                    severity=IssueSeverity.CRITICAL,
                    description=(
                        "Existem ocorrências cujo eventID não "
                        "corresponde a um evento conhecido."
                    ),
                    affected_records=unmatched_occ_count,
                    details={
                        "sample_unmatched": list(
                            unmatched_occ
                        )[:10]
                    },
                )
            )

        # Humboldt → hierarquia de eventos

        unmatched_hum_count, unmatched_hum = (
            self._check_humboldt_hierarchy(
                df_events,
                df_humboldt,
            )
        )

        if unmatched_hum_count > 0:
            issues.append(
                QualityIssue(
                    code="UNRESOLVED_HUMBOLDT_REFERENCE",
                    severity=IssueSeverity.WARNING,
                    description=(
                        "Existem identificadores Humboldt que "
                        "não foram resolvidos diretamente como "
                        "eventID nem como parentEventID. "
                        "A relação precisa ser investigada antes "
                        "de tratar o identificador como FK quebrada."
                    ),
                    affected_records=unmatched_hum_count,
                    details={
                        "sample_unmatched": list(
                            unmatched_hum
                        )[:10]
                    },
                )
            )

        # Schema

        event_schema = self._validate_records(
            df_events,
            EventSchema,
        )

        occurrence_schema = self._validate_records(
            df_occurrences,
            OccurrenceSchema,
        )

        humboldt_schema = self._validate_records(
            df_humboldt,
            HumboldtInventorySchema,
        )

        schema_total = (
            event_schema.total_invalid_records
            + occurrence_schema.total_invalid_records
            + humboldt_schema.total_invalid_records
        )

        schema_fields = Counter()

        for summary in [
            event_schema,
            occurrence_schema,
            humboldt_schema,
        ]:
            schema_fields.update(
                summary.errors_by_field
            )

        schema_types = Counter()

        for summary in [
            event_schema,
            occurrence_schema,
            humboldt_schema,
        ]:
            schema_types.update(
                summary.errors_by_type
            )

        schema_examples = (
            event_schema.examples
            + occurrence_schema.examples
            + humboldt_schema.examples
        )[:20]

        schema_summary = SchemaValidationSummary(
            total_invalid_records=schema_total,
            errors_by_field=dict(schema_fields),
            errors_by_type=dict(schema_types),
            examples=schema_examples,
        )

        if schema_total > 0:
            issues.append(
                QualityIssue(
                    code="SCHEMA_VALIDATION_ERRORS",
                    severity=IssueSeverity.WARNING,
                    description=(
                        "Foram encontrados registros que não "
                        "atendem completamente aos schemas definidos."
                    ),
                    affected_records=schema_total,
                    details={
                        "errors_by_field": dict(schema_fields),
                        "errors_by_type": dict(schema_types),
                        "examples": schema_examples,
                    },
                )
            )

        # Semântica

        issues.extend(
            self._check_occurrence_semantics(
                df_occurrences
            )
        )

        protocol_issue = self._inspect_protocols(
            df_events
        )

        if protocol_issue:
            issues.append(protocol_issue)

        issues.extend(
            self._inspect_effort(
                df_events,
                df_humboldt,
            )
        )

        issues.extend(
            self._check_coordinates(
                df_events
            )
        )

        # Relatório

        report = QualityReport(
            total_events=len(df_events),
            total_occurrences=len(df_occurrences),
            total_inventories=len(df_humboldt),
            unmatched_occurrence_references=unmatched_occ_count,
            unmatched_inventory_references=unmatched_hum_count,
            duplicate_events=duplicate_events,
            duplicate_occurrences=duplicate_occurrences,
            schema_validation=schema_summary,
            issues=issues,
        )

        # Limitações analíticas

        if unmatched_hum_count > 0:
            report.analysis_limitations.append(
                "A relação entre inventários Humboldt e eventos "
                "não está completamente resolvida."
            )

        if protocol_issue:
            report.analysis_limitations.append(
                "Existem múltiplos protocolos de amostragem; "
                "comparações entre protocolos devem considerar "
                "a heterogeneidade metodológica."
            )

        if any(
            issue.code == "EFFORT_FIELDS_PRESENT"
            for issue in issues
        ):
            report.analysis_limitations.append(
                "Os campos de esforço possuem diferentes conceitos "
                "e/ou unidades e não devem ser tratados como equivalentes "
                "sem validação."
            )

        report.finalize()

        return report

    # SILVER

    def process_and_save_silver(
        self,
        question: str = "Diagnóstico inicial dos dados",
    ) -> QualityReport:

        (
            df_events,
            df_occurrences,
            df_humboldt,
        ) = self.load_raw_tables()

        print(
            "🔍 Executando diagnóstico determinístico..."
        )

        quality_report = self.validate_dataset(
            df_events,
            df_occurrences,
            df_humboldt,
        )

        # ID da execução

        execution_id = (
            pd.Timestamp.utcnow()
            .strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )

        execution_path = (
            self.execution_dir
            / execution_id
        )

        execution_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------------------
        # Silver
        #
        # Neste estágio NÃO chamamos os dados de "limpos".
        # Eles foram ingeridos, preservados e validados.
        # ------------------------------------------------------

        print(
            "💾 Salvando dados ingeridos e validados "
            "na camada Silver..."
        )

        df_events.to_csv(
            self.processed_dir / "eventos.csv",
            index=False,
        )

        df_occurrences.to_csv(
            self.processed_dir / "ocorrencias.csv",
            index=False,
        )

        df_humboldt.to_csv(
            self.processed_dir / "inventarios.csv",
            index=False,
        )

        # Relatório de qualidade

        quality_path = (
            execution_path
            / "relatorio_qualidade.json"
        )

        quality_path.write_text(
            quality_report.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        # Manifesto básico

        manifest = {
            "execution_id": execution_id,
            "question": question,
            "input_files": [
                str(
                    self.raw_dir / filename
                )
                for filename in self.REQUIRED_FILES.values()
            ],
            "output_files": [
                str(
                    self.processed_dir / "eventos.csv"
                ),
                str(
                    self.processed_dir / "ocorrencias.csv"
                ),
                str(
                    self.processed_dir / "inventarios.csv"
                ),
            ],
            "quality_report": str(
                quality_path
            ),
            "status": (
                "VALIDO"
                if quality_report.is_valid_for_analysis
                else "INVALIDO"
            ),
        }

        (
            execution_path / "manifesto.json"
        ).write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(
            "✅ Ingestão concluída."
        )

        print(
            "📋 Relatório de qualidade:"
        )

        print(
            quality_report.model_dump_json(
                indent=2
            )
        )

        return quality_report


if __name__ == "__main__":

    tool = DwCAIngestionTool()

    tool.process_and_save_silver(
        question=(
            "Como os dados estão estruturados e quais "
            "problemas de qualidade podem afetar a análise "
            "da comunidade de aves?"
        )
    )