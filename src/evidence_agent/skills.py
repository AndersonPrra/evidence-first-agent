from typing import Any, Callable, Dict, List, Optional

from evidence_agent.tools.evidence_engine import EvidenceEngine


class SkillDefinition(dict):
    @property
    def name(self) -> str:
        return self["name"]


class SkillRegistry:

    def __init__(
        self,
        engine: Optional[EvidenceEngine] = None,
    ):
        self.engine = engine or EvidenceEngine()
        self._skills: Dict[str, SkillDefinition] = {}

        self._register_default_skills()

    def _register_default_skills(self):
        self.register_skill(
            name="peak_richness",
            description=(
                "Identifica o mês com maior riqueza observada "
                "de espécies."
            ),
            keywords=[
                "riqueza",
                "richness",
                "espécies",
                "especies",
                "species",
                "mês",
                "mes",
                "mensal",
                "month",
                "monthly",
                "pico",
                "peak",
                "maior",
                "highest",
                "maximum",
                "max",
            ],
            required_keywords=[
                [
                    "riqueza",
                    "richness",
                    "species",
                    "espécies",
                    "especies",
                ],
                [
                    "mês",
                    "mes",
                    "mensal",
                    "month",
                    "monthly",
                    "pico",
                    "peak",
                    "maior",
                    "highest",
                    "maximum",
                    "max",
                ],
            ],
            func=self.engine.get_peak_richness_by_month,
        )

        self.register_skill(
            name="abundance_summary",
            description=(
                "Resume abundância quantitativa e registros "
                "de presença sem contagem."
            ),
            keywords=[
                "abundância",
                "abundancia",
                "abundance",
                "indivíduos",
                "individuos",
                "individuals",
                "quantidade",
                "quantity",
                "quantitativo",
                "quantitative",
                "qualitativo",
                "qualitative",
                "registros",
                "records",
                "presença",
                "presenca",
                "presence",
            ],
            required_keywords=[
                [
                    "abundância",
                    "abundancia",
                    "abundance",
                    "indivíduos",
                    "individuos",
                    "individuals",
                    "quantidade",
                    "quantity",
                    "registros",
                    "records",
                ]
            ],
            func=self.engine.get_abundance_summary,
        )

        self.register_skill(
            name="effort_discrepancy",
            description=(
                "Avalia a presença e a estrutura dos diferentes "
                "campos de esforço de amostragem."
            ),
            keywords=[
                "esforço",
                "esforco",
                "effort",
                "amostragem",
                "sampling",
                "sample",
                "protocolo",
                "protocol",
                "protocolos",
                "protocols",
                "tempo",
                "time",
                "duração",
                "duracao",
                "duration",
            ],
            required_keywords=[
                [
                    "esforço",
                    "esforco",
                    "effort",
                    "amostragem",
                    "sampling",
                ]
            ],
            func=self.engine.get_effort_discrepancy_report,
        )

    def register_skill(
        self,
        name: str,
        description: str,
        keywords: List[str],
        required_keywords: List[List[str]],
        func: Callable[[], Dict[str, Any]],
    ):
        self._skills[name] = SkillDefinition(
            name=name,
            description=description,
            keywords=keywords,
            required_keywords=required_keywords,
            executable=func,
        )

    def match(
        self,
        query: str,
    ) -> Optional[Any]:
        """
        Retorna a definição da skill correspondente à consulta.

        Esta é a interface pública de roteamento.
        """

        query_lower = query.lower()

        candidates = []

        for skill in self._skills.values():

            required_ok = True

            for group in skill["required_keywords"]:

                if not any(
                    keyword in query_lower
                    for keyword in group
                ):
                    required_ok = False
                    break

            if not required_ok:
                continue

            hits = sum(
                1
                for keyword in skill["keywords"]
                if keyword in query_lower
            )

            candidates.append(
                (
                    hits,
                    skill,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return candidates[0][1]

    def match_skill(
        self,
        query: str,
    ) -> Optional[Callable[[], Dict[str, Any]]]:
        """
        Retorna diretamente a função executável da skill.

        Mantém compatibilidade com o AnalysisOrchestrator.
        """

        skill = self.match(query)

        if skill is None:
            return None

        return skill["executable"]

    def list_skills(self) -> List[Dict[str, str]]:
        return [
            {
                "name": skill["name"],
                "description": skill["description"],
            }
            for skill in self._skills.values()
        ]