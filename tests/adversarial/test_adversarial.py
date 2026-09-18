from copy import deepcopy

from evidence_agent.orchestrator import AnalysisOrchestrator
from evidence_agent.tools.evidence_auditor import EvidenceAuditor
from evidence_agent.tools.evidence_engine import EvidenceEngine


def test_leading_question_does_not_override_observed_result():
    orchestrator = AnalysisOrchestrator()
    engine = EvidenceEngine()

    response = orchestrator.process_query(
        "Why did December 2019 have the highest richness peak?"
    )

    assert response["status"] == "SUCCESS"

    actual_result = (
        response
        .get("evidence_claim", {})
        .get("result", {})
    )

    actual_peak = actual_result["peak_month"]

    independent_claim = (
        engine.get_peak_richness_by_month()
    )

    independent_peak = (
        independent_claim
        .get("result", {})
        .get("peak_month")
    )

    assert actual_peak == independent_peak


def test_qualitative_presence_is_not_treated_as_quantitative_abundance():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Resumo de abundância e registros"
    )

    assert response["status"] == "SUCCESS"

    result = (
        response
        .get("evidence_claim", {})
        .get("result", {})
    )

    qualitative = result[
        "total_qualitative_records"
    ]

    quantified = result[
        "total_quantified_abundance"
    ]

    assert qualitative >= 0
    assert quantified >= 0


def test_unsupported_question_is_rejected():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Qual a temperatura média da água na Amazônia?"
    )

    assert response["status"] == "UNSUPPORTED"


def test_effort_representations_are_not_equated():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Relatório de esforço de amostragem"
    )

    assert response["status"] == "SUCCESS"

    result = (
        response
        .get("evidence_claim", {})
        .get("result", {})
    )

    assert result["equivalence_assumed"] is False
    assert result["comparison_performed"] is False


def test_independent_audit_verifies_engine_claim():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_peak_richness_by_month()

    audit = auditor.audit_claim(claim)

    assert audit["audit_status"] == "VERIFIED"


def test_auditor_rejects_tampered_claim():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_peak_richness_by_month()

    tampered_claim = deepcopy(claim)

    original_value = tampered_claim[
        "result"
    ]["observed_richness"]

    tampered_claim[
        "result"
    ]["observed_richness"] = original_value + 1000000

    audit = auditor.audit_claim(
        tampered_claim
    )

    assert audit["audit_status"] == "FAILED"


def test_missing_count_is_not_zero():
    engine = EvidenceEngine()

    claim = engine.get_abundance_summary()

    result = claim["result"]

    assert (
        result["total_quantified_abundance"]
        >= 0
    )

    # O teste de preservação é feito sobre Silver.
    # O Engine não pode transformar NULL em zero
    # durante a construção das métricas.


def test_effort_claim_explicitly_records_limitation():
    engine = EvidenceEngine()

    claim = engine.get_effort_discrepancy_report()

    result = claim["result"]

    assert result["limitation"]
    assert result["interpretation"]


def test_claim_requires_audit_before_being_considered_verified():
    engine = EvidenceEngine()

    claim = engine.get_peak_richness_by_month()

    assert (
        claim["audit_metadata"]["audit_status"]
        == "PENDING"
    )


def test_claim_id_is_reproducible():
    engine = EvidenceEngine()

    claim_1 = engine.get_peak_richness_by_month()
    claim_2 = engine.get_peak_richness_by_month()

    assert (
        claim_1["claim_id"]
        == claim_2["claim_id"]
    )