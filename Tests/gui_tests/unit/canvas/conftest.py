import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(config, items):
    if sys.platform != "win32":
        return

    skip_reason = (
        "Skipping unit/canvas tests on Windows due to unstable Qt native state "
        "in full pytest sessions"
    )
    skip_marker = pytest.mark.skip(reason=skip_reason)
    for item in items:
        item_path = Path(str(item.fspath)).resolve()
        if BASE_DIR == item_path.parent or BASE_DIR in item_path.parents:
            item.add_marker(skip_marker)
