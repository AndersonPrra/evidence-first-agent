import sys

from evidence_agent.orchestrator import AnalysisOrchestrator


def main():

    print("=" * 70)
    print(
        "   🌿 EVIDENCE-FIRST BIODIVERSITY AGENT 🌿"
    )
    print("=" * 70)

    print(
        "Faça uma pergunta sobre os dados de biodiversidade."
    )

    print("\nExemplos:")

    print(
        "  - Qual foi o mês com maior riqueza de espécies?"
    )

    print(
        "  - Resumo de abundância e registros"
    )

    print(
        "  - Relatório de esforço de amostragem"
    )

    print(
        "\nDigite 'sair' para encerrar.\n"
    )

    orchestrator = AnalysisOrchestrator()

    while True:

        try:

            user_input = input(
                "🗣️ Usuário > "
            ).strip()

            if not user_input:
                continue

            if user_input.lower() in {
                "sair",
                "exit",
                "quit",
            }:

                print(
                    "\nEncerrando sessão. Até logo! 👋"
                )

                sys.exit(0)

            print(
                "\n⚙️ Executando análise determinística..."
            )

            response = (
                orchestrator.process_query(
                    user_input
                )
            )

            status = response.get(
                "status"
            )

            if status == "SUCCESS":

                print(
                    "\n✅ Resposta auditada:\n"
                )

                print(
                    response.get(
                        "final_report",
                        "",
                    )
                )

                print(
                    "\n📄 Relatório:"
                )

                print(
                    response.get(
                        "report_file",
                        "N/A",
                    )
                )

                print(
                    "\n🔍 Claim ID:"
                )

                print(
                    response
                    .get(
                        "evidence_claim",
                        {},
                    )
                    .get(
                        "claim_id",
                        "N/A",
                    )
                )

            elif status == "UNSUPPORTED":

                print(
                    "\n⚠️ Consulta fora do escopo:"
                )

                print(
                    response.get(
                        "message",
                        "",
                    )
                )

            else:

                print(
                    f"\n⚠️ Status: {status}"
                )

                print(
                    response.get(
                        "message",
                        response.get(
                            "reason",
                            "",
                        ),
                    )
                )

            print(
                "\n" + "-" * 70 + "\n"
            )

        except KeyboardInterrupt:

            print(
                "\n\nSessão interrompida. Até logo! 👋"
            )

            sys.exit(0)


if __name__ == "__main__":
    main()