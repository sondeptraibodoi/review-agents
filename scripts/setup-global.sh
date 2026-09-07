#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)

if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'ERROR: python3 is required on macOS or Linux.' >&2
    exit 127
fi

if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    printf '%s\n' 'ERROR: Python 3.10 or newer is required.' >&2
    exit 3
fi

exec python3 "$SCRIPT_DIR/agent_setup.py" "$@"
