import json
from typing import Any, Dict

try:
    import ollama
except ImportError:
    ollama = None
    print(
        "O Ollama não está instalado no seu computador isso não invalida a execução, "
        "mas o ideal é que ele seja instalado! Para isso você pode baixar ou rodar o comando "
        'no seu terminal "winget install Ollama.Ollama" depois "python -m pip install ollama" '
        'e por fim o modelo usado no projeto "ollama pull llama3.2".'
    )

class LLMService:

    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def synthesize_response(
        self,
        question: str,
        claim: Dict[str, Any],
        audit: Dict[str, Any],
    ) -> str:

        if audit.get("audit_status") != "VERIFIED":
            return (
                "O resultado analítico não foi verificado de forma independente. "
                "Nenhuma conclusão substantiva foi fornecida."
            )

        if ollama is None:
            return self._deterministic_fallback(
                question,
                claim,
                audit,
            )

        try:
            prompt = self._build_prompt(
                question,
                claim,
                audit,
            )

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            return response["message"]["content"]

        except Exception:
            return self._deterministic_fallback(
                question,
                claim,
                audit,
            )

    def _build_prompt(
        self,
        question: str,
        claim: Dict[str, Any],
        audit: Dict[str, Any],
    ) -> str:

        return f"""
Você é a camada de relatórios de um sistema analítico focado em evidências.

Sua tarefa é comunicar evidências analíticas verificadas.

REGRAS ESTREITAS:

1. Use apenas as evidências fornecidas.
2. Não invente valores.
3. Não introduza fatos externos.
4. Não converta valores ausentes em zero.
5. Não transforme associação em causalidade.
6. Distinga claramente observação de inferência.
7. Mencione limitações importantes.
8. Se as evidências forem insuficientes, diga isso explicitamente.
9. Preserve o ID da Alegação (Claim ID).

PERGUNTA:
{question}

ALEGAÇÃO (CLAIM):
{claim}

AUDITORIA INDEPENDENTE:
{audit}

Escreva uma interpretação técnica e concisa em português.
"""

    def _deterministic_fallback(
        self,
        question: str,
        claim: Dict[str, Any],
        audit: Dict[str, Any],
    ) -> str:

        result = claim.get("result", {})
        claim_id = claim.get("claim_id", "desconhecido")

        analysis_name = claim.get("analysis_name")

        if analysis_name == "peak_richness_by_month":

            peak_months = result.get("peak_months", [])

            if len(peak_months) == 1:
                conclusion = (
                    f"A maior riqueza de espécies observada ocorreu "
                    f"em {peak_months[0]}."
                )
            else:
                conclusion = (
                    "A maior riqueza de espécies observada empatou "
                    f"entre os meses: {', '.join(peak_months)}."
                )

        elif analysis_name == "abundance_summary":

            conclusion = (
                "O conjunto de dados contém registros de abundância quantificada e de "
                "presença sem contagem individual de espécimes. "
                "Eles não devem ser interpretados como medidas equivalentes."
            )

        elif analysis_name == "effort_discrepancy_report":

            conclusion = (
                "As informações sobre o esforço de amostragem são representadas através "
                "de diferentes campos e unidades. Essas medições não devem ser "
                "tratadas como intercambiáveis sem o suporte dos metadados."
            )

        else:
            conclusion = (
                "A análise foi concluída e verificada de forma independente."
            )

        return (
            f"{conclusion}\n\n"
            f"Estado da evidência: VERIFICADO.\n"
            f"ID da Alegação: {claim_id}.\n"
            "A interpretação está limitada ao conjunto de dados fornecido e ao "
            "procedimento analítico utilizado."
        )