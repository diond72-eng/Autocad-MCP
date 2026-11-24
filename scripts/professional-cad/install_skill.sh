#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname -- "$0")/../.." && pwd)
destination=${1:-"$repo/.agents/skills"}
mkdir -p "$destination"
target="$destination/professional-cad"
if [[ -L "$target" && $(readlink -f "$target") == "$repo/skills/professional-cad" ]]; then exit 0; fi
if [[ -e "$target" || -L "$target" ]]; then printf 'Skill destination already exists: %s\n' "$target" >&2; exit 1; fi
ln -s "$repo/skills/professional-cad" "$target"
