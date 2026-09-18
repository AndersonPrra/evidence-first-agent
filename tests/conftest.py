from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    return project_root / "data"


@pytest.fixture
def silver_dir(data_dir: Path) -> Path:
    return data_dir / "silver_processed"


@pytest.fixture
def gold_dir(data_dir: Path) -> Path:
    return data_dir / "gold_analytical"