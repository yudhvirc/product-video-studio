"""Render settings. Presets were benchmarked on a 16-core Ryzen 9 CPU (no GPU):
proof ~2 s/frame, final ~12 s/frame, high ~30 s/frame at 1080p."""
import bpy
from .camera import ASPECTS

PRESETS = {
    "proof": dict(pct=50, samples=8, threshold=0.08),
    "final": dict(pct=100, samples=20, threshold=0.04),
    "high":  dict(pct=100, samples=64, threshold=0.02),
}


def configure(spec, quality="final"):
    q = PRESETS[quality]
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    r.resolution_x, r.resolution_y = ASPECTS[spec.get("output", {}).get("aspect", "16:9")]
    r.resolution_percentage = q["pct"]
    cy.samples = q["samples"]
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = q["threshold"]
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces = 10
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 6
    cy.transmission_bounces = 10
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = True
    cy.caustics_refractive = False
    cy.blur_glossy = 0.5
    cy.sample_clamp_indirect = 8.0
    r.use_persistent_data = True
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    r.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = spec.get("look", {}).get("exposure", 0.0)
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.color_depth = '8'
