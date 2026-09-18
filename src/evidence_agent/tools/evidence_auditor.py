import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


class EvidenceAuditor:
    """
    Verifica Evidence Claims utilizando uma rota de cálculo independente
    daquela usada para gerar o claim.

    Objetivo:
        Engine → gera resultado
        Auditor → recalcula resultado
    """

    def __init__(
        self,
        base_dir: Path = Path("data"),
    ):
        self.base_dir = base_dir
        self.silver_dir = base_dir / "silver_processed"

    def audit_claim(
        self,
        claim: Dict[str, Any],
    ) -> Dict[str, Any]:

        analysis_name = claim.get("analysis_name")

        if analysis_name == "peak_richness_by_month":
            return self._audit_peak_richness(claim)

        if analysis_name == "abundance_summary":
            return self._audit_abundance_summary(claim)

        if analysis_name == "effort_discrepancy_report":
            return self._audit_effort(claim)

        return {
            "claim_id": claim.get("claim_id"),
            "audit_status": "REJECTED",
            "reason": (
                f"Análise '{analysis_name}' não possui "
                "protocolo de auditoria registrado."
            ),
        }

    def _load_silver(self):
        events_path = self.silver_dir / "eventos.csv"
        occurrences_path = self.silver_dir / "ocorrencias.csv"

        if not events_path.exists():
            raise FileNotFoundError(events_path)

        if not occurrences_path.exists():
            raise FileNotFoundError(occurrences_path)

        events = pd.read_csv(
            events_path,
            dtype=str,
            keep_default_na=False,
        )

        occurrences = pd.read_csv(
            occurrences_path,
            dtype=str,
            keep_default_na=False,
        )

        return events, occurrences

    def _audit_peak_richness(
        self,
        claim: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:
            events, occurrences = self._load_silver()

            events["eventDate"] = pd.to_datetime(
                events["eventDate"],
                errors="coerce",
            )

            events = events[
                events["eventDate"].notna()
            ].copy()

            events["year_month"] = (
                events["eventDate"]
                .dt.to_period("M")
                .astype(str)
            )

            present = occurrences[
                occurrences["occurrenceStatus"].str.lower()
                == "present"
            ].copy()

            present["scientificName"] = (
                present["scientificName"]
                .str.strip()
            )

            present = present[
                present["scientificName"].notna()
                & (present["scientificName"] != "")
            ]

            merged = present.merge(
                events[
                    [
                        "eventID",
                        "year_month",
                    ]
                ],
                on="eventID",
                how="inner",
            )

            monthly = (
                merged.groupby("year_month")["scientificName"]
                .nunique()
                .reset_index(name="observed_richness")
            )

            if monthly.empty:
                return {
                    "claim_id": claim.get("claim_id"),
                    "audit_status": "ERROR",
                    "reason": (
                        "Não foi possível recalcular riqueza mensal."
                    ),
                }

            max_value = monthly[
                "observed_richness"
            ].max()

            peaks = monthly[
                monthly["observed_richness"] == max_value
            ].sort_values("year_month")

            expected_months = peaks[
                "year_month"
            ].tolist()

            expected_peak = expected_months[0]

            claim_result = claim.get("result", {})

            claimed_peak = claim_result.get(
                "peak_month"
            )

            claimed_richness = claim_result.get(
                "observed_richness"
            )

            valid = (
                claimed_peak == expected_peak
                and int(claimed_richness)
                == int(max_value)
            )

            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": (
                    "VERIFIED"
                    if valid
                    else "FAILED"
                ),
                "recalculated_values": {
                    "peak_month": expected_peak,
                    "peak_months": expected_months,
                    "observed_richness": int(max_value),
                },
                "discrepancy_detected": not valid,
            }

        except Exception as exc:
            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": "ERROR",
                "reason": str(exc),
            }

    def _audit_abundance_summary(
        self,
        claim: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:
            _, occurrences = self._load_silver()

            present = occurrences[
                occurrences["occurrenceStatus"].str.lower()
                == "present"
            ].copy()

            present["individualCount_num"] = pd.to_numeric(
                present["individualCount"],
                errors="coerce",
            )

            expected_quantified = float(
                present["individualCount_num"].sum(
                    skipna=True
                )
            )

            expected_qualitative = int(
                present["individualCount_num"]
                .isna()
                .sum()
            )

            expected_records = int(
                len(present)
            )

            claim_result = claim.get(
                "result",
                {},
            )

            claimed_quantified = float(
                claim_result.get(
                    "total_quantified_abundance",
                    -1,
                )
            )

            claimed_qualitative = int(
                claim_result.get(
                    "total_qualitative_records",
                    -1,
                )
            )

            claimed_records = int(
                claim_result.get(
                    "total_records_analyzed",
                    -1,
                )
            )

            valid = (
                claimed_quantified
                == expected_quantified
                and claimed_qualitative
                == expected_qualitative
                and claimed_records
                == expected_records
            )

            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": (
                    "VERIFIED"
                    if valid
                    else "FAILED"
                ),
                "recalculated_values": {
                    "total_quantified_abundance":
                        expected_quantified,
                    "total_qualitative_records":
                        expected_qualitative,
                    "total_records_analyzed":
                        expected_records,
                },
                "discrepancy_detected": not valid,
            }

        except Exception as exc:
            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": "ERROR",
                "reason": str(exc),
            }

    def _audit_effort(
        self,
        claim: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:
            events_path = (
                self.silver_dir / "eventos.csv"
            )
            inventories_path = (
                self.silver_dir / "inventarios.csv"
            )

            events = pd.read_csv(
                events_path,
                dtype=str,
                keep_default_na=False,
            )

            inventories = pd.read_csv(
                inventories_path,
                dtype=str,
                keep_default_na=False,
            )

            event_effort = pd.to_numeric(
                events["sampleSizeValue"],
                errors="coerce",
            )

            inventory_ids = set(
                inventories["id"]
                .dropna()
            )

            parent_ids = (
                events["parentEventID"]
                .replace("", pd.NA)
                .dropna()
            )

            linked_inventory_events = int(
                parent_ids.isin(
                    inventory_ids
                ).sum()
            )

            expected = {
                "events_with_event_effort":
                    int(event_effort.notna().sum()),
                "events_with_humboldt_reference":
                    linked_inventory_events,
            }

            result = claim.get(
                "result",
                {},
            )

            # A auditoria aqui valida a estrutura factual,
            # não uma equivalência numérica entre esforços.
            valid = (
                result.get(
                    "total_event_records"
                )
                == len(events)
            )

            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": (
                    "VERIFIED"
                    if valid
                    else "FAILED"
                ),
                "recalculated_values": expected,
                "discrepancy_detected": not valid,
                "note": (
                    "A auditoria não assume equivalência "
                    "entre unidades/conceitos de esforço."
                ),
            }

        except Exception as exc:
            return {
                "claim_id": claim.get("claim_id"),
                "audit_status": "ERROR",
                "reason": str(exc),
            }


if __name__ == "__main__":
    from evidence_agent.tools.evidence_engine import (
        EvidenceEngine,
    )

    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_peak_richness_by_month()

    result = auditor.audit_claim(claim)

    print("--- Resultado da Auditoria ---")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )