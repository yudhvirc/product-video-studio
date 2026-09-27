# Product Video Studio (Claude Code plugin)

Photoreal 3D product videos of jewelry and crystal products from ordinary product photos:
a **15 s cinematic ad** (close glide → reveal → hero) and a **seamless 8 s turntable loop**,
rendered with Blender Cycles. Products are matched to the real piece, including its imperfections.

## Install

### On any machine (from GitHub)

The repo is public: no GitHub account or sign-in is needed. Use the **HTTPS** URL. The short form
`yudhvirc/product-video-studio` clones over SSH and fails with "Host key verification failed" on machines
without SSH set up.

In a terminal (PowerShell or Git Bash):
```bash
claude plugin marketplace add https://github.com/yudhvirc/product-video-studio.git
claude plugin install product-video-studio@tathastu-tools
claude plugin list
```

Or inside Claude Code:
```text
/plugin marketplace add https://github.com/yudhvirc/product-video-studio.git
/plugin install product-video-studio@tathastu-tools
/reload-plugins
```

Easiest for non-technical users: in Claude Code, just say
*"Install the product-video-studio plugin from https://github.com/yudhvirc/product-video-studio"* and let
Claude run the steps.

### Without git (download a zip)

No commands and no git needed:

1. Download the plugin:
   **https://github.com/yudhvirc/product-video-studio/releases/latest/download/product-video-studio.zip**
2. Open File Explorer, click the address bar, type `%USERPROFILE%\.claude` and press Enter. If there's no
   `skills` folder there, create one (right-click → New → Folder → `skills`).
3. Right-click the downloaded zip → **Extract All…** → **Browse…** → choose that `skills` folder → **Extract**.
   Check that the result is `C:\Users\<you>\.claude\skills\product-video-studio\`, and that it contains a
   `.claude-plugin` folder. If Windows added an extra `product-video-studio` level, move the inner folder up
   one level.
4. Restart Claude Code. The plugin loads in every session (`claude plugin list` shows
   `product-video-studio@skills-dir`).

To update, delete that folder and repeat the steps with the latest zip. Use either this method or the
marketplace install, not both, to avoid loading the plugin twice.

### On the machine that has the source folder

```text
/plugin marketplace add C:\temp\tathastumedia\plugins
/plugin install product-video-studio@tathastu-tools
```
Validate after editing with `claude plugin validate C:\temp\tathastumedia\plugins`.

### Updates

After a new version is pushed (bump `version` in `.claude-plugin/plugin.json`):
```bash
claude plugin marketplace update tathastu-tools
claude plugin update product-video-studio@tathastu-tools
```
Then run `/reload-plugins`, or restart Claude Code.

### Releasing a new version (maintainer)

Bump `version` in `.claude-plugin/plugin.json`, then commit and push. Then publish the plugin-only zip that
the download link serves. From the repo root:
```bash
V=1.2.0   # the new version
git archive --format=zip --prefix=product-video-studio/ HEAD:product-video-studio -o product-video-studio.zip
gh release create v$V product-video-studio.zip --title "product-video-studio $V" --notes "..."
```
The `releases/latest/download/product-video-studio.zip` link then serves the new zip.

### Requirements for rendering

These are checked by `tools/check_env.sh`. The skills report anything missing and ask before installing:
- Blender 5.x: the portable zip unpacked in `C:\tools\` is fine. Use a mirror such as
  `https://mirrors.ocf.berkeley.edu/blender/release/Blender5.2/` (winget's Blender download can 403) and
  check the SHA-256.
- ffmpeg: `winget install --id Gyan.FFmpeg -e`
- Node.js LTS
- bash: Git Bash on Windows

### Troubleshooting: "claude is not recognized"

If `claude` only works when you type its full path, its folder isn't on your PATH. Add it once in PowerShell,
then open a new terminal:
```powershell
$dir = "$env:USERPROFILE\.local\bin"   # folder containing claude.exe (npm installs: $env:APPDATA\npm)
$old = [Environment]::GetEnvironmentVariable("Path", "User")
if (($old -split ";") -notcontains $dir) { [Environment]::SetEnvironmentVariable("Path", "$old;$dir", "User") }
```
Check with `claude --version` from any folder. `claude doctor` shows where Claude Code is installed.

## Use

| You say | Skill |
|---|---|
| "Make a 3D video of the green onyx bracelet in products\green-onyx" | `/product-video-studio:product-video` |
| "Make videos for all the new products in C:\temp\tathastumedia\products" | `/product-video-studio:product-video-batch` |
| "How far along is the batch render?" | batch (runs `batch.sh status`) |

Both skills interview you first, then go through **hard approval gates**:

| Gate | You approve | Unlocks |
|---|---|---|
| plan | The drafted spec (sequence, stones, look, videos, time estimate) | preview stills |
| stills | Preview stills and side-by-sides with your photos | proof video |
| proof | The low-res proof videos, plus the final time estimate | final render |
| delivery | The finished videos | done |

Every decision is appended to `<product>/approvals.md` with your own words. The tools refuse to render past an
unapproved gate, and any change to the spec or engine after an approval requires a fresh one.

## Products folder

```
products/
  _library/stones.json          approved stone looks (reused across products)
  <slug>/photos/                overview + close-up of every charm/spacer + a daylight shot
  <slug>/spec.json              product description (the skill writes it)
  <slug>/previews/vN proofs/vN final/vN     every run adds a new version; nothing is ever overwritten
                                            (frames/.blend cache: %LOCALAPPDATA%\pvs_work\<slug>)
```

## What's built in

- **Strung** bracelets and anklets: beads (any stone), rhinestone rondelles, metal balls, and photo-relief
  charms built from a close-up photo. A relaxed irregular loop with the cord showing in some gaps.
- **Tumble stones**: irregular polished pebbles, from pebble-round to rounded-box.
- **Stone patterns:** fibrous · banded · crystalline · clear · mottled · speckled · metallic · porous,
  with a library of starting looks.
- **Backdrops:** studio white, and velvet or linen in the shop's colours (royal blue, burgundy, mustard, teal,
  emerald, purple, black, cream).
- **Aspects:** 16:9, 9:16, 1:1, 4:5. **Quality:** proof (about 2 s/frame), final (about 12 s/frame), high
  (about 30 s/frame), measured on a 16-core CPU.
- **Custom products** (rings, gem trees, malas, pyramids, Shivling, selenite): a builder hook plus recipes in
  `skills/product-video/reference/custom-products.md`.

## Command-line tools (what the skills run)

```bash
tools/check_env.sh                                   # find Blender / ffmpeg
tools/approve.sh  <product_dir> plan|stills|proof|delivery approved|changes|stopped "<user's words>"
tools/approve.sh  <product_dir> check stills|proof|final | show
tools/render.sh   <product_dir> stills|proof|final|high [ad|turntable|both]
tools/checks.sh   <product_dir> charms|sheet|proofsheet
tools/batch.sh    <products_root> status|stills|proof|final|contact [slug ...]
blender -b --python tools/sample_palette.py -- <photo> x0 y0 x1 y1 [--white x0 y0 x1 y1]
```
Renders are resumable: re-run the same command after an interruption.
