---
name: product-video-batch
description: Batch-produce 3D product videos (ad + turntable) for many jewelry/crystal products at once, one folder per product. Use when the user wants videos for several products, a whole collection, new arrivals, or "all products in this folder"; or asks to check or resume a batch render. Shares one interview and look across products, drafts every spec from the photos, gets one consolidated approval, then renders a resumable queue.
argument-hint: "[products root folder]"
---

# Product Video Studio: batch

Same engine and quality bar as the single-product skill. Read and follow
`${CLAUDE_PLUGIN_ROOT}/skills/product-video/SKILL.md` and its `reference/` files; this skill adds the batch flow.
Tools: `${CLAUDE_PLUGIN_ROOT}/tools/batch.sh` (status · stills · proof · final · contact) wraps `render.sh`.

## Folder layout

```
<products_root>/
  _batch_defaults.json        shared look/output/videos (written in step 2)
  _library/stones.json        approved stone looks, reused across products
  _batch.log                  queue log
  <slug>/photos/*.jpg|png     overview + close-ups of every charm/spacer (+ daylight shot)
  <slug>/spec.json            drafted in step 3
  <slug>/SKIP                 optional: exclude from runs
  <slug>/previews/vN proofs/vN final/vN   outputs; every run adds a new vN, nothing is overwritten
  (frames and .blend files are cached outside the project in %LOCALAPPDATA%/pvs_work/<slug>)
```
If the user drops photos in one flat folder, propose a grouping into product folders (by filename or by what the
photos show) and confirm it before moving anything.

## Steps

1. **Environment + inventory.** Run `check_env.sh`, then `batch.sh <root> status`. **Read every photo** of every
   product. Classify each product: strung / tumble / custom (see `custom-products.md`). Custom products need
   their own builder, so flag them and estimate the extra effort.

2. **One shared interview** (AskUserQuestion, at most 4 per round). Ask once for the whole batch: platform/aspect,
   look/backdrop policy (one backdrop for all, or match each product's shop photo colour?), which videos and
   their lengths, fps, and quality/time budget. Save the answers to `_batch_defaults.json` and merge them into
   every spec.

3. **Draft every spec from the photos.** For each product, count beads, estimate size, write the sequence, pick
   the front piece, choose stone looks (prefer `_library` / `templates/stones.json`, otherwise sample a palette),
   and set up `photo_charm` parts from close-ups.
   Then show **one consolidated table** (product · type · stone · beads · sequence · front · open issues) and ask
   only the genuinely uncertain points, grouped. **Missing close-ups block that product:** list exactly which
   photos are needed and keep going with the others. Don't invent components.
   **→ Gate `plan`** for the batch (see below). Nothing renders before it.

4. **Stills for all:** `batch.sh <root> stills` (about 1–2 min per product), then `batch.sh <root> contact` and
   `checks.sh <dir> charms|sheet` per product. Run the quality checklist on every product yourself. Fix, then
   present: the contact sheet first, then per-product sheets and side-by-sides for anything new or doubtful.
   **→ Gate `stills`** for the batch. Products with requested changes get fixed, re-rendered and re-asked, while
   approved ones move on.

5. **Proofs (required before any final):** `batch.sh <root> proof` in the background (about 25 min per product
   for 15 s + 8 s). It renders only products whose stills are approved and reports the rest as "awaiting
   approval". Review the proof sheets and share the videos. **→ Gate `proof`** for the batch, with the
   final-queue estimate in the Approve option: Σ frames × ~12 s (e.g. 10 products × 690 frames ≈ 23 h).
   Offer to run overnight, split into sessions, or cut lengths or fps.

6. **Final queue:** `batch.sh <root> final` in the background. It renders only products with an approved proof
   of their current spec. Products render sequentially (parallel runs only slow each other down). Report
   progress with `batch.sh <root> status` (its last column shows how far each product's approvals allow it to
   go). The queue is resumable: after an interruption or reboot, run the same command again.

7. **Deliver:** verify every latest `final/vN/*.mp4` (ffprobe duration, frames, resolution; look at a few frames) and give
   a table of product → files. **→ Gate `delivery`** for the batch. Add any newly approved stone looks to
   `_library/stones.json`.

## Approval gates for a batch (mandatory)

The gates, rules and tool enforcement are exactly those in the single-product skill's "Approval gates" section:
read it. Batch specifics:
- One AskUserQuestion per stage covers every product that reached it. List the products and their preview/proof
  paths in the question text. Options: **"Approve all listed – continue to <next> (<estimate>)"** ·
  **"Approve some – I'll name the exceptions"** · **"Request changes"** · **"Stop here"**.
- Record the decision **per product**:
  `approve.sh <root>/<slug> <gate> <approved|changes|stopped> "<the user's words>"`. For "approve some",
  products the user excluded get `changes` with their words, and the rest get `approved`.
- Never record an approval for a product the user didn't cover. Products that miss a gate simply wait: the
  tools skip them and `batch.sh status` shows how far each may go.

## Batch etiquette
- One approval question per stage for the whole batch, with decisions recorded per product.
- Keep the user informed with short status lines during long runs (product n of N, ETA).
- Never delete or overwrite anything in the product folders (the user asked for this). Outputs are versioned,
  and if a cleanup seems needed, ask first.
