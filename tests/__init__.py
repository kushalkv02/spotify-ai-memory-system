"""
Package initialization for tests.
Sets up sys.path and module aliases for unittest and pytest runners.
"""
from __future__ import annotations

import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

INTERACTION_API_DIR = os.path.join(PROJECT_ROOT, "interaction-api")
if INTERACTION_API_DIR not in sys.path:
    sys.path.insert(0, INTERACTION_API_DIR)

if os.path.exists(INTERACTION_API_DIR) and "interaction_api" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "interaction_api",
        os.path.join(INTERACTION_API_DIR, "__init__.py"),
        submodule_search_locations=[INTERACTION_API_DIR],
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules["interaction_api"] = mod
        spec.loader.exec_module(mod)
