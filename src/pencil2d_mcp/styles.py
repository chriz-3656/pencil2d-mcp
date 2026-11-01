"""Art style renderers and procedural animation presets for Pencil2D MCP.

Includes comprehensive procedural character generators and animation sequences for:
- Stickman (Dynamic Martial Arts & Parkour with curved lines of action)
- Anime (Expressive eyes, layered hair volume, two-tone cel shading)
- Pencil Sketch (Multi-pass construction: blue gesture underdrawing + graphite contours + hatching)
- Studio Ghibli Aesthetic (Lush rolling grassy hills, painterly cumulus clouds, warm breeze)
- Doodle (Playful hand-drawn marker wobble, rubber-hose squash/stretch, cartoon sweat drops)
"""

import math
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw

from .drawing import (
    bow_curve,
    calculate_squash_stretch,
    draw_doodle_wobble_line,
    draw_dust_puff,
    draw_impact_spark,
    draw_pencil_sketch_stroke,
    draw_soft_gradient_glow,
    draw_speed_lines,
    draw_tapered_stroke,
    ease_in_out_cubic,
    ease_in_quad,
    ease_out_quad,
    ease_overshoot,
    parabolic_arc,
    sample_cubic_bezier,
)


# =========================================================================
# 1. DYNAMIC STICKMAN RENDERER
# =========================================================================

