#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)

if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'ERROR: python3 is required inside WSL2 or Linux.' >&2
    exit 127
fi

exec python3 "$SCRIPT_DIR/agent_setup.py" "$@"
