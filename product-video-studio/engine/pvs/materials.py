"""Materials: natural stones (by pattern family), metals, crystals, cord and
backdrops. Every material carries real-world imperfections by default; the
spec can dial `realism` down, but never to CG-perfect by default."""
import math
from .util import new_mat, node, rgba

METALS = {                    # linear base colours
    "bright_gold":   (1.0, 0.64, 0.17),
    "antique_brass": (0.72, 0.56, 0.24),   # matched on the sunstone bracelet: rondelles == butterfly
    "brass":         (0.80, 0.60, 0.25),
    "rose_gold":     (0.95, 0.60, 0.50),
    "silver":        (0.92, 0.92, 0.93),
    "antique_silver": (0.70, 0.70, 0.72),
    "copper":        (0.95, 0.52, 0.33),
    "gunmetal":      (0.28, 0.28, 0.30),
}


def metal_rgb(spec):
    if isinstance(spec, str):
        return METALS[spec]
    return tuple(spec)


# ---------------------------------------------------------------- stones
def _palette_ramp(nt, palette):
    ramp = node(nt, "ShaderNodeValToRGB")
    cr = ramp.color_ramp
    pal = sorted(palette, key=lambda s: s[0])
    cr.elements[0].position, cr.elements[0].color = pal[0][0], rgba(pal[0][1])
    cr.elements[1].position, cr.elements[1].color = pal[-1][0], rgba(pal[-1][1])
    for p, c in pal[1:-1]:
        e = cr.elements.new(p); e.color = rgba(c)
    return ramp