class StickmanRenderer:
    """Renders expressive, kinetic stick figures with proper line of action and weight."""

    COLOR = (26, 26, 36, 255)
    ACCENT = (235, 60, 60, 255) # Headband / sash

    @staticmethod
    def render_pose(width: int, height: int,
                    head_pos: Tuple[float, float],
                    spine_curve: List[Tuple[float, float]],
                    l_arm: List[Tuple[float, float]],
                    r_arm: List[Tuple[float, float]],
                    l_leg: List[Tuple[float, float]],
                    r_leg: List[Tuple[float, float]],
                    head_radius: float = 18.0,
                    headband_tail: Optional[List[Tuple[float, float]]] = None,
                    speed_trail: Optional[Tuple[Tuple[float, float], float]] = None,
                    dust_pos: Optional[Tuple[float, float]] = None,
                    spark_pos: Optional[Tuple[float, float]] = None) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Ground dust
        if dust_pos:
            draw_dust_puff(img, dust_pos, radius=18.0)

        # Speed lines
        if speed_trail:
            center, angle = speed_trail
            draw_speed_lines(img, center, direction_deg=angle, length=70.0, count=5)

        # Draw Limbs (curved Bezier / tapered strokes)
        draw_tapered_stroke(img, l_leg, StickmanRenderer.COLOR, base_width=5.0)
        draw_tapered_stroke(img, r_leg, StickmanRenderer.COLOR, base_width=5.0)
        draw_tapered_stroke(img, spine_curve, StickmanRenderer.COLOR, base_width=6.0)
        draw_tapered_stroke(img, l_arm, StickmanRenderer.COLOR, base_width=4.5)
        draw_tapered_stroke(img, r_arm, StickmanRenderer.COLOR, base_width=4.5)

        # Head (solid filled with clean antialiased outline)
        hx, hy = head_pos
        hr = head_radius
        draw = ImageDraw.Draw(img, "RGBA")
        draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=StickmanRenderer.COLOR)

        # Headband / Action sash accent
        if headband_tail:
            draw_tapered_stroke(img, headband_tail, StickmanRenderer.ACCENT, base_width=3.5)
            # Headband wrap on head
            draw.line([(hx - hr * 0.9, hy - hr * 0.2), (hx + hr * 0.9, hy - hr * 0.2)],
                      fill=StickmanRenderer.ACCENT, width=3)

        # Impact hit spark
        if spark_pos:
            draw_impact_spark(img, spark_pos, radius=28.0)

        return img

    @classmethod
    def generate_animation(cls, width: int = 800, height: int = 600,
                           action: str = "jump", frame_count: int = 12) -> List[Image.Image]:
        frames = []
        cx = width * 0.5
        ground_y = height * 0.78

        if action == "run":
            for f in range(frame_count):
                phase = (f / float(frame_count)) * (2.0 * math.pi)
                bob = math.sin(phase * 2.0) * 14.0
                forward_x = cx - 80 + (f / float(frame_count)) * 160.0

                # Running pose parameters
                head_x = forward_x + 18.0
                head_y = ground_y - 120.0 + bob
                pelvis_x = forward_x
                pelvis_y = ground_y - 55.0 + bob

                spine = bow_curve((head_x, head_y + 12), (pelvis_x, pelvis_y), bow_amount=12.0)

                # Alternating leg stride
                l_foot_x = pelvis_x + math.sin(phase) * 45.0
                l_foot_y = ground_y - max(0.0, -math.cos(phase)) * 25.0
                r_foot_x = pelvis_x + math.sin(phase + math.pi) * 45.0
                r_foot_y = ground_y - max(0.0, -math.cos(phase + math.pi)) * 25.0

                l_knee = ((pelvis_x + l_foot_x) * 0.5 + 8, (pelvis_y + l_foot_y) * 0.5 - 10)
                r_knee = ((pelvis_x + r_foot_x) * 0.5 - 8, (pelvis_y + r_foot_y) * 0.5 - 10)

                l_leg = [ (pelvis_x, pelvis_y), l_knee, (l_foot_x, l_foot_y) ]
                r_leg = [ (pelvis_x, pelvis_y), r_knee, (r_foot_x, r_foot_y) ]

                # Alternating arms (opposite to legs)
                l_hand_x = forward_x - math.sin(phase) * 35.0
                l_hand_y = head_y + 25.0 + math.cos(phase) * 15.0
                r_hand_x = forward_x - math.sin(phase + math.pi) * 35.0
                r_hand_y = head_y + 25.0 + math.cos(phase + math.pi) * 15.0

                l_arm = [ (head_x - 4, head_y + 18), ((head_x + l_hand_x)*0.5, head_y + 35), (l_hand_x, l_hand_y) ]
                r_arm = [ (head_x - 4, head_y + 18), ((head_x + r_hand_x)*0.5, head_y + 35), (r_hand_x, r_hand_y) ]

                tail = bow_curve((head_x - 12, head_y - 2), (head_x - 45, head_y - 10 + math.sin(phase) * 8), bow_amount=6.0)

                dust = (forward_x - 25, ground_y + 2) if (f % 4 == 0) else None

                frame_img = cls.render_pose(
                    width, height, (head_x, head_y), spine, l_arm, r_arm, l_leg, r_leg,
                    headband_tail=tail, dust_pos=dust
                )
                frames.append(frame_img)

        else: # "jump" or action leap
            for f in range(frame_count):
                t = f / float(max(1, frame_count - 1))
                if t < 0.25:
                    # 1. Anticipation: deep crouch & squash
                    sub_t = t / 0.25
                    crouch = ease_in_quad(sub_t) * 35.0
                    head_y = ground_y - 95.0 + crouch
                    pelvis_y = ground_y - 40.0 + crouch * 0.8
                    spine = bow_curve((cx, head_y + 12), (cx, pelvis_y), bow_amount=-8.0)
                    l_leg = [(cx, pelvis_y), (cx - 25, (pelvis_y + ground_y)*0.5 + 10), (cx - 15, ground_y)]
                    r_leg = [(cx, pelvis_y), (cx + 25, (pelvis_y + ground_y)*0.5 + 10), (cx + 15, ground_y)]
                    l_arm = [(cx, head_y + 20), (cx - 30, head_y + 45), (cx - 40, head_y + 30)]
                    r_arm = [(cx, head_y + 20), (cx + 30, head_y + 45), (cx + 40, head_y + 30)]
                    tail = [(cx - 12, head_y), (cx - 30, head_y - 5)]
                    frame_img = cls.render_pose(width, height, (cx, head_y), spine, l_arm, r_arm, l_leg, r_leg, headband_tail=tail)

                elif t < 0.65:
                    # 2. Launch & Apex: stretch up parabolic jump
                    sub_t = (t - 0.25) / 0.40
                    arc_x, arc_y = parabolic_arc((cx, ground_y - 95), (cx + 60, ground_y - 280), (cx + 120, ground_y - 95), sub_t)
                    spine = bow_curve((arc_x, arc_y + 12), (arc_x - 15, arc_y + 60), bow_amount=10.0)
                    l_leg = [(arc_x - 15, arc_y + 60), (arc_x - 25, arc_y + 90), (arc_x - 20, arc_y + 115)]
                    r_leg = [(arc_x - 15, arc_y + 60), (arc_x - 5, arc_y + 85), (arc_x + 10, arc_y + 105)]
                    l_arm = [(arc_x, arc_y + 18), (arc_x - 25, arc_y - 10), (arc_x - 35, arc_y - 25)]
                    r_arm = [(arc_x, arc_y + 18), (arc_x + 30, arc_y - 5), (arc_x + 45, arc_y - 20)]
                    tail = bow_curve((arc_x - 12, arc_y), (arc_x - 45, arc_y + 15), bow_amount=-8.0)
                    speed = ((arc_x, arc_y + 30), 90.0) if sub_t < 0.4 else None
                    dust = (cx, ground_y) if sub_t < 0.15 else None
                    frame_img = cls.render_pose(width, height, (arc_x, arc_y), spine, l_arm, r_arm, l_leg, r_leg,
                                                headband_tail=tail, speed_trail=speed, dust_pos=dust)

                elif t < 0.85:
                    # 3. Ground Impact: squash with dust puff and impact sparks
                    sub_t = (t - 0.65) / 0.20
                    land_x = cx + 120
                    squash = (1.0 - sub_t) * 40.0
                    head_y = ground_y - 85.0 + squash
                    pelvis_y = ground_y - 35.0 + squash * 0.7
                    spine = bow_curve((land_x, head_y + 12), (land_x, pelvis_y), bow_amount=15.0)
                    l_leg = [(land_x, pelvis_y), (land_x - 35, ground_y - 10), (land_x - 25, ground_y)]
                    r_leg = [(land_x, pelvis_y), (land_x + 35, ground_y - 10), (land_x + 25, ground_y)]
                    l_arm = [(land_x, head_y + 20), (land_x - 45, ground_y - 20), (land_x - 40, ground_y)]
                    r_arm = [(land_x, head_y + 20), (land_x + 35, ground_y - 30), (land_x + 45, ground_y - 10)]
                    tail = [(land_x - 12, head_y), (land_x - 40, head_y - 15)]
                    dust = (land_x, ground_y)
                    spark = (land_x, ground_y - 5) if sub_t < 0.5 else None
                    frame_img = cls.render_pose(width, height, (land_x, head_y), spine, l_arm, r_arm, l_leg, r_leg,
                                                headband_tail=tail, dust_pos=dust, spark_pos=spark)

                else:
                    # 4. Settle / Stand upright
                    sub_t = (t - 0.85) / 0.15
                    land_x = cx + 120
                    head_y = ground_y - 130.0 + (1.0 - sub_t) * 10.0
                    pelvis_y = ground_y - 65.0
                    spine = [(land_x, head_y + 14), (land_x, pelvis_y)]
                    l_leg = [(land_x, pelvis_y), (land_x - 10, (pelvis_y + ground_y)*0.5), (land_x - 10, ground_y)]
                    r_leg = [(land_x, pelvis_y), (land_x + 10, (pelvis_y + ground_y)*0.5), (land_x + 10, ground_y)]
                    l_arm = [(land_x, head_y + 20), (land_x - 18, head_y + 45), (land_x - 15, head_y + 70)]
                    r_arm = [(land_x, head_y + 20), (land_x + 18, head_y + 45), (land_x + 15, head_y + 70)]
                    tail = [(land_x - 12, head_y), (land_x - 30, head_y + 10)]
                    frame_img = cls.render_pose(width, height, (land_x, head_y), spine, l_arm, r_arm, l_leg, r_leg, headband_tail=tail)

                frames.append(frame_img)

        return frames


