from pathlib import Path
from typing import Dict

import pandas as pd


class AnalyticalPipeline:
    """
    Constrói as tabelas analíticas Gold a partir das tabelas Silver.

    Princípios:
    - Silver preserva a estrutura ingerida e validada.
    - Gold contém representações derivadas para análises específicas.
    - Nenhuma ausência de contagem é convertida silenciosamente em zero.
    - Esforços provenientes de estruturas diferentes não são tratados como
      equivalentes automaticamente.
    """

    def __init__(self, base_dir: Path = Path("data")):
        self.base_dir = base_dir
        self.silver_dir = base_dir / "silver_processed"
        self.output_dir = base_dir / "gold_analytical"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_sources(self):
        event_path = self.silver_dir / "eventos.csv"
        occurrence_path = self.silver_dir / "ocorrencias.csv"
        inventory_path = self.silver_dir / "inventarios.csv"

        required = [
            event_path,
            occurrence_path,
            inventory_path,
        ]

        for path in required:
            if not path.exists():
                raise FileNotFoundError(
                    f"Arquivo Silver necessário não encontrado: {path}"
                )

        events = pd.read_csv(event_path, dtype=str, keep_default_na=False)
        occurrences = pd.read_csv(
            occurrence_path,
            dtype=str,
            keep_default_na=False,
        )
        inventories = pd.read_csv(
            inventory_path,
            dtype=str,
            keep_default_na=False,
        )

        return events, occurrences, inventories

    @staticmethod
    def _require_columns(df: pd.DataFrame, columns, table_name: str):
        missing = [column for column in columns if column not in df.columns]

        if missing:
            raise ValueError(
                f"A tabela '{table_name}' não possui as colunas necessárias: "
                f"{missing}"
            )

    @staticmethod
    def _empty_to_na(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte apenas strings vazias em NA.

        Não transforma valores semânticos como 'absent', 'mostly' etc.
        """
        result = df.copy()

        for column in result.columns:
            result[column] = result[column].replace("", pd.NA)

        return result

    def generate_all_tables(self) -> Dict[str, int]:
        print("🚀 Iniciando geração das tabelas analíticas Gold...")

        events, occurrences, inventories = self._load_sources()

        events = self._empty_to_na(events)
        occurrences = self._empty_to_na(occurrences)
        inventories = self._empty_to_na(inventories)

        richness_event = self._build_richness(events, occurrences)
        richness_event.to_csv(
            self.output_dir / "richness_event.csv",
            index=False,
        )

        richness_month = self._build_richness_by_month(
            events,
            occurrences,
        )
        richness_month.to_csv(
            self.output_dir / "richness_month.csv",
            index=False,
        )

        abundance_event = self._build_abundance(occurrences)
        abundance_event.to_csv(
            self.output_dir / "abundance_event.csv",
            index=False,
        )

        composition_event = self._build_composition(occurrences)
        composition_event.to_csv(
            self.output_dir / "composition_event.csv",
            index=False,
        )

        effort_event = self._build_effort(events, inventories)
        effort_event.to_csv(
            self.output_dir / "effort_event.csv",
            index=False,
        )

        result = {
            "richness_event": len(richness_event),
            "richness_month": len(richness_month),
            "abundance_event": len(abundance_event),
            "composition_event": len(composition_event),
            "effort_event": len(effort_event),
        }

        print(
            f"✅ Tabelas Gold geradas em '{self.output_dir}'."
        )

        for name, count in result.items():
            print(f"   {name}: {count:,} registros")

        return result

    def _build_richness(
        self,
        events: pd.DataFrame,
        occurrences: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calcula riqueza observada por evento.

        Riqueza = número de táxons distintos detectados como present.
        """

        self._require_columns(
            occurrences,
            [
                "eventID",
                "occurrenceStatus",
                "scientificName",
            ],
            "occurrence",
        )

        present = occurrences[
            occurrences["occurrenceStatus"].str.lower() == "present"
        ].copy()

        present["scientificName"] = present["scientificName"].str.strip()

        present = present[
            present["scientificName"].notna()
            & (present["scientificName"] != "")
        ]

        richness = (
            present.groupby("eventID")["scientificName"]
            .nunique()
            .reset_index(name="observed_richness")
        )

        # Garante que eventos sem nenhuma ocorrência presente continuem
        # representados com riqueza zero.
        event_ids = events[["eventID"]].drop_duplicates()

        richness = event_ids.merge(
            richness,
            on="eventID",
            how="left",
        )

        richness["observed_richness"] = (
            richness["observed_richness"]
            .fillna(0)
            .astype(int)
        )

        return richness

    def _build_richness_by_month(
        self,
        events: pd.DataFrame,
        occurrences: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calcula riqueza acumulada por mês.

        Importante:
        a riqueza mensal é o número de espécies únicas detectadas no mês,
        e NÃO a soma da riqueza dos eventos daquele mês.
        """

        self._require_columns(
            events,
            ["eventID", "eventDate"],
            "event",
        )

        self._require_columns(
            occurrences,
            [
                "eventID",
                "occurrenceStatus",
                "scientificName",
            ],
            "occurrence",
        )

        event_dates = events[
            ["eventID", "eventDate"]
        ].drop_duplicates("eventID").copy()

        event_dates["eventDate"] = pd.to_datetime(
            event_dates["eventDate"],
            errors="coerce",
        )

        event_dates = event_dates[
            event_dates["eventDate"].notna()
        ].copy()

        event_dates["year_month"] = (
            event_dates["eventDate"]
            .dt.to_period("M")
            .astype(str)
        )

        present = occurrences[
            occurrences["occurrenceStatus"].str.lower() == "present"
        ].copy()

        present["scientificName"] = present["scientificName"].str.strip()

        present = present[
            present["scientificName"].notna()
            & (present["scientificName"] != "")
        ]

        merged = present.merge(
            event_dates[
                ["eventID", "year_month"]
            ],
            on="eventID",
            how="inner",
        )

        monthly = (
            merged.groupby("year_month")["scientificName"]
            .nunique()
            .reset_index(name="observed_richness")
        )

        monthly = monthly.sort_values("year_month")

        return monthly

    def _build_abundance(
        self,
        occurrences: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calcula abundância quantitativa e mantém separadas as ocorrências
        presentes sem contagem numérica.
        """

        self._require_columns(
            occurrences,
            [
                "eventID",
                "occurrenceID",
                "occurrenceStatus",
                "individualCount",
            ],
            "occurrence",
        )

        present = occurrences[
            occurrences["occurrenceStatus"].str.lower() == "present"
        ].copy()

        present["individualCount_num"] = pd.to_numeric(
            present["individualCount"],
            errors="coerce",
        )

        abundance = (
            present.groupby("eventID")
            .agg(
                total_quantified_abundance=(
                    "individualCount_num",
                    lambda values: values.sum(min_count=1),
                ),
                qualitative_presence_count=(
                    "individualCount_num",
                    lambda values: int(values.isna().sum()),
                ),
                total_records=("occurrenceID", "count"),
            )
            .reset_index()
        )

        return abundance

    def _build_composition(
        self,
        occurrences: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Mantém a composição em formato longo:

        eventID | scientificName

        Isso permite reutilização em análises posteriores de comunidade.
        """

        self._require_columns(
            occurrences,
            [
                "eventID",
                "occurrenceStatus",
                "scientificName",
            ],
            "occurrence",
        )

        present = occurrences[
            occurrences["occurrenceStatus"].str.lower() == "present"
        ].copy()

        present["scientificName"] = present["scientificName"].str.strip()

        composition = (
            present[
                [
                    "eventID",
                    "scientificName",
                ]
            ]
            .dropna()
            .drop_duplicates()
            .sort_values(
                [
                    "eventID",
                    "scientificName",
                ]
            )
            .reset_index(drop=True)
        )

        return composition

    def _build_effort(
        self,
        events: pd.DataFrame,
        inventories: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Constrói uma representação de esforço sem assumir que
        sampleSizeValue/sampleSizeUnit e
        samplingEffortValue/samplingEffortUnit
        representam a mesma grandeza.

        A relação Humboldt → evento prioriza a correspondência direta entre
        inventários filhos e eventID. Quando ela não existe, usa
        parentEventID como fallback para registros agregados.
        """

        self._require_columns(
            events,
            [
                "eventID",
                "parentEventID",
                "sampleSizeValue",
                "sampleSizeUnit",
                "samplingProtocol",
            ],
            "event",
        )

        self._require_columns(
            inventories,
            [
                "id",
                "samplingEffortValue",
                "samplingEffortUnit",
            ],
            "humboldt",
        )

        event_effort = events[
            [
                "eventID",
                "parentEventID",
                "samplingProtocol",
                "sampleSizeValue",
                "sampleSizeUnit",
            ]
        ].copy()

        inventory_effort = inventories[
            [
                "id",
                "samplingEffortValue",
                "samplingEffortUnit",
            ]
        ].copy()

        inventory_effort = inventory_effort.rename(
            columns={
                "id": "inventory_id",
            }
        )

        # Evita multiplicação de eventos caso existam múltiplos registros
        # Humboldt para o mesmo inventário.
        inventory_summary = (
            inventory_effort
            .groupby("inventory_id", dropna=False)
            .agg(
                humboldt_effort_record_count=(
                    "samplingEffortValue",
                    "size",
                ),
                humboldt_effort_values=(
                    "samplingEffortValue",
                    lambda x: "|".join(
                        sorted(
                            {
                                str(v)
                                for v in x.dropna()
                            }
                        )
                    ),
                ),
                humboldt_effort_units=(
                    "samplingEffortUnit",
                    lambda x: "|".join(
                        sorted(
                            {
                                str(v)
                                for v in x.dropna()
                            }
                        )
                    ),
                ),
            )
            .reset_index()
        )

        direct_effort = event_effort.merge(
            inventory_summary,
            left_on="eventID",
            right_on="inventory_id",
            how="left",
        )

        parent_effort = event_effort.merge(
            inventory_summary,
            left_on="parentEventID",
            right_on="inventory_id",
            how="left",
        )

        effort = direct_effort[event_effort.columns].copy()

        for column in [
            "humboldt_effort_record_count",
            "humboldt_effort_values",
            "humboldt_effort_units",
        ]:
            direct_values = direct_effort[column].replace("", pd.NA)
            parent_values = parent_effort[column].replace("", pd.NA)
            effort[column] = direct_values.combine_first(parent_values)

        # Mantemos parentEventID porque ele é relevante para a interpretação
        # da estrutura hierárquica da amostragem.
        return effort


if __name__ == "__main__":
    pipeline = AnalyticalPipeline()
    pipeline.generate_all_tables()