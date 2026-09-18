import json


def test_quality_report_exists(project_root):
    path = (
        project_root
        / "data"
        / "silver_processed"
        / "relatorio_qualidade.json"
    )

    assert path.exists()


def test_quality_report_has_expected_structure(project_root):
    path = (
        project_root
        / "data"
        / "silver_processed"
        / "relatorio_qualidade.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    required_fields = [
        "total_events",
        "total_occurrences",
        "total_inventories",
        "issues",
        "is_valid_for_analysis",
        "analysis_limitations",
    ]

    for field in required_fields:
        assert field in report


def test_quality_report_contains_effort_warning(project_root):
    path = (
        project_root
        / "data"
        / "silver_processed"
        / "relatorio_qualidade.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    codes = {
        issue["code"]
        for issue in report["issues"]
    }

    assert "EFFORT_FIELDS_PRESENT" in codes


def test_quality_report_detects_multiple_protocols(project_root):
    path = (
        project_root
        / "data"
        / "silver_processed"
        / "relatorio_qualidade.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    codes = {
        issue["code"]
        for issue in report["issues"]
    }

    assert "MULTIPLE_SAMPLING_PROTOCOLS" in codes