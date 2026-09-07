#!/usr/bin/env python3
"""Thin compatibility entrypoint for the modular macOS/Linux setup tool."""

from __future__ import annotations

import sys
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

# Re-export the established Python API for callers and existing tests.
from agent_setup_lib.auth_env import *  # noqa: E402,F401,F403
from agent_setup_lib.common import *  # noqa: E402,F401,F403
from agent_setup_lib.doctor import *  # noqa: E402,F401,F403
from agent_setup_lib.global_setup import *  # noqa: E402,F401,F403
from agent_setup_lib.project import *  # noqa: E402,F401,F403
from agent_setup_lib.public_tools import *  # noqa: E402,F401,F403
from agent_setup_lib.repositories import *  # noqa: E402,F401,F403
from agent_setup_lib.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
