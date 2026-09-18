from __future__ import annotations

import json
from pathlib import Path

from evidence_agent.tools.data_profile import (
    DataProfiler,
)
from evidence_agent.tools.ingestion import (
    DwCAIngestionTool,
)


def main():

    # ---------------------------------------------------------
    # Caminhos
    # ---------------------------------------------------------

    raw_dir = Path(
        "data/bronze_raw"
    )

    processed_dir = Path(
        "data/silver_processed"
    )

    execution_dir = Path(
        "execucoes"
    )

    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    execution_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Ingestão
    # ---------------------------------------------------------

    ingestion = DwCAIngestionTool(
        raw_dir=str(raw_dir),
        processed_dir=str(processed_dir),
        execution_dir=str(execution_dir),
    )

    (
        events,
        occurrences,
        inventories,
    ) = ingestion.load_raw_tables()

    # ---------------------------------------------------------
    # Perfil determinístico
    # ---------------------------------------------------------

    print(
        "\n📊 Gerando perfil determinístico..."
    )

    profiler = DataProfiler()

    profile = profiler.profile_dataset(
        events=events,
        occurrences=occurrences,
        inventories=inventories,
    )

    profile_path = (
        processed_dir
        / "perfil_dados.json"
    )

    profile_path.write_text(
        json.dumps(
            profile,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        f"✅ Perfil salvo em: {profile_path}"
    )

    # ---------------------------------------------------------
    # Validação de qualidade
    # ---------------------------------------------------------

    print(
        "\n🔍 Executando validação de qualidade..."
    )

    quality_report = ingestion.validate_dataset(
        events,
        occurrences,
        inventories,
    )

    quality_path = (
        processed_dir
        / "relatorio_qualidade.json"
    )

    quality_path.write_text(
        quality_report.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    print(
        f"✅ Relatório salvo em: {quality_path}"
    )

    # ---------------------------------------------------------
    # Resumo
    # ---------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("RESUMO DO DIAGNÓSTICO")
    print("=" * 60)

    print(
        f"Eventos:       {len(events):,}"
    )

    print(
        f"Ocorrências:   {len(occurrences):,}"
    )

    print(
        f"Inventários:   {len(inventories):,}"
    )

    print(
        f"Problemas:     {len(quality_report.issues):,}"
    )

    print(
        "Status:        "
        + (
            "VÁLIDO"
            if quality_report.is_valid_for_analysis
            else "INVÁLIDO"
        )
    )

    print("=" * 60)


if __name__ == "__main__":
    main()