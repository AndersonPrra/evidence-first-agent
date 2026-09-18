from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


class EvidenceEngine:
    """
    Gera Evidence Claims a partir das representações analíticas Gold.

    O Engine calcula resultados.
    Ele não declara que os resultados foram auditados.
    A auditoria é responsabilidade do EvidenceAuditor.
    """

    def __init__(
        self,
        base_dir: Path = Path("data"),
    ):
        self.base_dir = base_dir
        self.gold_dir = base_dir / "gold_analytical"
        self.silver_dir = base_dir / "silver_processed"

    def _generate_claim_id(
        self,
        analysis_name: str,
        params: Dict[str, Any],
    ) -> str:
        raw = (
            f"{analysis_name}_"
            f"{json.dumps(params, sort_keys=True, ensure_ascii=False)}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:12]

    def _create_evidence_claim(
        self,
        analysis_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        data_source: str,
    ) -> Dict[str, Any]:

        return {
            "claim_id": self._generate_claim_id(
                analysis_name,
                params,
            ),
            "timestamp": datetime.now(UTC).isoformat(),
            "analysis_name": analysis_name,
            "data_source": data_source,
            "parameters": params,
            "result": result,
            "audit_metadata": {
                "execution_status": "SUCCESS",
                "is_reproducible": True,
                "audit_status": "PENDING",
            },
        }

    def get_peak_richness_by_month(self) -> Dict[str, Any]:
        """
        Identifica o mês com maior riqueza observada acumulada.

        A riqueza mensal corresponde ao número de espécies únicas detectadas
        naquele mês.
        """

        path = self.gold_dir / "richness_month.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Tabela analítica não encontrada: {path}"
            )

        df = pd.read_csv(path)

        required = [
            "year_month",
            "observed_richness",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Colunas ausentes em richness_month.csv: {missing}"
            )

        df["observed_richness"] = pd.to_numeric(
            df["observed_richness"],
            errors="coerce",
        )

        df = df.dropna(
            subset=[
                "year_month",
                "observed_richness",
            ]
        )

        if df.empty:
            raise ValueError(
                "Não existem dados suficientes para calcular riqueza mensal."
            )

        max_value = df["observed_richness"].max()

        # Tratamos empates explicitamente.
        peaks = df[
            df["observed_richness"] == max_value
        ].sort_values("year_month")

        peak_months = peaks["year_month"].tolist()

        return self._create_evidence_claim(
            analysis_name="peak_richness_by_month",
            params={},
            result={
                "peak_month": peak_months[0],
                "peak_months": peak_months,
                "observed_richness": int(max_value),
                "is_tied": len(peak_months) > 1,
            },
            data_source="gold_analytical/richness_month.csv",
        )

    def get_abundance_summary(self) -> Dict[str, Any]:
        """
        Resume abundância quantitativa e registros qualitativos.

        Presença sem individualCount NÃO é convertida em zero.
        """

        path = self.gold_dir / "abundance_event.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Tabela analítica não encontrada: {path}"
            )

        df = pd.read_csv(path)

        required = [
            "total_quantified_abundance",
            "qualitative_presence_count",
            "total_records",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Colunas ausentes em abundance_event.csv: {missing}"
            )

        df["total_quantified_abundance"] = pd.to_numeric(
            df["total_quantified_abundance"],
            errors="coerce",
        )

        total_quantified = float(
            df["total_quantified_abundance"].sum(
                skipna=True
            )
        )

        total_qualitative = int(
            pd.to_numeric(
                df["qualitative_presence_count"],
                errors="coerce",
            ).fillna(0).sum()
        )

        total_records = int(
            pd.to_numeric(
                df["total_records"],
                errors="coerce",
            ).fillna(0).sum()
        )

        qualitative_ratio = (
            total_qualitative / total_records
            if total_records > 0
            else None
        )

        return self._create_evidence_claim(
            analysis_name="abundance_summary",
            params={},
            result={
                "total_quantified_abundance": total_quantified,
                "total_qualitative_records": total_qualitative,
                "total_records_analyzed": total_records,
                "qualitative_ratio": (
                    round(qualitative_ratio, 4)
                    if qualitative_ratio is not None
                    else None
                ),
            },
            data_source="gold_analytical/abundance_event.csv",
        )

    def get_effort_discrepancy_report(self) -> Dict[str, Any]:
        """
        Descreve as diferentes representações de esforço presentes no dataset.

        O método preserva as métricas de esforço provenientes de estruturas
        diferentes e não assume equivalência sem evidência explícita no
        esquema ou nos metadados.
        """

        path = self.gold_dir / "effort_event.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Tabela analítica não encontrada: {path}"
            )

        df = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
        )

        required = [
            "sampleSizeValue",
            "sampleSizeUnit",
            "humboldt_effort_values",
            "humboldt_effort_units",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Colunas ausentes em effort_event.csv: {missing}"
            )

        # ---------------------------------------------------------
        # Representação de esforço no evento
        # ---------------------------------------------------------

        event_effort = pd.to_numeric(
            df["sampleSizeValue"],
            errors="coerce",
        )

        has_event_effort = event_effort.notna()

        # ---------------------------------------------------------
        # Representação de esforço Humboldt
        # ---------------------------------------------------------

        humboldt_effort = df[
            "humboldt_effort_values"
        ].replace("", pd.NA)

        has_humboldt_effort = humboldt_effort.notna()

        # ---------------------------------------------------------
        # Relação estrutural entre as representações
        # ---------------------------------------------------------

        both = int(
            (has_event_effort & has_humboldt_effort).sum()
        )

        only_event = int(
            (has_event_effort & ~has_humboldt_effort).sum()
        )

        only_humboldt = int(
            (~has_event_effort & has_humboldt_effort).sum()
        )

        # ---------------------------------------------------------
        # Preservação das unidades
        # ---------------------------------------------------------

        event_units = sorted(
            {
                str(value).strip()
                for value in df["sampleSizeUnit"]
                if str(value).strip()
            }
        )

        humboldt_units = sorted(
            {
                str(value).strip()
                for value in df["humboldt_effort_units"]
                if str(value).strip()
            }
        )

        # ---------------------------------------------------------
        # Regra de segurança
        # ---------------------------------------------------------

        # Mesmo que exista compatibilidade matemática entre unidades,
        # não assumimos equivalência sem evidência semântica/metadados.
        equivalence_assumed = False

        return self._create_evidence_claim(
            analysis_name="effort_discrepancy_report",
            params={},
            result={
                "events_with_both_effort_representations": both,
                "events_with_only_event_effort": only_event,
                "events_with_only_humboldt_effort": only_humboldt,
                "event_effort_units": event_units,
                "humboldt_effort_units": humboldt_units,
                "equivalence_assumed": equivalence_assumed,
                "comparison_performed": False,
                "interpretation": (
                    "As métricas de esforço provenientes das estruturas "
                    "event e Humboldt foram mantidas separadas. "
                    "O sistema não assume que representam a mesma medida "
                    "sem evidência explícita no esquema ou metadados."
                ),
                "limitation": (
                    "Não foi realizada conversão ou agregação entre "
                    "as diferentes representações de esforço."
                ),
                "total_event_records": len(df),
            },
            data_source="gold_analytical/effort_event.csv",
        )


if __name__ == "__main__":
    engine = EvidenceEngine()

    print("--- Testando Evidence Engine ---")

    evidence = engine.get_peak_richness_by_month()

    print(
        json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
        )
    )