# =========================================================================
# 2. ANIME & MANGA RENDERER
# =========================================================================

class AnimeRenderer:
    """Renders authentic anime characters with expressive eyes, layered hair, and cel-shading."""

    SKIN_BASE = (255, 235, 222, 255)
    SKIN_SHADOW = (235, 205, 195, 255)
    HAIR_COLOR = (42, 52, 75, 255)       # Midnight blue
    HAIR_SHADOW = (28, 35, 52, 255)
    HAIR_SHEEN = (110, 135, 185, 220)
    LINE_COLOR = (35, 30, 42, 255)       # Soft warm inking
    EYE_IRIS_TOP = (20, 60, 140, 255)
    EYE_IRIS_BOTTOM = (65, 145, 235, 255)

    @classmethod
    def render_face(cls, width: int, height: int,
                    center: Tuple[float, float], scale: float = 1.0,
                    eye_open: float = 1.0, wind_phase: float = 0.0,
                    smile: float = 0.5) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cx, cy = center
        s = scale

        draw = ImageDraw.Draw(img, "RGBA")

        # 1. Face Silhouette & Jawline (tapered anime chin)
        chin_pt = (cx, cy + 85 * s)
        jaw_l = (cx - 55 * s, cy + 25 * s)
        jaw_r = (cx + 55 * s, cy + 25 * s)
        cheek_l = (cx - 65 * s, cy - 20 * s)
        cheek_r = (cx + 65 * s, cy - 20 * s)
        forehead_t = (cx, cy - 90 * s)

        face_poly = [forehead_t, cheek_l, jaw_l, chin_pt, jaw_r, cheek_r]
        draw.polygon(face_poly, fill=cls.SKIN_BASE)

        # Jawline shadow (cel shading)
        shadow_poly = [(cx - 25 * s, cy + 60 * s), chin_pt, jaw_r, (cx + 10 * s, cy + 45 * s)]
        draw.polygon(shadow_poly, fill=cls.SKIN_SHADOW)

        # Face outline
        draw.line([cheek_l, jaw_l, chin_pt, jaw_r, cheek_r], fill=cls.LINE_COLOR, width=int(2.5 * s))

        # 2. Soft anime cheek blush
        draw_soft_gradient_glow(img, (cx - 40 * s, cy + 28 * s), 15 * s, (245, 120, 130, 90))
        draw_soft_gradient_glow(img, (cx + 40 * s, cy + 28 * s), 15 * s, (245, 120, 130, 90))

        # 3. Expressive Anime Eyes
        eye_y = cy + 10 * s
        for eye_x, is_left in [(cx - 32 * s, True), (cx + 32 * s, False)]:
            ew = 22 * s
            eh = 26 * s * max(0.08, eye_open)

            # Eye socket white
            draw.ellipse([eye_x - ew*0.5, eye_y - eh*0.5, eye_x + ew*0.5, eye_y + eh*0.5], fill=(255, 255, 255, 255))

            if eye_open > 0.25:
                # Iris gradient (top dark, bottom luminous)
                iris_r = ew * 0.45
                draw.ellipse([eye_x - iris_r, eye_y - eh*0.45, eye_x + iris_r, eye_y + eh*0.45], fill=cls.EYE_IRIS_TOP)
                draw.ellipse([eye_x - iris_r*0.85, eye_y, eye_x + iris_r*0.85, eye_y + eh*0.45], fill=cls.EYE_IRIS_BOTTOM)
                # Pupil
                draw.ellipse([eye_x - iris_r*0.35, eye_y - eh*0.15, eye_x + iris_r*0.35, eye_y + eh*0.25], fill=(10, 15, 30, 255))
                # Catchlight specular highlights (classic dual white gleams)
                draw.ellipse([eye_x - iris_r*0.4, eye_y - eh*0.3, eye_x - iris_r*0.1, eye_y - eh*0.1], fill=(255, 255, 255, 255))
                draw.ellipse([eye_x + iris_r*0.15, eye_y + eh*0.1, eye_x + iris_r*0.35, eye_y + eh*0.25], fill=(255, 255, 255, 220))

            # Upper Eyelash (thick anime sweep)
            curv = -4 * s if eye_open > 0.25 else 4 * s
            lash_pts = bow_curve((eye_x - ew*0.6, eye_y - eh*0.5), (eye_x + ew*0.6, eye_y - eh*0.5), bow_amount=curv)
            draw_tapered_stroke(img, lash_pts, cls.LINE_COLOR, base_width=3.5 * s)

        # Eyebrows
        for eb_x, mult in [(cx - 32 * s, -1), (cx + 32 * s, 1)]:
            brow_pts = bow_curve((eb_x - 14 * s, eye_y - 22 * s), (eb_x + 14 * s, eye_y - 20 * s), bow_amount=mult * 2.5 * s)
            draw_tapered_stroke(img, brow_pts, cls.LINE_COLOR, base_width=2.5 * s)

        # Nose (dainty anime point / shadow notch)
        draw.line([(cx, cy + 32 * s), (cx + 2 * s, cy + 36 * s)], fill=cls.LINE_COLOR, width=int(2 * s))

        # Mouth (expressive curve)
        mouth_y = cy + 55 * s
        mouth_w = 14 * s + smile * 8 * s
        mouth_curve = bow_curve((cx - mouth_w * 0.5, mouth_y), (cx + mouth_w * 0.5, mouth_y), bow_amount=smile * 6 * s)
        draw_tapered_stroke(img, mouth_curve, (190, 70, 80, 255), base_width=2.5 * s)

        # 4. Sculptural Anime Hair with Wind Dynamics
        wind_offset = math.sin(wind_phase) * 12.0 * s
        hair_bangs = [
            # Left side fringe
            sample_cubic_bezier((cx - 65 * s, cy - 60 * s), (cx - 75 * s + wind_offset, cy), (cx - 60 * s + wind_offset, cy + 40 * s), (cx - 50 * s, cy + 70 * s)),
            # Center bangs
            sample_cubic_bezier((cx - 20 * s, cy - 70 * s), (cx - 30 * s + wind_offset*0.5, cy - 20 * s), (cx - 15 * s + wind_offset, cy + 15 * s), (cx - 5 * s, cy + 30 * s)),
            sample_cubic_bezier((cx + 10 * s, cy - 70 * s), (cx + 5 * s + wind_offset*0.5, cy - 15 * s), (cx + 20 * s + wind_offset, cy + 15 * s), (cx + 25 * s, cy + 28 * s)),
            # Right side fringe
            sample_cubic_bezier((cx + 65 * s, cy - 60 * s), (cx + 70 * s + wind_offset, cy), (cx + 60 * s + wind_offset, cy + 40 * s), (cx + 50 * s, cy + 65 * s)),
        ]

        # Top hair crown volume
        crown_poly = [
            (cx - 75 * s, cy - 30 * s), (cx - 85 * s, cy - 80 * s),
            (cx - 40 * s + wind_offset*0.3, cy - 120 * s), (cx + 30 * s + wind_offset*0.5, cy - 122 * s),
            (cx + 85 * s, cy - 80 * s), (cx + 75 * s, cy - 30 * s)
        ]
        draw.polygon(crown_poly, fill=cls.HAIR_COLOR)

        # Hair Sheen Highlight Band
        sheen_curve = bow_curve((cx - 65 * s, cy - 75 * s), (cx + 65 * s, cy - 75 * s), bow_amount=-15 * s)
        draw_tapered_stroke(img, sheen_curve, cls.HAIR_SHEEN, base_width=6.0 * s)

        # Bangs drawing
        for bang in hair_bangs:
            draw_tapered_stroke(img, bang, cls.HAIR_COLOR, base_width=10.0 * s)
            draw_tapered_stroke(img, bang, cls.LINE_COLOR, base_width=2.5 * s)

        return img

    @classmethod
    def generate_animation(cls, width: int = 800, height: int = 600,
                           action: str = "blink_and_breeze", frame_count: int = 12) -> List[Image.Image]:
        frames = []
        center = (width * 0.5, height * 0.48)

        for f in range(frame_count):
            t = f / float(max(1, frame_count - 1))
            # Wind phase oscillating
            wind = t * 2.0 * math.pi

            # Natural 3-frame blink at frame 4, 5, 6
            if f in (4, 6):
                eye_open = 0.45
            elif f == 5:
                eye_open = 0.05
            else:
                eye_open = 1.0

            smile = 0.5 + 0.25 * math.sin(t * math.pi)

            frame = cls.render_face(width, height, center=center, scale=1.4,
                                    eye_open=eye_open, wind_phase=wind, smile=smile)
            frames.append(frame)

        return frames


