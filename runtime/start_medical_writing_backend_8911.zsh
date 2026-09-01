#!/bin/zsh

set -eu

WORKBENCH_ROOT="${0:A:h:h}"
WORKBENCH_API_PORT="${WORKBENCH_API_PORT:-8911}"
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "$WORKBENCH_ROOT"
exec env -u PYTHONPATH \
  WORKBENCH_AI_DEPLOYMENT_PROFILE=local_private_clinical \
  /usr/bin/python3 -m uvicorn services.api.app.main:app \
    --host 127.0.0.1 \
    --port "$WORKBENCH_API_PORT"
