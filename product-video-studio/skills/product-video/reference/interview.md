# Interview: the questions that matter

Use AskUserQuestion. At most 4 questions per round, recommended option first, and never ask what the
photos already answer: state what you saw and ask only for confirmation. Typical flow is 2–3 rounds.
If the user answers with an image or free text, follow that over the options.

## Round 1: purpose and look (skip items settled by batch defaults)

| Question | Options (recommended first) | Why it matters |
|---|---|---|
| Where will the video be used? | Website/YouTube 16:9 · Instagram Reel/Story 9:16 · Square feed 1:1 · Product listing 4:5 or 1:1 | Sets `output.aspect` and framing |
| What look? | Match the shop: coloured velvet (name the colour) · Clean studio white · Cream linen · Dark luxury (black velvet) | `look.backdrop` and `backdrop_color`. Tathastu shop photos use royal blue, burgundy, mustard, teal, emerald, purple velvet and cream linen |
| What should the videos show? | Both: cinematic ad + turntable loop · Ad only · Turntable only | `videos` |
| Quality vs. time | Fast 1080p (~12 s/frame) · High (~30 s/frame) | render preset; say the hours |

## Round 2: product truth (the part that makes or breaks realism)

Always state what you counted or saw, then ask for confirmation:
- **Stone.** "Sunstone / peach moonstone / not sure (match the photo)". The name drives the pattern family (see the table below).
- **Which photo shows the true colour?** Photos under different light disagree. Offer each photo plus "the render
  you showed me". (On the sunstone job the user picked the rendered colour after seeing it.)
- **Bead size and count.** "I count 18 × ~10 mm, right?" Offer ±2 mm alternatives. Size sets the whole scale.
- **Sequence around the loop.** Spell it out: "10 beads, rondelle, 2 beads, butterfly, 2 beads, rondelle, 4 beads".
  Ask which piece faces the front (`product.front`).
- **Finishing.** Hide the knot and loose elastic ends (recommended) · exactly as photographed · keep the tag only.
- **Charm orientation.** Faces outward as worn (recommended) · lies flat facing up.
- **Metal colour.** Should all metals match? Bright gold · antique brass · silver · rose gold.

## Round 3: references (ask for photos, don't guess)

For every non-bead component that isn't sharp in the photos, ask for **a close-up of that part alone**, straight on,
on a plain neutral background (grey or white paper), in soft light. Also useful:
- A daylight shot of the whole piece (true colour).
- Something for scale (a finger, a ruler) if the bead size is uncertain.
- For photo charms: one straight-on shot, with the cord running vertically if possible.

## Round 4 (after previews): review questions that worked

When the user rejects a preview, don't guess the reason. Ask a pointed question with options, e.g. "What doesn't
look right? Charm looks flat · Size/proportion · Colour · Something else (describe)". Then fix exactly that and
show a side-by-side with the reference. Past corrections to anticipate:
- "Too perfect": turn realism up (gaps, lumps, drift, grain) and use photo-relief for metal parts.
- "The inside of the wings is still perfect": build the part from the photo (photo_charm).
- "Black bleeding outside the boundary": the shadow peel in photo_charm handles it; raise `shadow_lum` if needed.
- "Rondelle gold should match the butterfly": use the same `metal` on every part.
- "Remove the vignette": set `look.vignette` false (the default).

## Stone name → pattern family

| Pattern | Stones |
|---|---|
| fibrous | sunstone, moonstone, black tourmaline, selenite-like silky stones |
| banded | tiger eye, agate, onyx bands, malachite |
| crystalline | amethyst, rose quartz, fluorite, milky/chevron quartz |
| clear | clear quartz, citrine, glass crystal beads (set `transmission`, `cloudiness`) |
| mottled | green aventurine (+ `flecks`), jade, rhodonite, howlite |
| speckled | jasper, dalmatian stone, unakite |
| metallic | pyrite, hematite |
| porous | lava stone (matte) |
