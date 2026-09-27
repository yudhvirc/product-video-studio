# Tathastu Claude Code plugins

Claude Code plugin marketplace **`tathastu-tools`**.

| Plugin | What it does |
|---|---|
| [`product-video-studio`](product-video-studio/README.md) | Photoreal 3D product videos (15 s cinematic ad + seamless 8 s turntable) of jewelry and crystal products from their photos, single or batch, with hard approval gates (plan → stills → proof → delivery) |

## Install

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

## Install with PowerShell (no git)

Open **PowerShell** (Start → type "PowerShell" → Enter), paste this line and press Enter:

```powershell
irm https://raw.githubusercontent.com/yudhvirc/product-video-studio/main/install.ps1 | iex
```

It downloads the latest release and installs it into `%USERPROFILE%\.claude\skills\product-video-studio`.
Restart Claude Code afterwards. **Run the same line again to update.** An old copy is moved to `%TEMP%`, not
deleted. The script is [`install.ps1`](install.ps1) if you want to read it first.

Or run the steps yourself:
```powershell
$skills = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path $skills | Out-Null
Invoke-WebRequest -UseBasicParsing -OutFile "$env:TEMP\product-video-studio.zip" `
  -Uri https://github.com/yudhvirc/product-video-studio/releases/latest/download/product-video-studio.zip
Expand-Archive "$env:TEMP\product-video-studio.zip" -DestinationPath $skills -Force
```

The marketplace commands above also work as-is in PowerShell:
```powershell
claude plugin marketplace add https://github.com/yudhvirc/product-video-studio.git
claude plugin install product-video-studio@tathastu-tools
```

## Install without git (download a zip)

No commands and no git needed:

1. Download the plugin:
   **https://github.com/yudhvirc/product-video-studio/releases/latest/download/product-video-studio.zip**
2. Open File Explorer, click the address bar, type `%USERPROFILE%\.claude` and press Enter. If there's no
   `skills` folder there, create one (right-click → New → Folder → `skills`).
3. Right-click the downloaded zip → **Extract All…** → **Browse…** → choose that `skills` folder → **Extract**.
   Check that the result is `C:\Users\<you>\.claude\skills\product-video-studio\`, and that it contains a
   `.claude-plugin` folder. If Windows added an extra `product-video-studio` level, move the inner folder up
   one level.
4. Restart Claude Code. The plugin loads in every session.

To update, delete `C:\Users\<you>\.claude\skills\product-video-studio` and repeat the steps with the latest
zip. Use either this method or the marketplace install above, not both, to avoid loading the plugin twice.

## Update

```bash
claude plugin marketplace update tathastu-tools
claude plugin update product-video-studio@tathastu-tools
```

## Use

- One product: `/product-video-studio:product-video`, or just ask, e.g. "make a 3D video of the tiger eye
  bracelet".
- Many products: `/product-video-studio:product-video-batch`, e.g. "make videos for all products in this folder".

Rendering requirements (Blender 5.x, ffmpeg, Node.js, Git Bash on Windows), troubleshooting for
"claude is not recognized", and full usage are in the
[plugin README](product-video-studio/README.md).
