#!/usr/bin/env bash
# Batch processing over a products root (one folder per product, each with spec.json).
#
#   batch.sh <products_root> status
#   batch.sh <products_root> <stills|proof|final|high> [product ...]   (default: every product with spec.json)
#   batch.sh <products_root> contact                                   latest hero still of every product, one sheet
#
# Products render one after another (the CPU is the bottleneck; parallel runs
# only slow each other down). Each product is resumable, so re-running the same
# command after an interruption continues where it stopped (frames are cached
# outside the product folders). Every run writes new version folders; nothing is
# deleted or overwritten. A product whose folder contains SKIP is ignored.
# Log: <products_root>/_batch.log (append-only)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${1:?products root}" && pwd)"; CMD="${2:?status|stills|proof|final|high|contact}"; shift 2
LOG="$ROOT/_batch.log"
CACHE_ROOT="${PVS_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/pvs_work}"
latest() { ls -d "$1"/v* 2>/dev/null | sort -V | tail -1; }
list() { if [ $# -gt 0 ]; then for p in "$@"; do echo "$ROOT/$p"; done;
         else for d in "$ROOT"/*/; do [ -f "$d/spec.json" ] && [ ! -f "$d/SKIP" ] && echo "${d%/}"; done; fi; }
case "$CMD" in
  status)
    printf "%-34s %-5s %-9s %-9s %-24s %-7s %s\n" PRODUCT SPEC PREVIEWS PROOFS "FINAL FRAMES (cache)" FINALS "MAY RUN (approvals)"
    for d in "$ROOT"/*/; do d="${d%/}"; n=$(basename "$d"); [ "${n:0:1}" = _ ] && continue
      sp=$([ -f "$d/spec.json" ] && echo yes || echo -); [ -f "$d/SKIP" ] && sp=SKIP
      pv=$(basename "$(latest "$d/previews")" 2>/dev/null); pr=$(basename "$(latest "$d/proofs")" 2>/dev/null)
      fv=$(basename "$(latest "$d/final")" 2>/dev/null)
      fa=$(ls -d "$CACHE_ROOT/$n"/final/ad_frames_* 2>/dev/null | sort | tail -1)
      ft=$(ls -d "$CACHE_ROOT/$n"/final/turntable_frames_* 2>/dev/null | sort | tail -1)
      ca=$([ -n "$fa" ] && find "$fa" -name 'f_*.png' -size +2k | wc -l || echo 0)
      ct=$([ -n "$ft" ] && find "$ft" -name 'f_*.png' -size +2k | wc -l || echo 0)
      ok=""; for st in stills proof final; do "$HERE/approve.sh" "$d" check $st >/dev/null 2>&1 && ok="$st"; done
      printf "%-34s %-5s %-9s %-9s %-24s %-7s %s\n" "$n" "$sp" "${pv:--}" "${pr:--}" "ad $ca / tt $ct" "${fv:--}" "${ok:-nothing (plan not approved)}"
    done ;;
  contact)
    files=(); for d in $(list "$@"); do V=$(latest "$d/previews"); f=$(ls "$V"/ad_*.png 2>/dev/null | tail -1); [ -n "$f" ] && files+=("$f"); done
    n=${#files[@]}; [ "$n" -gt 0 ] || { echo "no stills yet: batch.sh $ROOT stills"; exit 1; }
    k=1; while [ -e "$ROOT/_contact_sheet_v$k.png" ]; do k=$((k+1)); done
    out="$ROOT/_contact_sheet_v$k.png"
    args=(); for f in "${files[@]}"; do args+=(-i "$f"); done
    lay=$(node -e "const n=$n,c=Math.min(4,n),o=[];for(let i=0;i<n;i++){const x=i%c,y=Math.floor(i/c);o.push((x?Array(x).fill('w0').join('+'):'0')+'_'+(y?Array(y).fill('h0').join('+'):'0'))}console.log(o.join('|'))")
    fc=""; for i in $(seq 0 $((n-1))); do fc="$fc[$i]scale=480:270[v$i];"; done; for i in $(seq 0 $((n-1))); do fc="$fc[v$i]"; done
    ffmpeg -loglevel error -n "${args[@]}" -filter_complex "${fc}xstack=inputs=$n:layout=$lay:fill=white" "$out" \
      && echo "-> $out ($n products, in folder order)" ;;
  stills|proof|final|high)
    fails=0; blocked=0
    for d in $(list "$@"); do
      if ! gate=$("$HERE/approve.sh" "$d" check "$CMD" 2>&1); then
        blocked=$((blocked+1)); echo "[$(date '+%F %T')] AWAITING APPROVAL $CMD $(basename "$d"): $gate" | tee -a "$LOG"
        continue
      fi
      echo "[$(date '+%F %T')] START $CMD $(basename "$d")" | tee -a "$LOG"
      if "$HERE/render.sh" "$d" "$CMD" 2>&1 | tee -a "$LOG"; then
        echo "[$(date '+%F %T')] DONE  $CMD $(basename "$d")" | tee -a "$LOG"
      else
        fails=$((fails+1)); echo "[$(date '+%F %T')] FAIL  $CMD $(basename "$d") (logs: $CACHE_ROOT/$(basename "$d"))" | tee -a "$LOG"
      fi
    done
    echo "batch $CMD finished, failures: $fails, awaiting approval: $blocked" | tee -a "$LOG"
    [ $fails -eq 0 ] && [ $blocked -eq 0 ] ;;
  *) echo "unknown command $CMD"; exit 2 ;;
esac