# =========================================================================
# 3. TRADITIONAL PENCIL SKETCH RENDERER
# =========================================================================

class PencilSketchRenderer:
    """Simulates traditional Disney-style hand-drawn rough graphite on animators' paper."""

    PAPER_BG = (252, 250, 245, 255)       # Animation paper
    BLUE_ROUGH = (120, 160, 205, 120)     # Non-photo blue rough underdrawing
    GRAPHITE_KEY = (40, 40, 45, 220)      # Confident graphite stroke

    @classmethod
    def generate_animation(cls, width: int = 800, height: int = 600,
                           action: str = "sketch_bird_flight", frame_count: int = 12) -> List[Image.Image]:
        frames = []
        cx, cy = width * 0.5, height * 0.45

        for f in range(frame_count):
            img = Image.new("RGBA", (width, height), cls.PAPER_BG)
            phase = (f / float(frame_count)) * (2.0 * math.pi)
            wing_angle = math.sin(phase) * 0.75 # Flapping arc

            # 1. Underdrawing pass (light blue gesture lines)
            body_center = (cx - 50 + (f / float(frame_count)) * 100, cy + math.sin(phase) * 25.0)
            bx, by = body_center

            # Rough axis of motion (line of action)
            draw_pencil_sketch_stroke(img, (bx - 70, by + 10), (bx + 70, by - 15), cls.BLUE_ROUGH, passes=4, spread=2.5)

            # 2. Bird Body & Head Gestures (Layered Graphite)
            head_p = (bx + 45, by - 15)
            draw_pencil_sketch_stroke(img, (bx - 35, by), head_p, cls.GRAPHITE_KEY, passes=3, spread=1.0)
            draw_pencil_sketch_stroke(img, head_p, (bx + 65, by - 12), cls.GRAPHITE_KEY, passes=3) # Beak

            # Wings in motion (arcs of flight)
            wing_tip_l = (bx - 10, by - 80 * math.cos(wing_angle) - 20)
            wing_tip_r = (bx - 20, by + 75 * math.cos(wing_angle) + 10)

            # Left wing graphite strokes
            draw_pencil_sketch_stroke(img, (bx - 10, by - 5), wing_tip_l, cls.GRAPHITE_KEY, passes=4, spread=1.2)
            draw_pencil_sketch_stroke(img, wing_tip_l, (bx - 45, by), cls.GRAPHITE_KEY, passes=3, spread=1.0)

            # Right wing (behind)
            draw_pencil_sketch_stroke(img, (bx - 15, by + 5), wing_tip_r, (70, 70, 80, 160), passes=3, spread=1.5)

            # Cross-hatching shade underneath body
            for h in range(-3, 4):
                draw_pencil_sketch_stroke(img, (bx + h * 8 - 15, by + 8), (bx + h * 8 - 5, by + 22), (60, 60, 65, 110), passes=2)

            frames.append(img)

        return frames


