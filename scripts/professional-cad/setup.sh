#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "$0")/../.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/professional-cad-uv}"
uv sync --locked --extra professional
scripts/professional-cad/install_skill.sh
UV_NO_SYNC=1 uv run python -m professional_cad schema >/dev/null
