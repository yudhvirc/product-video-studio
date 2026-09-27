#!/usr/bin/env bash
# Record the user's decision at an approval gate (append-only log).
#
#   approve.sh <product_dir> <plan|stills|proof|delivery> <approved|changes|stopped> "<the user's own words>"
#   approve.sh <product_dir> check <stills|proof|final>     exit 0 if that stage may run, 3 if not (prints why)
#   approve.sh <product_dir> show                           print the approvals log
#
# ONLY record a decision the user actually gave in answer to the gate question.
# Each entry stores a fingerprint of spec.json + the engine, and the artifact
# version shown to the user. render.sh refuses to render stills without an
# approved plan, a proof without approved stills, and a final without an
# approved proof; stills and proof approvals only count while the fingerprint
# is unchanged (any later change to the spec or engine needs a fresh approval).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROD="$(cd "${1:?product dir}" && pwd)"; CMD="${2:?gate or check|show}"
LOG="$PROD/approvals.md"

fingerprint() {
  { cat "$PROD/spec.json"; find "$HERE/../engine" -name '*.py' -not -path '*/__pycache__/*' | sort | xargs cat; } \
    | sha256sum | cut -c1-12
}
latest() { ls -d "$1"/v* 2>/dev/null | sort -V | tail -1; }
# last decision recorded for a gate: prints "<decision> <fingerprint>"
last_decision() {
  grep -E "^\| [0-9]{4}-" "$LOG" 2>/dev/null | awk -F'|' -v g="$1" '{gsub(/ /,"",$3)} $3==g {d=$4; f=$6} END {gsub(/ /,"",d); gsub(/ /,"",f); if (d!="") print d, f}'
}

case "$CMD" in
  show) [ -f "$LOG" ] && cat "$LOG" || echo "no approvals recorded yet ($LOG)" ;;
  check)
    STAGE="${3:?stills|proof|final|high}"
    [ -f "$PROD/spec.json" ] || { echo "BLOCKED: no spec.json"; exit 3; }
    fp=$(fingerprint)
    need() {   # need <gate> <must_match_fingerprint:yes|no> <what to do>
      read -r d f <<<"$(last_decision "$1")" || true
      if [ "${d:-}" != approved ]; then
        echo "BLOCKED: the '$1' gate is not approved (last decision: ${d:-none}). $3"; exit 3; fi
      if [ "$2" = yes ] && [ "${f:-}" != "$fp" ]; then
        echo "BLOCKED: '$1' was approved for a different spec/engine (fingerprint ${f:-?}, now $fp). $3"; exit 3; fi
    }
    case "$STAGE" in
      stills)     need plan no "Show the user the plan and ask the plan gate question." ;;
      proof)      need stills yes "Render stills of the current spec, show them, and ask the stills gate question." ;;
      final|high) need proof yes "Render a proof of the current spec, show it, and ask the proof gate question." ;;
      *) echo "unknown stage $STAGE"; exit 2 ;;
    esac
    echo "OK: $STAGE may run (fingerprint $fp)" ;;
  plan|stills|proof|delivery)
    DEC="${3:?approved|changes|stopped}"; WORDS="${4:?quote the words the user answered with}"
    case "$DEC" in approved|changes|stopped) ;; *) echo "decision must be approved|changes|stopped"; exit 2 ;; esac
    case "$CMD" in
      plan)     ART="spec.json" ;;
      stills)   ART=$(latest "$PROD/previews"); ART="${ART#$PROD/}" ;;
      proof)    ART=$(latest "$PROD/proofs");   ART="${ART#$PROD/}" ;;
      delivery) ART=$(latest "$PROD/final");    ART="${ART#$PROD/}" ;;
    esac
    [ -n "$ART" ] || { echo "nothing to approve yet for '$CMD' (no output folder)"; exit 2; }
    if [ ! -f "$LOG" ]; then
      cat > "$LOG" <<EOF
# Approvals: $(basename "$PROD")

Append-only record of the user's decisions at each gate.

| time | gate | decision | artifacts | fingerprint | user's words |
|---|---|---|---|---|---|
EOF
    fi
    words=$(printf '%s' "$WORDS" | tr '\n|' '  ')
    printf '| %s | %s | %s | %s | %s | %s |\n' "$(date '+%F %T')" "$CMD" "$DEC" "$ART" "$(fingerprint)" "$words" >> "$LOG"
    echo "recorded: $CMD -> $DEC ($ART)" ;;
  *) echo "usage: approve.sh <product_dir> <plan|stills|proof|delivery> <approved|changes|stopped> \"words\" | check <stage> | show"; exit 2 ;;
esac
