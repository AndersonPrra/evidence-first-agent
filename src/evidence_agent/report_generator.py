from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Dict


class ReportGenerator:

    def __init__(
        self,
        output_dir: Path = Path("reports"),
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def generate_markdown_report(
        self,
        orchestrator_response: Dict[str, Any],
    ) -> Path:

        claim = orchestrator_response.get(
            "evidence_claim",
            {},
        )

        audit = orchestrator_response.get(
            "audit_result",
            {},
        )

        user_query = orchestrator_response.get(
            "user_query",
            "",
        )

        final_report = orchestrator_response.get(
            "final_report",
            "",
        )

        claim_id = claim.get(
            "claim_id",
            "N/A",
        )

        timestamp = datetime.now(
            UTC
        ).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        filename = (
            f"report_{claim_id}_"
            f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
        )

        file_path = (
            self.output_dir / filename
        )

        claim_result_json = json.dumps(
            claim.get("result", {}),
            indent=2,
            ensure_ascii=False,
        )

        recalculated_json = json.dumps(
            audit.get(
                "recalculated_values",
                {},
            ),
            indent=2,
            ensure_ascii=False,
        )

        audit_status = audit.get(
            "audit_status",
            "N/A",
        )

        analysis_name = claim.get(
            "analysis_name",
            "N/A",
        )

        data_source = claim.get(
            "data_source",
            "N/A",
        )

        evidence_state = (
            claim.get(
                "audit_metadata",
                {},
            ).get(
                "evidence_state",
                "N/A",
            )
        )

        md_content = f"""# Biodiversity Analysis Report

**Question:** "{user_query}"

**Issued:** {timestamp}

**Analysis:** `{analysis_name}`

**Evidence Claim:** `{claim_id}`

**Evidence State:** `{evidence_state}`

**Audit Status:** `{audit_status}`

---

## 1. Executive Conclusion

{final_report}

---

## 2. Evidence

**Data Source:** `{data_source}`

**Reproducible:** `{claim.get("audit_metadata", {}).get("is_reproducible", False)}`

### Calculated Result

```json
{claim_result_json}
```

### Independently Recalculated Result

```json
{recalculated_json}
```

**Discrepancy Detected:** `{audit.get("discrepancy_detected", False)}`

---

## 3. Audit

The result above was independently recalculated by the evidence auditor.

**Audit Status:** `{audit_status}`
"""

        file_path.write_text(
            md_content,
            encoding="utf-8",
        )

        return file_path