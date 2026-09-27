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