# =========================================================================
# 4. STUDIO GHIBLI AESTHETIC RENDERER
# =========================================================================

class GhibliRenderer:
    """Painterly, nostalgic Ghibli-inspired landscapes, puffy clouds, and soft lighting."""

    SKY_TOP = (110, 175, 235, 255)
    SKY_HORIZON = (235, 242, 248, 255)
    HILL_DISTANT = (145, 185, 155, 255)
    HILL_FOREGROUND = (75, 145, 90, 255)
    CLOUD_SHADOW = (215, 215, 235, 230)
    CLOUD_LIT = (255, 255, 252, 255)

    @classmethod
    def render_background(cls, width: int, height: int, cloud_offset: float = 0.0) -> Image.Image:
        bg = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(bg, "RGBA")

        # Vertical Sky Gradient
        for y in range(height):
            t = y / float(height)
            r = int(cls.SKY_TOP[0] * (1.0 - t) + cls.SKY_HORIZON[0] * t)
            g = int(cls.SKY_TOP[1] * (1.0 - t) + cls.SKY_HORIZON[1] * t)
            b = int(cls.SKY_TOP[2] * (1.0 - t) + cls.SKY_HORIZON[2] * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Fluffy Cumulus Ghibli Clouds
        cx = (width * 0.45 + cloud_offset) % (width + 200) - 100
        cy = height * 0.32
        puffs = [
            (cx, cy, 70), (cx - 60, cy + 20, 55), (cx + 60, cy + 15, 55),
            (cx - 100, cy + 35, 45), (cx + 100, cy + 30, 45), (cx, cy + 35, 60)
        ]
        # Cloud base shadow
        for px, py, r in puffs:
            draw.ellipse([px - r, py - r + 8, px + r, py + r + 8], fill=cls.CLOUD_SHADOW)
        # Cloud sunlit highlight
        for px, py, r in puffs:
            draw.ellipse([px - r, py - r, px + r, py + r], fill=cls.CLOUD_LIT)

        # Distant Soft Green Hill
        h_pts_dist = [(0, height * 0.62), (width * 0.5, height * 0.55), (width, height * 0.64), (width, height), (0, height)]
        draw.polygon(h_pts_dist, fill=cls.HILL_DISTANT)

        # Foreground Lush Rolling Hill
        h_pts_fore = [(0, height * 0.76), (width * 0.4, height * 0.68), (width, height * 0.78), (width, height), (0, height)]
        draw.polygon(h_pts_fore, fill=cls.HILL_FOREGROUND)

        return bg

    @classmethod
    def generate_animation(cls, width: int = 800, height: int = 600,
                           action: str = "breeze_scene", frame_count: int = 12) -> List[Image.Image]:
        frames = []
        cx, cy = width * 0.5, height * 0.65

        for f in range(frame_count):
            t = f / float(max(1, frame_count - 1))
            cloud_drift = t * 60.0
            bg = cls.render_background(width, height, cloud_offset=cloud_drift)

            draw = ImageDraw.Draw(bg, "RGBA")
            wind = math.sin(t * 2.0 * math.pi) * 15.0

            # Character standing in the breeze (Ghibli coat and scarf)
            char_x = cx - 30
            char_y = cy - 25

            # Coat silhouette with wind flutter
            coat_poly = [
                (char_x, char_y),
                (char_x - 18, char_y + 65),
                (char_x - 35 + wind, char_y + 85),
                (char_x + 35 + wind, char_y + 85),
                (char_x + 18, char_y + 65),
            ]
            draw.polygon(coat_poly, fill=(185, 80, 75, 255)) # Terracotta red coat

            # Flowing Red Scarf
            scarf_pts = sample_cubic_bezier(
                (char_x + 6, char_y + 8),
                (char_x + 35 + wind * 1.5, char_y + 12),
                (char_x + 65 + wind * 2.0, char_y + 25),
                (char_x + 95 + wind * 2.5, char_y + 18)
            )
            draw_tapered_stroke(bg, scarf_pts, (220, 215, 210, 255), base_width=6.0)

            # Character head & cute hat
            draw.ellipse([char_x - 12, char_y - 25, char_x + 12, char_y - 1], fill=(255, 230, 210, 255))
            # Straw hat brim
            draw.ellipse([char_x - 28 + wind * 0.2, char_y - 26, char_x + 28 + wind * 0.2, char_y - 18], fill=(235, 210, 140, 255), outline=(170, 140, 80, 255))

            # Floating wind leaves / dandelion particles
            for i in range(5):
                p_t = (t + i * 0.2) % 1.0
                leaf_x = width * p_t
                leaf_y = height * 0.55 + math.sin(p_t * 6.0 + i) * 35.0
                draw.ellipse([leaf_x - 3, leaf_y - 2, leaf_x + 3, leaf_y + 2], fill=(245, 220, 120, 220))

            frames.append(bg)

        return frames


# =========================================================================
# 5. HAND-DRAWN DOODLE & CARTOON RENDERER
# =========================================================================

class DoodleRenderer:
    """Whimsical, wobbly hand-drawn cartoon with rubber-hose physics and expressive accents."""

    BG_COLOR = (252, 250, 245, 255)       # Cream sketchbook
    MARKER_COLOR = (24, 24, 30, 255)
    ACCENT_COLOR = (255, 215, 0, 255)     # Cheerful yellow

    @classmethod
    def generate_animation(cls, width: int = 800, height: int = 600,
                           action: str = "bounce_dance", frame_count: int = 12) -> List[Image.Image]:
        frames = []
        cx = width * 0.5
        ground_y = height * 0.75

        for f in range(frame_count):
            img = Image.new("RGBA", (width, height), cls.BG_COLOR)
            t = f / float(frame_count)
            phase = t * 2.0 * math.pi

            # Rubber-hose bouncing body
            bounce_y = -abs(math.sin(phase)) * 70.0
            scale_y = 1.0 - 0.3 * math.sin(phase)
            sx, sy = calculate_squash_stretch(scale_y)

            body_cx = cx + math.cos(phase) * 15.0
            body_cy = ground_y - 90.0 + bounce_y

            bw = 48.0 * sx
            bh = 48.0 * sy

            # Wobbly body outline (marker style)
            body_pts = [
                (body_cx - bw, body_cy),
                (body_cx - bw * 0.7, body_cy - bh),
                (body_cx, body_cy - bh * 1.05),
                (body_cx + bw * 0.7, body_cy - bh),
                (body_cx + bw, body_cy),
                (body_cx + bw * 0.7, body_cy + bh),
                (body_cx, body_cy + bh * 1.05),
                (body_cx - bw * 0.7, body_cy + bh),
                (body_cx - bw, body_cy)
            ]
            draw = ImageDraw.Draw(img, "RGBA")
            draw.polygon(body_pts, fill=cls.ACCENT_COLOR)
            draw_doodle_wobble_line(img, body_pts, color=cls.MARKER_COLOR, width=3, seed=f * 10)

            # Funny Cartoon Eyes (squash with the body)
            for ex in [body_cx - 16 * sx, body_cx + 16 * sx]:
                draw.ellipse([ex - 6, body_cy - 12 * sy, ex + 6, body_cy + 4 * sy], fill=(255, 255, 255, 255), outline=cls.MARKER_COLOR, width=2)
                # Pupils looking happily up
                draw.ellipse([ex - 2, body_cy - 8 * sy, ex + 3, body_cy - 2 * sy], fill=cls.MARKER_COLOR)

            # Silly smile
            smile_pts = bow_curve((body_cx - 12 * sx, body_cy + 10 * sy), (body_cx + 12 * sx, body_cy + 10 * sy), bow_amount=10.0 * sy)
            draw_doodle_wobble_line(img, smile_pts, color=cls.MARKER_COLOR, width=3, seed=f * 12)

            # Cartoon Sweat Drop if bouncing high
            if bounce_y < -40:
                drop_x = body_cx + 36 * sx
                drop_y = body_cy - 28 * sy
                drop_pts = [(drop_x, drop_y - 12), (drop_x + 8, drop_y), (drop_x, drop_y + 6), (drop_x - 8, drop_y), (drop_x, drop_y - 12)]
                draw.polygon(drop_pts, fill=(120, 200, 255, 255), outline=cls.MARKER_COLOR)

            # Ground bounce impact lines
            if bounce_y > -15:
                draw_speed_lines(img, (body_cx, ground_y + 10), direction_deg=90, length=30, count=4, color=(160, 160, 170, 200))

            frames.append(img)

        return frames


# =========================================================================
# Unified Animation Generator Dispatcher
# =========================================================================

STYLE_REGISTRY = {
    "stickman": StickmanRenderer,
    "anime": AnimeRenderer,
    "pencil_sketch": PencilSketchRenderer,
    "sketch": PencilSketchRenderer,
    "ghibli": GhibliRenderer,
    "doodle": DoodleRenderer,
    "cartoon": DoodleRenderer
}


def generate_stylized_animation(style: str = "stickman",
                                action: Optional[str] = None,
                                width: int = 800, height: int = 600,
                                frame_count: int = 12) -> List[Image.Image]:
    """Generate high-quality animation frames matching the requested style."""
    key = (style or "stickman").strip().lower()
    renderer = STYLE_REGISTRY.get(key)
    if not renderer:
        renderer = StickmanRenderer

    if key == "stickman":
        act = action or "jump"
        return renderer.generate_animation(width=width, height=height, action=act, frame_count=frame_count)
    elif key == "anime":
        act = action or "blink_and_breeze"
        return renderer.generate_animation(width=width, height=height, action=act, frame_count=frame_count)
    elif key in ("pencil_sketch", "sketch"):
        act = action or "sketch_bird_flight"
        return renderer.generate_animation(width=width, height=height, action=act, frame_count=frame_count)
    elif key == "ghibli":
        act = action or "breeze_scene"
        return renderer.generate_animation(width=width, height=height, action=act, frame_count=frame_count)
    elif key in ("doodle", "cartoon"):
        act = action or "bounce_dance"
        return renderer.generate_animation(width=width, height=height, action=act, frame_count=frame_count)
    else:
        return StickmanRenderer.generate_animation(width=width, height=height, frame_count=frame_count)
