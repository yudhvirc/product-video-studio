#!/usr/bin/env bash
# Finds Blender and ffmpeg. Prints `PVS_BLENDER=<path>` / `PVS_FFMPEG=<path>` lines
# (eval-able) and exits 1 with install hints if something is missing.
# Honors a pre-set PVS_BLENDER.
set -u
find_blender() {
  if [ -n "${PVS_BLENDER:-}" ] && [ -x "$PVS_BLENDER" ]; then echo "$PVS_BLENDER"; return; fi
  if command -v blender >/dev/null 2>&1; then command -v blender; return; fi
  local c
  for c in $(ls -d /c/tools/blender-*/blender.exe "/c/Program Files/Blender Foundation"/Blender*/blender.exe \
             /opt/blender*/blender /Applications/Blender.app/Contents/MacOS/Blender 2>/dev/null | sort -rV); do
    [ -x "$c" ] && { echo "$c"; return; }
  done
}
B=$(find_blender)
F=$(command -v ffmpeg 2>/dev/null || true)
ok=1
if [ -n "$B" ]; then
  echo "PVS_BLENDER=\"$B\""
  "$B" -b --version 2>/dev/null | head -1 | sed 's/^/# /'
else
  ok=0
  cat <<'EOF'
# Blender NOT FOUND. Install the portable build (winget's Blender download can 403):
#   mkdir -p /c/tools && cd /c/tools
#   M=https://mirrors.ocf.berkeley.edu/blender/release/Blender5.2
#   curl -sL -A "Mozilla/5.0" -o blender.zip $M/blender-5.2.1-windows-x64.zip
#   curl -sL -A "Mozilla/5.0" $M/blender-5.2.1.sha256 | grep windows-x64.zip   # compare with:
#   sha256sum blender.zip && unzip -q blender.zip && rm blender.zip
EOF
fi
if [ -n "$F" ]; then echo "PVS_FFMPEG=\"$F\""; else
  ok=0; echo "# ffmpeg NOT FOUND. Install: winget install --id Gyan.FFmpeg -e (then open a new shell)"; fi
command -v node >/dev/null 2>&1 || { ok=0; echo "# node NOT FOUND (used by the tools to read JSON). Install Node.js LTS."; }
nproc 2>/dev/null | sed 's/^/# CPU threads: /'
[ $ok = 1 ]
