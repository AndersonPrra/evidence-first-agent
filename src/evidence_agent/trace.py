from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Dict


class ExecutionTracer:

    def __init__(
        self,
        log_dir: Path = Path("logs"),
        trace_filename: str = "execution_trace.jsonl",
    ):
        self.log_dir = log_dir

        self.log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.trace_file = (
            self.log_dir / trace_filename
        )

    def record_execution(
        self,
        user_query: str,
        response: Dict[str, Any],
    ) -> Dict[str, Any]:

        claim = response.get(
            "evidence_claim",
            {},
        )

        audit = response.get(
            "audit_result",
            {},
        )

        trace_entry = {
            "timestamp": datetime.now(
                UTC
            ).isoformat(),

            "user_query": user_query,

            "status": response.get(
                "status"
            ),

            "skill_executed": claim.get(
                "analysis_name"
            ),

            "claim_id": claim.get(
                "claim_id"
            ),

            "audit_status": audit.get(
                "audit_status"
            ),

            "report_file": response.get(
                "report_file"
            ),

            "response": response,
        }

        with self.trace_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    trace_entry,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return trace_entry