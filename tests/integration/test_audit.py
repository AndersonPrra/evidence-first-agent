from copy import deepcopy

from evidence_agent.tools.evidence_auditor import EvidenceAuditor
from evidence_agent.tools.evidence_engine import EvidenceEngine


def test_peak_richness_is_independently_verified():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_peak_richness_by_month()

    audit = auditor.audit_claim(claim)

    assert audit["audit_status"] == "VERIFIED"


def test_abundance_is_independently_verified():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_abundance_summary()

    audit = auditor.audit_claim(claim)

    assert audit["audit_status"] == "VERIFIED"


def test_effort_claim_is_independently_verified():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_effort_discrepancy_report()

    audit = auditor.audit_claim(claim)

    assert audit["audit_status"] == "VERIFIED"


def test_auditor_detects_tampered_peak_result():
    engine = EvidenceEngine()
    auditor = EvidenceAuditor()

    claim = engine.get_peak_richness_by_month()

    tampered_claim = deepcopy(claim)

    tampered_claim["result"]["peak_month"] = (
        "9999-99"
    )

    audit = auditor.audit_claim(
        tampered_claim
    )

    assert audit["audit_status"] == "FAILED"