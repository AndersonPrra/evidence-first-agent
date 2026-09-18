from pathlib import Path
import subprocess
import sys


class ProjectBootstrap:
    """
    prepara o projeto para execução

    O bootstrap oculta a ordem de execução interna do usuário:
    Bronze -> Silver -> Diagnosis -> Gold.
    """

    REQUIRED_RAW_FILES = [
        "event.txt",
        "occurrence.txt",
        "humboldtecologicalinventory.txt",
    ]

    REQUIRED_GOLD_FILES = [
        "richness_event.csv",
        "richness_month.csv",
        "abundance_event.csv",
        "composition_event.csv",
        "effort_event.csv",
    ]

    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"

        self.bronze_dir = self.data_dir / "bronze_raw"
        self.silver_dir = self.data_dir / "silver_processed"
        self.gold_dir = self.data_dir / "gold_analytical"

    def verify_input_data(self) -> None:
        """
        Verifica que os inputs declarados da camada Bronze existem.
        """

        missing = [
            filename
            for filename in self.REQUIRED_RAW_FILES
            if not (self.bronze_dir / filename).exists()
        ]

        if missing:
            formatted = "\n".join(f"  - {item}" for item in missing)

            raise FileNotFoundError(
                "Required Bronze input files are missing:\n"
                f"{formatted}\n\n"
                "Place the compatible Darwin Core files in "
                "data/bronze_raw/ and run the project again."
            )

    def run_module(self, module_name: str) -> None:
        """
        Executa um módulo existente do projeto usando o ambiente Python atual.
        """

        command = [
            sys.executable,
            "-m",
            module_name,
        ]

        print(f"\n▶ Running: {module_name}")

        subprocess.run(
            command,
            cwd=self.base_dir,
            check=True,
        )

    def prepare(self) -> None:
        """
        Executa por completo o pipeline de preparação determinístico.
        """

        self.verify_input_data()

        print("\n" + "=" * 60)
        print("PROJECT PREPARATION")
        print("=" * 60)

        self.run_module("evidence_agent.tools.ingestion")
        self.run_module("evidence_agent.tools.run_diagnosis")
        self.run_module("evidence_agent.tools.analytical_tables")

        self.verify_gold_outputs()

        print("\n✓ Preparação de dados concluída.")

    def verify_gold_outputs(self) -> None:
        """
        Garante que a camada analítica foi efetivamente produzida.
        """

        missing = [
            filename
            for filename in self.REQUIRED_GOLD_FILES
            if not (self.gold_dir / filename).exists()
        ]

        if missing:
            formatted = "\n".join(f"  - {item}" for item in missing)

            raise RuntimeError(
                "Gold analytical layer was not generated correctly.\n"
                f"Missing files:\n{formatted}"
            )

    def is_prepared(self) -> bool:
        """
        Retorna True quando a camada Gold existe.
        """

        return all(
            (self.gold_dir / filename).exists()
            for filename in self.REQUIRED_GOLD_FILES
        )