def stone_material(name, cfg):
    """cfg keys (all optional except palette):
      palette      [[pos, [r,g,b]], ...] linear RGB, pos 0..1 (sample with tools/sample_palette.py)
      pattern      fibrous | banded | mottled | clear | porous | metallic | speckled
      flecks       {"density": 0..1, "color": [r,g,b]}   aventurescence / glitter
      translucency 0..1   subsurface glow (default 0.25; clear stones use transmission)
      gloss        coat roughness (default 0.03; porous stones are matte)
      tone_variation  per-bead light/dark shift (default 0.2)
      inclusions   0..1 dark specks density (default 0.25)
      realism      0..1 polish waviness, hairline scratches, pits (default 1)
    """
    pattern = cfg.get("pattern", "fibrous")
    realism = cfg.get("realism", 1.0)
    m, nt = new_mat(name)
    L = nt.links
    out = node(nt, "ShaderNodeOutputMaterial")
    bsdf = node(nt, "ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs["Surface"])

    tc = node(nt, "ShaderNodeTexCoord")
    info = node(nt, "ShaderNodeObjectInfo")
    rot = node(nt, "ShaderNodeVectorMath"); rot.operation = 'SCALE'
    L.new(info.outputs["Random"], rot.inputs["Scale"])
    rot.inputs[0].default_value = (40.0, 57.0, 23.0)
    mapping = node(nt, "ShaderNodeMapping")
    L.new(tc.outputs["Object"], mapping.inputs["Vector"])
    L.new(rot.outputs[0], mapping.inputs["Rotation"])
    L.new(rot.outputs[0], mapping.inputs["Location"])
    vec = mapping.outputs[0]

    warp = node(nt, "ShaderNodeTexNoise", Scale=1.3, Detail=3.0)
    L.new(vec, warp.inputs["Vector"])
    warped = node(nt, "ShaderNodeVectorMath"); warped.operation = 'MULTIPLY_ADD'
    L.new(warp.outputs["Color"], warped.inputs[0])
    warped.inputs[1].default_value = (0.9, 0.9, 0.9)
    L.new(vec, warped.inputs[2])

    # ---- the pattern factor 0..1 that indexes the palette
    if pattern in ("fibrous", "banded"):
        stretch = node(nt, "ShaderNodeMapping")
        stretch.inputs["Scale"].default_value = (0.9, 0.9, 6.0)
        L.new(warped.outputs[0], stretch.inputs["Vector"])
        fiber = node(nt, "ShaderNodeTexNoise", Scale=1.4, Detail=12.0, Roughness=0.72)
        L.new(stretch.outputs[0], fiber.inputs["Vector"])
        if pattern == "banded":   # tiger eye / agate: soft, wandering bands through the fibres
            bands = node(nt, "ShaderNodeTexWave", Scale=1.2, Distortion=9.0, Detail=8.0,
                         **{"Detail Roughness": 0.65})
            bands.wave_type = 'BANDS'
            L.new(warped.outputs[0], bands.inputs["Vector"])
            a, b = bands.outputs["Fac"], fiber.outputs["Fac"]
            mixf = 0.7
        else:
            noise = node(nt, "ShaderNodeTexNoise", Scale=1.8, Detail=8.0, Roughness=0.6)
            L.new(vec, noise.inputs["Vector"])
            a, b = noise.outputs["Fac"], fiber.outputs["Fac"]
            mixf = 0.55
        mix = node(nt, "ShaderNodeMix", Factor=mixf); mix.data_type = 'FLOAT'
        L.new(a, mix.inputs[2]); L.new(b, mix.inputs[3])
        fac = mix.outputs[0]
    elif pattern == "speckled":
        base = node(nt, "ShaderNodeTexNoise", Scale=2.0, Detail=6.0)
        L.new(vec, base.inputs["Vector"])
        spk = node(nt, "ShaderNodeTexVoronoi", Scale=18.0)
        L.new(warped.outputs[0], spk.inputs["Vector"])
        mix = node(nt, "ShaderNodeMix", Factor=0.5); mix.data_type = 'FLOAT'
        L.new(base.outputs["Fac"], mix.inputs[2]); L.new(spk.outputs["Distance"], mix.inputs[3])
        fac = mix.outputs[0]
    elif pattern == "crystalline":
        # amethyst / quartz / fluorite: broad mottled colour zones crossed by
        # pale crystal boundaries and hairline fractures
        mott = node(nt, "ShaderNodeTexNoise", Scale=1.1, Detail=8.0, Roughness=0.6)
        L.new(warped.outputs[0], mott.inputs["Vector"])
        cells = node(nt, "ShaderNodeTexVoronoi", Scale=2.4); cells.feature = 'DISTANCE_TO_EDGE'
        L.new(warped.outputs[0], cells.inputs["Vector"])
        veins = node(nt, "ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 0.06, "To Min": cfg.get("veins", 0.22), "To Max": 0.0})
        L.new(cells.outputs["Distance"], veins.inputs["Value"])
        cracks = node(nt, "ShaderNodeTexVoronoi", Scale=7.0); cracks.feature = 'DISTANCE_TO_EDGE'
        L.new(vec, cracks.inputs["Vector"])
        crk = node(nt, "ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 0.02, "To Min": cfg.get("fractures", 0.08), "To Max": 0.0})
        L.new(cracks.outputs["Distance"], crk.inputs["Value"])
        s1 = node(nt, "ShaderNodeMath"); s1.operation = 'ADD'
        L.new(mott.outputs["Fac"], s1.inputs[0]); L.new(veins.outputs[0], s1.inputs[1])
        s2 = node(nt, "ShaderNodeMath"); s2.operation = 'ADD'
        L.new(s1.outputs[0], s2.inputs[0]); L.new(crk.outputs[0], s2.inputs[1])
        fac = s2.outputs[0]
    else:   # mottled, clear, porous, metallic
        noise = node(nt, "ShaderNodeTexNoise", Scale=1.6, Detail=10.0, Roughness=0.62)
        L.new(warped.outputs[0], noise.inputs["Vector"])
        fac = noise.outputs["Fac"]

    tone = node(nt, "ShaderNodeMath"); tone.operation = 'MULTIPLY_ADD'
    tv = cfg.get("tone_variation", 0.2)
    tone.inputs[1].default_value = tv; tone.inputs[2].default_value = -tv / 2
    L.new(info.outputs["Random"], tone.inputs[0])
    shifted = node(nt, "ShaderNodeMath"); shifted.operation = 'ADD'
    L.new(fac, shifted.inputs[0]); L.new(tone.outputs[0], shifted.inputs[1])
    ramp = _palette_ramp(nt, cfg["palette"])
    L.new(shifted.outputs[0], ramp.inputs["Fac"])
    color = ramp.outputs["Color"]
    normal = None

    # ---- flecks (aventurescence): tiny tilted mirrors that glint
    fl = cfg.get("flecks")
    fleck_mask = None
    if fl or pattern == "metallic":
        density = fl.get("density", 0.3) if fl else 0.9
        vor = node(nt, "ShaderNodeTexVoronoi", Scale=34.0 if pattern != "metallic" else 14.0)
        L.new(vec, vor.inputs["Vector"])
        sep = node(nt, "ShaderNodeSeparateColor"); L.new(vor.outputs["Color"], sep.inputs[0])
        small = node(nt, "ShaderNodeMath"); small.operation = 'LESS_THAN'
        small.inputs[1].default_value = 0.16 if pattern != "metallic" else 2.0
        L.new(vor.outputs["Distance"], small.inputs[0])
        pick = node(nt, "ShaderNodeMath"); pick.operation = 'GREATER_THAN'
        pick.inputs[1].default_value = 1.0 - density
        L.new(sep.outputs[0], pick.inputs[0])
        fm = node(nt, "ShaderNodeMath"); fm.operation = 'MULTIPLY'
        L.new(small.outputs[0], fm.inputs[0]); L.new(pick.outputs[0], fm.inputs[1])
        fleck_mask = fm.outputs[0]
        geo = node(nt, "ShaderNodeNewGeometry")
        tilt = node(nt, "ShaderNodeVectorMath"); tilt.operation = 'MULTIPLY_ADD'
        L.new(vor.outputs["Color"], tilt.inputs[0])
        amt = 1.8 if pattern != "metallic" else 0.7
        tilt.inputs[1].default_value = (amt,) * 3; tilt.inputs[2].default_value = (-amt / 2,) * 3
        add = node(nt, "ShaderNodeVectorMath"); add.operation = 'ADD'
        L.new(geo.outputs["Normal"], add.inputs[0]); L.new(tilt.outputs[0], add.inputs[1])
        nrm = node(nt, "ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
        L.new(add.outputs[0], nrm.inputs[0])
        nmix = node(nt, "ShaderNodeMix"); nmix.data_type = 'VECTOR'
        L.new(fleck_mask, nmix.inputs["Factor"])
        L.new(geo.outputs["Normal"], nmix.inputs[4]); L.new(nrm.outputs[0], nmix.inputs[5])
        normal = nmix.outputs[1]
        if pattern != "metallic":
            cm = node(nt, "ShaderNodeMix"); cm.data_type = 'RGBA'
            L.new(fleck_mask, cm.inputs["Factor"]); L.new(color, cm.inputs[6])
            cm.inputs[7].default_value = rgba(fl.get("color", (1.0, 0.52, 0.24)))
            color = cm.outputs[2]

    # ---- natural dark inclusions
    inc_d = cfg.get("inclusions", 0.25)
    if inc_d > 0:
        inc_v = node(nt, "ShaderNodeTexVoronoi", Scale=6.0)
        L.new(warped.outputs[0], inc_v.inputs["Vector"])
        inc_sep = node(nt, "ShaderNodeSeparateColor"); L.new(inc_v.outputs["Color"], inc_sep.inputs[0])
        inc_a = node(nt, "ShaderNodeMapRange", **{"From Min": 0.07, "From Max": 0.02})
        L.new(inc_v.outputs["Distance"], inc_a.inputs["Value"])
        inc_b = node(nt, "ShaderNodeMath"); inc_b.operation = 'GREATER_THAN'
        inc_b.inputs[1].default_value = 1.0 - inc_d * 0.9
        L.new(inc_sep.outputs[2], inc_b.inputs[0])
        inc = node(nt, "ShaderNodeMath"); inc.operation = 'MULTIPLY'
        L.new(inc_a.outputs[0], inc.inputs[0]); L.new(inc_b.outputs[0], inc.inputs[1])
        dark = node(nt, "ShaderNodeMix"); dark.data_type = 'RGBA'
        L.new(inc.outputs[0], dark.inputs["Factor"]); L.new(color, dark.inputs[6])
        dark.inputs[7].default_value = rgba(cfg.get("inclusion_color", (0.09, 0.045, 0.025)))
        color = dark.outputs[2]

    L.new(color, bsdf.inputs["Base Color"])
    if normal is not None:
        L.new(normal, bsdf.inputs["Normal"])

    # ---- surface response per family
    ior = cfg.get("ior", 1.54)
    bsdf.inputs["IOR"].default_value = ior
    polished = pattern not in ("porous",)
    if pattern == "clear":
        bsdf.inputs["Transmission Weight"].default_value = cfg.get("transmission", 0.92)
        bsdf.inputs["Roughness"].default_value = 0.02
        # cloudy veils: milky where the pattern is high
        cloud = node(nt, "ShaderNodeMapRange", **{"From Min": 0.55, "From Max": 0.8,
                                                   "To Min": 0.0, "To Max": cfg.get("cloudiness", 0.5)})
        L.new(fac, cloud.inputs["Value"])
        L.new(cloud.outputs[0], bsdf.inputs["Subsurface Weight"])
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 1.0, 1.0)
        bsdf.inputs["Subsurface Scale"].default_value = 0.001
    elif pattern == "metallic":
        met = node(nt, "ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.6, "To Min": 0.55, "To Max": 1.0})
        L.new(fac, met.inputs["Value"]); L.new(met.outputs[0], bsdf.inputs["Metallic"])
        bsdf.inputs["Roughness"].default_value = 0.22
        polished = cfg.get("polished", True)
    elif pattern == "porous":
        bsdf.inputs["Roughness"].default_value = 0.85
        pores = node(nt, "ShaderNodeTexVoronoi", Scale=26.0); pores.feature = 'SMOOTH_F1'
        L.new(vec, pores.inputs["Vector"])
        pr = node(nt, "ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 0.35})
        L.new(pores.outputs["Distance"], pr.inputs["Value"])
        pb = node(nt, "ShaderNodeBump", Strength=0.9, Distance=0.0002)
        L.new(pr.outputs[0], pb.inputs["Height"]); L.new(pb.outputs[0], bsdf.inputs["Normal"])
    else:
        rmix = node(nt, "ShaderNodeMath"); rmix.operation = 'MULTIPLY_ADD'
        rmix.inputs[1].default_value = -0.2 if fleck_mask else 0.0; rmix.inputs[2].default_value = 0.32
        if fleck_mask:
            L.new(fleck_mask, rmix.inputs[0])
            L.new(fleck_mask, bsdf.inputs["Metallic"])
        L.new(rmix.outputs[0], bsdf.inputs["Roughness"])
        sss = cfg.get("translucency", 0.25)
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Radius"].default_value = cfg.get("sss_radius", (1.0, 0.35, 0.12))
        bsdf.inputs["Subsurface Scale"].default_value = 0.0015

    if polished:
        bsdf.inputs["Coat Weight"].default_value = 1.0
        bsdf.inputs["Coat IOR"].default_value = ior
        gloss = cfg.get("gloss", 0.03)
        if realism > 0:
            # hand-polish waviness: highlights wobble instead of being perfect ellipses
            wav = node(nt, "ShaderNodeTexNoise", Scale=2.6, Detail=3.0, Roughness=0.5)
            L.new(vec, wav.inputs["Vector"])
            bump1 = node(nt, "ShaderNodeBump", Strength=0.35 * realism, Distance=0.00004)
            L.new(wav.outputs["Fac"], bump1.inputs["Height"])
            # hairline polishing scratches + tiny pits
            smap = node(nt, "ShaderNodeMapping")
            smap.inputs["Scale"].default_value = (2.0, 2.0, 90.0)
            smap.inputs["Rotation"].default_value = (0.6, 1.1, 0.3)
            L.new(vec, smap.inputs["Vector"])
            scr = node(nt, "ShaderNodeTexNoise", Scale=3.0, Detail=2.0)
            L.new(smap.outputs[0], scr.inputs["Vector"])
            scr_r = node(nt, "ShaderNodeMapRange", **{"From Min": 0.66, "From Max": 0.72})
            L.new(scr.outputs["Fac"], scr_r.inputs["Value"])
            pit_v = node(nt, "ShaderNodeTexVoronoi", Scale=22.0)
            L.new(vec, pit_v.inputs["Vector"])
            pit_sep = node(nt, "ShaderNodeSeparateColor"); L.new(pit_v.outputs["Color"], pit_sep.inputs[0])
            pa = node(nt, "ShaderNodeMath"); pa.operation = 'LESS_THAN'; pa.inputs[1].default_value = 0.05
            L.new(pit_v.outputs["Distance"], pa.inputs[0])
            pb = node(nt, "ShaderNodeMath"); pb.operation = 'GREATER_THAN'; pb.inputs[1].default_value = 0.8
            L.new(pit_sep.outputs[1], pb.inputs[0])
            pit = node(nt, "ShaderNodeMath"); pit.operation = 'MULTIPLY'
            L.new(pa.outputs[0], pit.inputs[0]); L.new(pb.outputs[0], pit.inputs[1])
            dent = node(nt, "ShaderNodeMath"); dent.operation = 'ADD'
            L.new(scr_r.outputs[0], dent.inputs[0]); L.new(pit.outputs[0], dent.inputs[1])
            neg = node(nt, "ShaderNodeMath"); neg.operation = 'MULTIPLY'; neg.inputs[1].default_value = -realism
            L.new(dent.outputs[0], neg.inputs[0])
            bump2 = node(nt, "ShaderNodeBump", Strength=0.5, Distance=0.00002)
            L.new(neg.outputs[0], bump2.inputs["Height"]); L.new(bump1.outputs[0], bump2.inputs["Normal"])
            L.new(bump2.outputs[0], bsdf.inputs["Coat Normal"])
            crm = node(nt, "ShaderNodeMath"); crm.operation = 'MULTIPLY_ADD'
            crm.inputs[1].default_value = 0.28 * realism; crm.inputs[2].default_value = gloss
            L.new(dent.outputs[0], crm.inputs[0]); L.new(crm.outputs[0], bsdf.inputs["Coat Roughness"])
        else:
            bsdf.inputs["Coat Roughness"].default_value = gloss
    return m


# ---------------------------------------------------------------- metals
def plated_metal_material(name, color):
    """Plated findings (rondelles, balls, caps): uneven polish, smudges, micro
    dents, a little tarnish in the crevices."""
    m, nt = new_mat(name)
    L = nt.links
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Metallic=1.0)
    L.new(b.outputs[0], out.inputs["Surface"])
    tc = node(nt, "ShaderNodeTexCoord")
    smudge = node(nt, "ShaderNodeTexNoise", Scale=900.0, Detail=4.0)
    L.new(tc.outputs["Object"], smudge.inputs["Vector"])
    rr = node(nt, "ShaderNodeMapRange", **{"From Min": 0.35, "From Max": 0.7, "To Min": 0.2, "To Max": 0.34})
    L.new(smudge.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs[0], b.inputs["Roughness"])
    dents = node(nt, "ShaderNodeTexNoise", Scale=4000.0, Detail=2.0)
    L.new(tc.outputs["Object"], dents.inputs["Vector"])
    bump = node(nt, "ShaderNodeBump", Strength=0.25, Distance=0.00002)
    L.new(dents.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    ao = node(nt, "ShaderNodeAmbientOcclusion", Distance=0.0005); ao.samples = 8
    inv = node(nt, "ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(ao.outputs["AO"], inv.inputs[1])
    tar = node(nt, "ShaderNodeMix"); tar.data_type = 'RGBA'
    L.new(inv.outputs[0], tar.inputs["Factor"])
    tar.inputs[6].default_value = rgba(color)
    tar.inputs[7].default_value = rgba([c * 0.45 for c in color])
    L.new(tar.outputs[2], b.inputs["Base Color"])
    return m


def photo_metal_material(name, color):
    """Patina for photo-relief parts, driven by the reference photo's brightness
    stored per vertex ('lum'): black grime in recesses, worn metal on the relief."""
    m, nt = new_mat(name)
    L = nt.links
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled")
    L.new(b.outputs[0], out.inputs["Surface"])
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "lum"; at.attribute_type = 'GEOMETRY'
    ramp = node(nt, "ShaderNodeValToRGB")
    cr = ramp.color_ramp
    c = color
    cr.elements[0].position, cr.elements[0].color = 0.06, (0.016, 0.012, 0.006, 1)
    cr.elements[1].position, cr.elements[1].color = 0.8, rgba([min(1, x * 1.12) for x in c])
    e = cr.elements.new(0.17); e.color = (0.07, 0.048, 0.02, 1)
    e = cr.elements.new(0.34); e.color = rgba([x * 0.8 for x in c])
    L.new(at.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    met = node(nt, "ShaderNodeMapRange", **{"From Min": 0.12, "From Max": 0.32, "To Min": 0.25, "To Max": 1.0})
    L.new(at.outputs["Fac"], met.inputs["Value"]); L.new(met.outputs[0], b.inputs["Metallic"])
    rgh = node(nt, "ShaderNodeMapRange", **{"From Min": 0.12, "From Max": 0.7, "To Min": 0.75, "To Max": 0.24})
    L.new(at.outputs["Fac"], rgh.inputs["Value"]); L.new(rgh.outputs[0], b.inputs["Roughness"])
    tc = node(nt, "ShaderNodeTexCoord")
    pores = node(nt, "ShaderNodeTexNoise", Scale=3500.0, Detail=6.0, Roughness=0.7)
    L.new(tc.outputs["Object"], pores.inputs["Vector"])
    bump = node(nt, "ShaderNodeBump", Strength=0.3, Distance=0.00003)
    L.new(pores.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m


def rhinestone_material():
    m, nt = new_mat("Rhinestone")
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.0, IOR=2.0,
             **{"Transmission Weight": 1.0, "Base Color": (1, 1, 1, 1)})
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def foil_material():
    m, nt = new_mat("Foil")
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Metallic=1.0, Roughness=0.05,
             **{"Base Color": (0.95, 0.95, 0.97, 1)})
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def cord_material(color=(0.85, 0.83, 0.78)):
    m, nt = new_mat("Cord")
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.4,
             **{"Base Color": rgba(color), "Subsurface Weight": 0.5, "Subsurface Scale": 0.0005})
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- backdrops
def studio_white_material():
    m, nt = new_mat("StudioWhite")
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.42,
             **{"Base Color": (0.87, 0.865, 0.855, 1), "Specular IOR Level": 0.35})
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = node(nt, "ShaderNodeTexCoord")
    fib = node(nt, "ShaderNodeTexNoise", Scale=2500.0, Detail=6.0)
    nt.links.new(tc.outputs["Object"], fib.inputs["Vector"])
    bump = node(nt, "ShaderNodeBump", Strength=0.08, Distance=0.00005)
    nt.links.new(fib.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def velvet_material(color):
    """Velvet as in the shop photos: deep colour, bright sheen on the folds,
    slightly crushed pile (uneven tone)."""
    m, nt = new_mat("Velvet")
    L = nt.links
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.95, **{"Sheen Weight": 1.0, "Sheen Roughness": 0.35,
                                                              "Specular IOR Level": 0.2})
    L.new(b.outputs[0], out.inputs["Surface"])
    tc = node(nt, "ShaderNodeTexCoord")
    crush = node(nt, "ShaderNodeTexNoise", Scale=60.0, Detail=6.0, Roughness=0.6)
    L.new(tc.outputs["Object"], crush.inputs["Vector"])
    cr = node(nt, "ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.8, "To Max": 1.15})
    L.new(crush.outputs["Fac"], cr.inputs["Value"])
    col = node(nt, "ShaderNodeVectorMath"); col.operation = 'SCALE'
    col.inputs[0].default_value = tuple(color)
    L.new(cr.outputs[0], col.inputs["Scale"])
    L.new(col.outputs[0], b.inputs["Base Color"])
    b.inputs["Sheen Tint"].default_value = rgba([min(1, 0.55 + c) for c in color])
    pile = node(nt, "ShaderNodeTexNoise", Scale=3000.0, Detail=3.0)
    L.new(tc.outputs["Object"], pile.inputs["Vector"])
    bump = node(nt, "ShaderNodeBump", Strength=0.15, Distance=0.00005)
    L.new(pile.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m


def linen_material(color):
    m, nt = new_mat("Linen")
    L = nt.links
    out = node(nt, "ShaderNodeOutputMaterial")
    b = node(nt, "ShaderNodeBsdfPrincipled", Roughness=0.85, **{"Base Color": rgba(color), "Sheen Weight": 0.3})
    L.new(b.outputs[0], out.inputs["Surface"])
    tc = node(nt, "ShaderNodeTexCoord")
    wx = node(nt, "ShaderNodeTexWave", Scale=900.0, Distortion=2.0, Detail=2.0); wx.bands_direction = 'X'
    wy = node(nt, "ShaderNodeTexWave", Scale=900.0, Distortion=2.0, Detail=2.0); wy.bands_direction = 'Y'
    L.new(tc.outputs["Object"], wx.inputs["Vector"]); L.new(tc.outputs["Object"], wy.inputs["Vector"])
    weave = node(nt, "ShaderNodeMath"); weave.operation = 'MAXIMUM'
    L.new(wx.outputs["Fac"], weave.inputs[0]); L.new(wy.outputs["Fac"], weave.inputs[1])
    bump = node(nt, "ShaderNodeBump", Strength=0.25, Distance=0.00005)
    L.new(weave.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m
