#!/usr/bin/env bash
# Render a product from its spec.
#
#   render.sh <product_dir> <stills|proof|final|high> [ad|turntable|both]
#
#   stills : 4 ad frames + 1 turntable frame at full res   -> <product>/previews/vN/
#   proof  : every frame at 50% res, 8 samples (~2 s/frame) -> <product>/proofs/vN/*.mp4
#   final  : every frame at 1080p-class, 20 samples (~12 s/frame) -> <product>/final/vN/*.mp4
#   high   : 64 samples (~30 s/frame)                        -> <product>/final/vN/*.mp4
#
# Nothing in the product folder is ever deleted or overwritten: every run writes
# a new version folder (v1, v2, ...). Frames and .blend files live in a work cache
# OUTSIDE the product folder: ${PVS_WORK_ROOT:-%LOCALAPPDATA%/pvs_work}/<slug>/.
# Resumable: finished frames are reused; the scene is rebuilt (with a fresh
# frames folder) only when spec.json or the engine changed.
# Never edit this file while it runs (bash reads scripts incrementally).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENGINE_DIR="$HERE/../engine"
PROD="$(cd "${1:?product dir}" && pwd)"
Q="${2:?stills|proof|final|high}"
KINDS="${3:-both}"; [ "$KINDS" = both ] && KINDS="ad turntable"
SPEC="$PROD/spec.json"; [ -f "$SPEC" ] || { echo "no spec.json in $PROD"; exit 1; }
eval "$("$HERE/check_env.sh" | grep -E '^PVS_')"
B="$PVS_BLENDER"
SLUG="$(basename "$PROD")"
CACHE_ROOT="${PVS_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/pvs_work}"
WORK="$CACHE_ROOT/$SLUG"
BQ=$([ "$Q" = stills ] && echo final || echo "$Q")
jget() { node -e "const s=require(process.argv[1]);const v=process.argv[2].split('.').reduce((o,k)=>o&&o[k],s);console.log(v===undefined?process.argv[3]:v)" "$1" "$2" "$3"; }
next_version() {   # next free <dir>/vN
  local d="$1" n=1
  while [ -e "$d/v$n" ]; do n=$((n+1)); done
  echo "$d/v$n"
}
GRAIN=$(jget "$SPEC" look.grain true); VIG=$(jget "$SPEC" look.vignette false)
BACKDROP=$(jget "$SPEC" look.backdrop studio_white)
FADE_COL=$([ "$BACKDROP" = studio_white ] && echo white || echo black)
LOOK="null"
[ "$GRAIN" = true ] && LOOK="noise=c0s=5:c0f=t"
[ "$VIG" = true ] && LOOK="$LOOK,vignette=angle=0.32"
mkdir -p "$WORK/$BQ"
OUTD=""
case "$Q" in
  stills) OUTD=$(next_version "$PROD/previews") ;;
  proof)  OUTD=$(next_version "$PROD/proofs") ;;
  *)      OUTD=$(next_version "$PROD/final") ;;
esac
echo "== output folder: $OUTD"

for K in $KINDS; do
  BL="$WORK/$BQ/$K.blend"
  if [ ! -f "$BL" ] || [ "$SPEC" -nt "$BL" ] || [ -n "$(find "$ENGINE_DIR" -name '*.py' -newer "$BL" 2>/dev/null)" ]; then
    echo "== building $K ($BQ)"
    "$B" -b --python "$ENGINE_DIR/build.py" -- "$SPEC" "$K" "$BL" "$BQ" > "$WORK/build_${BQ}_$K.log" 2>&1 \
      || { tail -20 "$WORK/build_${BQ}_$K.log"; exit 1; }
    date +%Y%m%d%H%M%S > "$BL.build_id"
    grep -E "^PVS built|^charm|^strung" "$WORK/build_${BQ}_$K.log" || true
  fi
  FR=$(jget "$BL.json" frames 0); FPS=$(jget "$BL.json" fps 30); SECS=$(jget "$BL.json" seconds 0)

  if [ "$Q" = stills ]; then
    mkdir -p "$OUTD"
    if [ "$K" = ad ]; then FRAMES="0 $((FR*110/450)) $((FR*215/450)) $((FR-1))"; else FRAMES="$((FR/3))"; fi
    ARGS=""; for f in $FRAMES; do ARGS="$ARGS -f $f"; done
    "$B" -b "$BL" -o "$OUTD/${K}_####" $ARGS > "$WORK/stills_$K.log" 2>&1
    grep -E "Saved:" "$WORK/stills_$K.log" | sed 's/.*Saved: /saved /' || true
    continue
  fi

  DIR="$WORK/$BQ/${K}_frames_$(cat "$BL.build_id")"      # cache, outside the product folder
  mkdir -p "$DIR"
  find "${DIR:?}" -name 'f_*.png' -size -2k -delete 2>/dev/null || true   # placeholders from an interrupted run
  DONE=$(ls "$DIR" 2>/dev/null | wc -l)
  echo "== rendering $K ($Q): $DONE/$FR frames already done  [$DIR]"
  if [ "$DONE" -lt "$FR" ]; then
    "$B" -b "$BL" --python-expr "import bpy; s=bpy.context.scene; s.render.use_overwrite=False; s.render.use_placeholder=True" \
        -o "$DIR/f_####" -a > "$WORK/render_${Q}_$K.log" 2>&1
  fi
  N=$(find "$DIR" -name 'f_*.png' -size +2k | wc -l)
  [ "$N" -eq "$FR" ] || { echo "only $N/$FR frames complete - re-run to resume"; exit 1; }

  mkdir -p "$OUTD"
  RES=$([ "$Q" = proof ] && echo 540p || echo 1080p)
  OUT="$OUTD/${SLUG}_${K}_${SECS}s_${RES}$([ "$Q" = proof ] && echo _PROOF).mp4"
  VF="$LOOK"
  if [ "$K" = ad ]; then
    END=$(node -e "console.log(($FR/$FPS-0.7).toFixed(2))")
    VF="$VF,fade=t=in:st=0:d=0.5:color=$FADE_COL,fade=t=out:st=$END:d=0.7:color=$FADE_COL"
  fi
  CRF=$([ "$Q" = proof ] && echo 20 || echo 17)
  ffmpeg -loglevel error -n -framerate "$FPS" -i "$DIR/f_%04d.png" -vf "$VF" -c:v libx264 -preset slow -crf "$CRF" \
    -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags +faststart "$OUT"
  ffprobe -v error -show_entries format=duration:stream=width,height,nb_frames -of compact "$OUT" | tr '\n' ' '
  echo "-> $OUT"
done
