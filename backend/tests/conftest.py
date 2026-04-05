from __future__ import annotations

import os

import pytest


def integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if integration_enabled():
        return

    skip_integration = pytest.mark.skip(reason="integration tests disabled; set RUN_INTEGRATION_TESTS=1")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)