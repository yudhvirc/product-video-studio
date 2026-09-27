# Tathastu Claude Code plugins

Claude Code plugin marketplace **`tathastu-tools`**.

| Plugin | What it does |
|---|---|
| [`product-video-studio`](product-video-studio/README.md) | Photoreal 3D product videos (15 s cinematic ad + seamless 8 s turntable) of jewelry and crystal products from their photos, single or batch, with hard approval gates (plan → stills → proof → delivery) |

## Install

This repo is private, so sign the machine in to GitHub first (one time). Then run in a terminal
(PowerShell or Git Bash):

```bash
# 1. Sign in to GitHub so the private repo can be cloned (one time)
#    (no gh yet? winget install --id GitHub.cli -e, then open a new terminal)
gh auth login
gh auth setup-git

# 2. Add the marketplace and install the plugin
claude plugin marketplace add yudhvirc/product-video-studio
claude plugin install product-video-studio@tathastu-tools

# 3. Check it's installed
claude plugin list
```

If you're already inside Claude Code:
```text
/plugin marketplace add yudhvirc/product-video-studio
/plugin install product-video-studio@tathastu-tools
/reload-plugins
```

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
