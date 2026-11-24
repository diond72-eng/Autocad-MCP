#!/usr/bin/env bash
# Convert editable DXFs with an existing ODA File Converter installation.
set -euo pipefail

if [[ $# != 2 ]]; then
  printf 'Usage: %s INPUT_DIRECTORY OUTPUT_DIRECTORY\n' "$0" >&2
  exit 2
fi
input=$(realpath "$1")
mkdir -p "$2"
output=$(realpath "$2")
source_dir=$(cd -- "$(dirname -- "$0")" && pwd)
conv_root="$source_dir/../../oda"
converter=${ODA_FILE_CONVERTER:-$(command -v ODAFileConverter || true)}
xvfb=${ODA_XVFB:-"$conv_root/xserver/usr/bin/Xvfb"}
if [[ ! -x "$converter" ]]; then
  printf 'Set ODA_FILE_CONVERTER to your installed ODA File Converter executable.\n' >&2
  exit 2
fi
temp=$(mktemp -d)
display_pid=''
cleanup() {
  if [[ -n "$display_pid" ]]; then kill "$display_pid" 2>/dev/null || true; fi
  rm -rf -- "$temp"
}
trap cleanup EXIT
if [[ -z ${DISPLAY:-} ]]; then
  if [[ ! -x "$xvfb" ]]; then xvfb=$(command -v Xvfb || true); fi
  if [[ -z "$xvfb" ]]; then printf 'Set DISPLAY or install Xvfb.\n' >&2; exit 2; fi
  "$xvfb" -displayfd 3 -screen 0 1024x768x24 -nolisten tcp 3>"$temp/display" >"$temp/xvfb.log" 2>&1 &
  display_pid=$!
  for _ in {1..60}; do [[ ! -s "$temp/display" ]] || break; sleep .1; done
  if [[ ! -s "$temp/display" ]]; then cat "$temp/xvfb.log" >&2; exit 1; fi
  export DISPLAY=":$(cat "$temp/display")"
fi
export QT_QPA_PLATFORM=xcb
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"$temp/cache"}
mkdir -p "$temp/dwg" "$temp/roundtrip"
timeout 135 "$converter" "$input" "$temp/dwg" ACAD2013 DWG 0 1 '*.dxf'
timeout 135 "$converter" "$temp/dwg" "$temp/roundtrip" ACAD2013 DXF 0 1 '*.dwg'
mkdir -p "$output/Roundtrip"
shopt -s nullglob
drawings=("$temp/dwg"/*.dwg)
if [[ ${#drawings[@]} == 0 ]]; then printf 'No DWGs created.\n' >&2; exit 1; fi
for dwg in "${drawings[@]}"; do
  base=$(basename "$dwg" .dwg)
  if [[ $(head -c6 "$dwg") != AC1027 || ! -s "$temp/roundtrip/$base.dxf" ]]; then
    printf 'Invalid or incomplete conversion: %s\n' "$dwg" >&2
    exit 1
  fi
  cp -- "$dwg" "$output/$base.dwg"
  cp -- "$temp/roundtrip/$base.dxf" "$output/Roundtrip/$base.dxf"
  printf 'AC1027 converted and reopened: %s\n' "$base.dwg"
done
