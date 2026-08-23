import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest  # noqa: E402

from parser import Config, load_config  # noqa: E402


@pytest.fixture(scope="session")
def config() -> Config:
    return load_config(PROJECT_ROOT / "templates" / "эхо" / "fields.toml")
