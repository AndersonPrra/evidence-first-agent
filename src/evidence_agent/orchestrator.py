from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from evidence_agent.llm_service import LLMService
from evidence_agent.report_generator import ReportGenerator
from evidence_agent.skills import SkillRegistry
from evidence_agent.tools.evidence_auditor import EvidenceAuditor
from evidence_agent.tools.evidence_engine import EvidenceEngine
from evidence_agent.trace import ExecutionTracer


class AnalysisOrchestrator:

    def __init__(
        self,
        base_dir: Path = Path("data"),
    ):
        self.base_dir = base_dir

        self.engine = EvidenceEngine(
            base_dir=base_dir,
        )

        self.auditor = EvidenceAuditor(
            base_dir=base_dir,
        )

        self.skills = SkillRegistry(
            engine=self.engine,
        )

        self.tracer = ExecutionTracer()

        self.reporter = ReportGenerator()

        self.llm = LLMService()

    def process_query(
        self,
        user_query: str,
    ) -> Dict[str, Any]:

        execution_id = str(uuid4())

        user_query = user_query.strip()

        # ---------------------------------------------------------
        # 0. Validação da entrada
        # ---------------------------------------------------------

        if not user_query:

            response = {
                "status": "ERROR",
                "message": "A pergunta não pode estar vazia.",
                "execution_id": execution_id,
                "user_query": user_query,
            }

            self.tracer.record_execution(
                user_query,
                response,
            )

            return response

        # ---------------------------------------------------------
        # 1. Entendimento / roteamento
        # ---------------------------------------------------------

        skill_func = self.skills.match_skill(
            user_query
        )

        if skill_func is None:

            response = {
                "status": "UNSUPPORTED",
                "message": (
                    "A pergunta não corresponde a nenhuma "
                    "análise atualmente suportada pelo contrato "
                    "e pelas ferramentas disponíveis."
                ),
                "execution_id": execution_id,
                "user_query": user_query,
            }

            self.tracer.record_execution(
                user_query,
                response,
            )

            return response

        # ---------------------------------------------------------
        # 2. Execução determinística
        # ---------------------------------------------------------

        try:

            claim = skill_func()

        except Exception as exc:

            response = {
                "status": "ANALYSIS_ERROR",
                "message": (
                    "A execução determinística da análise falhou."
                ),
                "reason": str(exc),
                "execution_id": execution_id,
                "user_query": user_query,
            }

            self.tracer.record_execution(
                user_query,
                response,
            )

            return response

        # ---------------------------------------------------------
        # 3. Auditoria independente
        # ---------------------------------------------------------

        audit = self.auditor.audit_claim(
            claim
        )

        audit_status = audit.get(
            "audit_status"
        )

        if audit_status != "VERIFIED":

            rejected_response = {
                "status": "REJECTED_BY_AUDITOR",
                "reason": audit.get(
                    "reason",
                    "A evidência não foi aprovada pela auditoria.",
                ),
                "execution_id": execution_id,
                "user_query": user_query,
                "evidence_claim": claim,
                "claim_id": claim.get("claim_id"),
                "audit_status": audit_status,
                "audit_result": audit,
            }

            self.tracer.record_execution(
                user_query,
                rejected_response,
            )

            return rejected_response

        # ---------------------------------------------------------
        # 4. Atualização do estado da evidência
        # ---------------------------------------------------------

        claim.setdefault(
            "audit_metadata",
            {},
        )

        claim[
            "audit_metadata"
        ][
            "audit_status"
        ] = audit_status

        claim[
            "audit_metadata"
        ][
            "evidence_state"
        ] = "VERIFIED"

        # ---------------------------------------------------------
        # 5. Síntese
        # ---------------------------------------------------------

        report = self.llm.synthesize_response(
            question=user_query,
            claim=claim,
            audit=audit,
        )

        # ---------------------------------------------------------
        # 6. Resultado final
        # ---------------------------------------------------------

        response = {
            "status": "SUCCESS",
            "execution_id": execution_id,
            "user_query": user_query,

            "skill": claim.get(
                "analysis_name"
            ),

            "claim_id": claim.get(
                "claim_id"
            ),

            "audit_status": audit_status,

            "evidence_state": claim.get(
                "audit_metadata",
                {},
            ).get(
                "evidence_state"
            ),

            "final_report": report,

            "evidence_claim": claim,

            "audit_result": audit,
        }

        # ---------------------------------------------------------
        # 7. Geração do artefato persistente
        # ---------------------------------------------------------

        report_path = (
            self.reporter.generate_markdown_report(
                response
            )
        )

        response[
            "report_file"
        ] = str(report_path)

        # ---------------------------------------------------------
        # 8. Rastreamento
        # ---------------------------------------------------------

        self.tracer.record_execution(
            user_query,
            response,
        )

        return response