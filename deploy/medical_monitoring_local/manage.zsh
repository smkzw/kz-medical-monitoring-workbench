#!/bin/zsh
# 医学监查工作台本地管理入口（中文）。
# 将全部参数转交给同目录 manage.py，以保持退出码合同一致。
set -euo pipefail

HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
exec env -u PYTHONPATH python3 "$HERE/manage.py" "$@"
