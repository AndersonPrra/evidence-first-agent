from __future__ import annotations

from typing import Any, Dict

import pandas as pd


class DataProfiler:
    """
    Gera um perfil determinístico das tabelas.

    O profiler não interpreta ecologicamente os dados.
    Ele apenas descreve propriedades observáveis.
    """

    def profile_dataframe(
        self,
        df: pd.DataFrame,
        name: str,
    ) -> Dict[str, Any]:

        columns = []

        for column in df.columns:

            series = df[column]

            missing = int(
                series.isna().sum()
            )

            non_missing = int(
                series.notna().sum()
            )

            unique = int(
                series.nunique(
                    dropna=True
                )
            )

            column_info = {
                "name": column,
                "dtype": str(series.dtype),
                "total_records": len(series),
                "missing_records": missing,
                "missing_rate": (
                    missing / len(series)
                    if len(series) > 0
                    else 0
                ),
                "non_missing_records": non_missing,
                "unique_values": unique,
            }

            # Numérico

            if pd.api.types.is_numeric_dtype(series):

                numeric = pd.to_numeric(
                    series,
                    errors="coerce",
                )

                column_info["numeric"] = {
                    "min": self._safe_value(
                        numeric.min()
                    ),
                    "max": self._safe_value(
                        numeric.max()
                    ),
                    "mean": self._safe_value(
                        numeric.mean()
                    ),
                    "median": self._safe_value(
                        numeric.median()
                    ),
                }

            # Categórico / texto

            else:

                values = (
                    series
                    .dropna()
                    .astype(str)
                )

                top_values = (
                    values
                    .value_counts()
                    .head(10)
                    .to_dict()
                )

                column_info["top_values"] = {
                    str(key): int(value)
                    for key, value in top_values.items()
                }

            columns.append(
                column_info
            )

        return {
            "table": name,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "columns_profile": columns,
        }

    @staticmethod
    def _safe_value(
        value: Any,
    ) -> Any:

        if pd.isna(value):
            return None

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        return value

    def profile_dataset(
        self,
        events: pd.DataFrame,
        occurrences: pd.DataFrame,
        inventories: pd.DataFrame,
    ) -> Dict[str, Any]:

        profile = {
            "events": self.profile_dataframe(
                events,
                "eventos",
            ),
            "occurrences": self.profile_dataframe(
                occurrences,
                "ocorrencias",
            ),
            "inventories": self.profile_dataframe(
                inventories,
                "inventarios",
            ),
        }

        # Informações específicas do domínio

        if "eventDate" in events.columns:

            dates = pd.to_datetime(
                events["eventDate"],
                errors="coerce",
            )

            profile["domain"] = {
                "temporal_range": {
                    "min": (
                        dates.min().isoformat()
                        if dates.notna().any()
                        else None
                    ),
                    "max": (
                        dates.max().isoformat()
                        if dates.notna().any()
                        else None
                    ),
                }
            }

        if "samplingProtocol" in events.columns:

            profile["domain"][
                "sampling_protocols"
            ] = sorted(
                events["samplingProtocol"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        if "locationID" in events.columns:

            profile["domain"][
                "locations"
            ] = sorted(
                events["locationID"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        if "scientificName" in occurrences.columns:

            profile["domain"][
                "unique_taxa"
            ] = int(
                occurrences["scientificName"]
                .nunique(
                    dropna=True
                )
            )

        if "occurrenceStatus" in occurrences.columns:

            profile["domain"][
                "occurrence_status"
            ] = {
                str(key): int(value)
                for key, value in (
                    occurrences[
                        "occurrenceStatus"
                    ]
                    .value_counts(
                        dropna=False
                    )
                    .to_dict()
                    .items()
                )
            }

        if {
            "samplingEffortValue",
            "samplingEffortUnit",
        }.issubset(inventories.columns):

            profile["domain"][
                "humboldt_effort_units"
            ] = sorted(
                inventories[
                    "samplingEffortUnit"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        if {
            "sampleSizeValue",
            "sampleSizeUnit",
        }.issubset(events.columns):

            profile["domain"][
                "event_effort_units"
            ] = sorted(
                events[
                    "sampleSizeUnit"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        return profile