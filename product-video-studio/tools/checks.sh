#!/usr/bin/env bash
# Review aids for a product. They work on the LATEST version folder and only ever
# add new files (never overwrite or delete anything in the product folder).
#
#   checks.sh <product_dir> charms     face-on render of each photo charm next to its reference photo
#   checks.sh <product_dir> sheet      stills of the latest previews/vN tiled into previews/vN/_sheet.png
#   checks.sh <product_dir> proofsheet 1 frame/sec of each video in the latest proofs/vN
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROD="$(cd "${1:?product dir}" && pwd)"; WHAT="${2:?charms|sheet|proofsheet}"
eval "$("$HERE/check_env.sh" | grep -E '^PVS_')"
SLUG="$(basename "$PROD")"
WORK="${PVS_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/pvs_work}/$SLUG"
latest() { ls -d "$1"/v* 2>/dev/null | sort -V | tail -1; }
fresh() {  # a filename that does not exist yet: name.png, name_2.png, ...
  local base="${1%.*}" ext="${1##*.}" n=2 f="$1"
  while [ -e "$f" ]; do f="${base}_$n.$ext"; n=$((n+1)); done
  echo "$f"
}
grid() {   # grid <out> <cols> <width> files...
  local out="$1" cols="$2" wd="$3"; shift 3
  local n=$# args=() i
  for f in "$@"; do args+=(-i "$f"); done
  local lay; lay=$(node -e "const n=$n,c=Math.min($cols,n),o=[];for(let i=0;i<n;i++){const x=i%c,y=Math.floor(i/c);o.push((x?Array(x).fill('w0').join('+'):'0')+'_'+(y?Array(y).fill('h0').join('+'):'0'))}console.log(o.join('|'))")
  local fc=""; for i in $(seq 0 $((n-1))); do fc="$fc[$i]scale=$wd:-2[v$i];"; done
  for i in $(seq 0 $((n-1))); do fc="$fc[v$i]"; done
  ffmpeg -loglevel error -n "${args[@]}" -filter_complex "${fc}xstack=inputs=$n:layout=$lay:fill=white" "$out"
}
case "$WHAT" in
  charms)
    BL="$WORK/final/ad.blend"; V=$(latest "$PROD/previews")
    [ -f "$BL" ] && [ -n "$V" ] || { echo "run render.sh $PROD stills first"; exit 1; }
    T=$(mktemp -d)
    "$PVS_BLENDER" -b "$BL" --python "$HERE/charm_check.py" -- "$T" 2>&1 | grep CHARM_CHECK || true
    for png in "$T"/charm_*.png; do
      [ -e "$png" ] || continue
      name=$(basename "$png" .png | sed -E 's/^charm_//; s/_[0-9]+$//')
      ref=$(node -e "const s=require(process.argv[1]);const p=s.product.parts[process.argv[2]];console.log(p?p.photo:'')" "$PROD/spec.json" "$name")
      [ -n "$ref" ] || continue
      out=$(fresh "$V/compare_${name}_vs_photo.png")
      ffmpeg -loglevel error -n -i "$png" -i "$PROD/$ref" -filter_complex "[0]scale=-1:500[a];[1]scale=-1:500[b];[a][b]hstack" "$out" \
        && echo "-> $out"
    done ;;
  sheet)
    V=$(latest "$PROD/previews"); [ -n "$V" ] || { echo "no stills yet"; exit 1; }
    files=("$V"/ad_*.png "$V"/turntable_*.png)
    out=$(fresh "$V/_sheet.png"); grid "$out" 3 640 "${files[@]}" && echo "-> $out" ;;
  proofsheet)
    V=$(latest "$PROD/proofs"); [ -n "$V" ] || { echo "no proofs yet"; exit 1; }
    for v in "$V"/*.mp4; do
      out=$(fresh "$V/_$(basename "$v" .mp4)_sheet.png")
      ffmpeg -loglevel error -n -i "$v" -vf "fps=1,scale=384:-1,tile=5x3" -frames:v 1 "$out" && echo "-> $out"
    done ;;
esac
