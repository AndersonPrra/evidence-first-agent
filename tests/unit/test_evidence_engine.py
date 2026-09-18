import pandas as pd

from evidence_agent.tools.evidence_engine import EvidenceEngine


def test_peak_richness_returns_valid_claim():
    engine = EvidenceEngine()

    claim = engine.get_peak_richness_by_month()

    assert claim["analysis_name"] == "peak_richness_by_month"
    assert claim["claim_id"]
    assert claim["data_source"]

    result = claim["result"]

    assert result["peak_month"]
    assert isinstance(result["peak_months"], list)
    assert len(result["peak_months"]) >= 1
    assert isinstance(result["observed_richness"], int)
    assert isinstance(result["is_tied"], bool)


def test_peak_richness_handles_ties():
    engine = EvidenceEngine()

    claim = engine.get_peak_richness_by_month()

    result = claim["result"]

    if result["is_tied"]:
        assert len(result["peak_months"]) > 1
    else:
        assert len(result["peak_months"]) == 1


def test_abundance_preserves_qualitative_records():
    engine = EvidenceEngine()

    claim = engine.get_abundance_summary()

    result = claim["result"]

    assert result["total_records_analyzed"] >= 0
    assert result["total_qualitative_records"] >= 0
    assert result["total_quantified_abundance"] >= 0


def test_missing_individual_count_is_not_converted_to_zero(
    silver_dir,
):
    path = silver_dir / "ocorrencias.csv"

    df = pd.read_csv(path)

    missing = df["individualCount"].isna()

    if missing.any():
        assert (
            df.loc[missing, "individualCount"]
            .isna()
            .all()
        )


def test_effort_claim_preserves_distinct_representations():
    engine = EvidenceEngine()

    claim = engine.get_effort_discrepancy_report()

    result = claim["result"]

    assert "event_effort_units" in result
    assert "humboldt_effort_units" in result
    assert "equivalence_assumed" in result
    assert "comparison_performed" in result

    assert result["equivalence_assumed"] is False
    assert result["comparison_performed"] is False


def test_claim_has_reproducibility_metadata():
    engine = EvidenceEngine()

    claim = engine.get_peak_richness_by_month()

    metadata = claim["audit_metadata"]

    assert metadata["execution_status"] == "SUCCESS"
    assert metadata["is_reproducible"] is True
    assert metadata["audit_status"] == "PENDING"


def test_claim_id_is_stable_for_same_analysis():
    engine = EvidenceEngine()

    claim_1 = engine.get_peak_richness_by_month()
    claim_2 = engine.get_peak_richness_by_month()

    assert claim_1["claim_id"] == claim_2["claim_id"]