from evidence_agent.orchestrator import AnalysisOrchestrator


def test_peak_richness_pipeline_completes():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Qual mês apresentou a maior riqueza observada de espécies de aves?"
    )

    assert response["status"] == "SUCCESS"
    assert response.get("execution_id")
    assert response.get("skill")
    assert response.get("evidence_claim")
    assert response.get("audit_status")
    assert response.get("report_file")


def test_abundance_pipeline_completes():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "O que o conjunto de dados mostra sobre a abundância quantificada?"
    )

    assert response["status"] == "SUCCESS"
    assert response.get("evidence_claim")
    assert response.get("audit_status")


def test_effort_pipeline_completes():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Existem diferenças no esforço de amostragem que possam afetar a interpretação?"
    )

    assert response["status"] == "SUCCESS"

    result = (
        response
        .get("evidence_claim", {})
        .get("result", {})
    )

    assert result["equivalence_assumed"] is False


def test_unsupported_pipeline_is_rejected():
    orchestrator = AnalysisOrchestrator()

    response = orchestrator.process_query(
        "Como estarão as populações de aves em 2050?"
    )

    assert response["status"] == "UNSUPPORTED"