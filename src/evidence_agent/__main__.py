import argparse
from pathlib import Path

from evidence_agent.bootstrap import ProjectBootstrap
from evidence_agent.orchestrator import AnalysisOrchestrator


DEFAULT_QUESTION = (
    "Qual mês apresentou a maior riqueza de espécies de aves observada?"
)


DEMO_QUESTIONS = [
    "Qual mês apresentou a maior riqueza de espécies de aves observada?",
    "Qual mês apresentou a maior abundância de espécies de aves observada?",
    "Há diferenças no esforço de amostragem que devem afetar a interpretação?",
    "Quais são os principais padrões de biodiversidade suportados pelos dados?",
]


def print_banner():
    print(
        """
============================================================
                 EVIDENCE-FIRST AGENT
============================================================

Evidence-first analytical system for bird community
monitoring data.

Pipeline:
  Input → Validation → Analysis → Audit → Report → Trace

============================================================
"""
    )


def run_question(question: str, orchestrator: AnalysisOrchestrator):
    print("\n" + "-" * 60)
    print(f"PERGUNTA:\n{question}")
    print("-" * 60)

    response = orchestrator.process_query(question)

    print("\nRESULT")
    print("=" * 60)

    status = response.get("status", "UNKNOWN")
    print(f"Status: {status}")

    if response.get("message"):
        print(f"\n{response['message']}")

    if response.get("report_file"):
        print(f"\nReport: {response['report_file']}")

    if response.get("claim_id"):
        print(f"Claim ID: {response['claim_id']}")

    return response


def main():
    parser = argparse.ArgumentParser(
        description="Evidence-first data analysis system."
    )

    parser.add_argument(
        "--question",
        type=str,
        help="Question to analyse.",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the demonstration questions.",
    )

    parser.add_argument(
        "--skip-preparation",
        action="store_true",
        help="Skip Bronze/Silver/Gold preparation.",
    )

    args = parser.parse_args()

    print_banner()

    bootstrap = ProjectBootstrap(Path("."))

    try:
        if not args.skip_preparation:
            bootstrap.prepare()
        else:
            print("⚠ Preparação ignorada pelo usuário.")

    except Exception as exc:
        print("\n✗ A preparação falhou.")
        print(f"Motivo: {exc}")
        raise SystemExit(1)

    orchestrator = AnalysisOrchestrator()

    if args.demo:
        for question in DEMO_QUESTIONS:
            run_question(question, orchestrator)

        print("\n" + "=" * 60)
        print("DEMO COMPLETA")
        print("=" * 60)
        return

    if args.question:
        run_question(args.question, orchestrator)
        return

    print("\nInteractive mode")
    print("Digite sua pergunta ou 'exit' para finalizar.\n")

    while True:
        try:
            question = input("Question > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if question.lower() in {"exit", "quit", "q"}:
            break

        if not question:
            continue

        run_question(question, orchestrator)


if __name__ == "__main__":
    main()