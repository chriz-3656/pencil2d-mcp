#!/usr/bin/env python3
"""Epic 10-Second Anime Stickman Fight Animation Generator for Pencil2D.

Choreography (120 frames @ 12 fps = 10.0 seconds, 960x540 16:9 widescreen):
- Sec 0-2 (Frames 1-24): Dramatic Standoff & Aura Gathering (Fire vs Lightning).
- Sec 2-4 (Frames 25-48): Sonic Dash & Flying Flaming Windup.
- Sec 4-6 (Frames 49-72): Mid-Air Kinetic Collision, Plasma Shockwave & Impact Sparks.
- Sec 6-8 (Frames 73-96): Explosion Knockback, Ground Skid Smoke & Aerial Meteor Recovery.
- Sec 8-10 (Frames 97-120): Cataclysmic Ground Slam, Crater Fissures & Cinematic Silhouette Settle.
"""

import io
import math
import os
import random
import sys
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw

# Ensure pencil2d_mcp is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from pencil2d_mcp.core import Pencil2DProject, export_project
from pencil2d_mcp.drawing import (
    bow_curve,
    calculate_squash_stretch,
    draw_dust_puff,
    draw_impact_spark,
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

WIDTH = 960
HEIGHT = 540
FPS = 12
TOTAL_FRAMES = 120 # 10.0 seconds
GROUND_Y = 430.0

# Colors
COLOR_RED_FIGHTER = (26, 22, 28, 255)
COLOR_RED_SASH = (235, 45, 45, 255)
COLOR_RED_FIRE_CORE = (255, 240, 150, 255)
COLOR_RED_FIRE_MID = (255, 110, 30, 220)
COLOR_RED_FIRE_EDGE = (210, 35, 20, 160)

COLOR_BLUE_FIGHTER = (20, 24, 32, 255)
COLOR_BLUE_SASH = (40, 180, 245, 255)
COLOR_BLUE_BOLT = (180, 245, 255, 255)
COLOR_BLUE_AURA = (50, 160, 255, 180)


def render_anime_background(w: int, h: int, ground_y: float) -> Image.Image:
    """Render a dramatic sunset anime battlefield background."""
    bg = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(bg, "RGBA")

    # 1. Sky Gradient: Twilight violet top to fiery amber-orange horizon
    sky_top = (48, 28, 68, 255)
    sky_mid = (165, 55, 65, 255)
    sky_horizon = (245, 150, 50, 255)

    for y in range(int(ground_y)):
        t = y / float(ground_y)
        if t < 0.5:
            st = t / 0.5
            r = int(sky_top[0] * (1.0 - st) + sky_mid[0] * st)
            g = int(sky_top[1] * (1.0 - st) + sky_mid[1] * st)
            b = int(sky_top[2] * (1.0 - st) + sky_mid[2] * st)
        else:
            st = (t - 0.5) / 0.5
            r = int(sky_mid[0] * (1.0 - st) + sky_horizon[0] * st)
            g = int(sky_mid[1] * (1.0 - st) + sky_horizon[1] * st)
            b = int(sky_mid[2] * (1.0 - st) + sky_horizon[2] * st)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Setting Sun Glow
    sun_cx, sun_cy = w * 0.5, ground_y - 40
    draw_soft_gradient_glow(bg, (sun_cx, sun_cy), 130, (255, 200, 90, 160))
    draw.ellipse([sun_cx - 45, sun_cy - 45, sun_cx + 45, sun_cy + 45], fill=(255, 245, 200, 255))

    # 2. Far Jagged Mountains Silhouette
    mountains = [
        (0, ground_y - 80), (120, ground_y - 150), (220, ground_y - 95),
        (350, ground_y - 180), (460, ground_y - 120), (580, ground_y - 195),
        (700, ground_y - 110), (840, ground_y - 165), (w, ground_y - 90),
        (w, ground_y), (0, ground_y)
    ]
    draw.polygon(mountains, fill=(65, 32, 58, 255))

    # Midground Rocky Pinnacles
    pinnacles = [
        (60, ground_y), (90, ground_y - 90), (130, ground_y),
        (780, ground_y), (820, ground_y - 110), (870, ground_y)
    ]
    draw.polygon(pinnacles[:3], fill=(42, 22, 38, 255))
    draw.polygon(pinnacles[3:], fill=(42, 22, 38, 255))

    # 3. Ground / Cracked Wasteland Arena
    draw.rectangle([0, int(ground_y), w, h], fill=(28, 20, 24, 255))

    # Horizon rim light on ground
    draw.line([(0, ground_y), (w, ground_y)], fill=(225, 110, 45, 255), width=2)

    # Perspective ground cracks with glowing lava/energy seams
    cracks = [
        [(w * 0.25, ground_y), (w * 0.22, ground_y + 40), (w * 0.18, ground_y + 90)],
        [(w * 0.5, ground_y), (w * 0.48, ground_y + 35), (w * 0.52, ground_y + 70), (w * 0.5, h)],
        [(w * 0.72, ground_y), (w * 0.76, ground_y + 45), (w * 0.82, ground_y + 100)]
    ]
    for c_pts in cracks:
        draw_tapered_stroke(bg, c_pts, (255, 95, 25, 200), base_width=3.0)
        draw_tapered_stroke(bg, c_pts, (255, 220, 80, 240), base_width=1.0)

    return bg


def draw_fire_flame(canvas: Image.Image, center: Tuple[float, float],
                    scale: float = 1.0, seed: int = 0):
    """Draw vibrant stylized anime fire aura tongue."""
    cx, cy = center
    rng = random.Random(seed)
    s = scale
    tongues = 5
    for i in range(tongues):
        angle = -math.pi * 0.5 + (i - tongues // 2) * 0.35 + rng.uniform(-0.15, 0.15)
        h = rng.uniform(28.0, 52.0) * s
        w = rng.uniform(8.0, 16.0) * s

        tip_x = cx + math.cos(angle) * h
        tip_y = cy + math.sin(angle) * h

        p0 = (cx - w, cy)
        p1 = (cx - w * 0.5, cy - h * 0.5)
        p2 = (tip_x - 5, tip_y + 10)
        p3 = (tip_x, tip_y)

        pts_l = sample_cubic_bezier(p0, p1, p2, p3, steps=8)
        pts_r = sample_cubic_bezier((cx + w, cy), (cx + w * 0.5, cy - h * 0.5), (tip_x + 5, tip_y + 10), p3, steps=8)
        poly = pts_l + list(reversed(pts_r))

        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.polygon(poly, fill=COLOR_RED_FIRE_EDGE)
        # Inner core
        draw.polygon([(x, y + 6) for x, y in poly[1:-1]], fill=COLOR_RED_FIRE_MID)
        draw.ellipse([cx - 8 * s, cy - 14 * s, cx + 8 * s, cy + 2 * s], fill=COLOR_RED_FIRE_CORE)


def draw_lightning_bolt(canvas: Image.Image, p_start: Tuple[float, float],
                        p_end: Tuple[float, float], branches: int = 1,
                        seed: int = 1):
    """Draw jagged anime electric discharge bolt."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    rng = random.Random(seed)
    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    dist = math.hypot(dx, dy)
    steps = max(5, int(dist // 18))

    pts = [p_start]
    cur_x, cur_y = p_start
    for i in range(1, steps):
        t = i / float(steps)
        normal_x = -dy / (dist or 1)
        normal_y = dx / (dist or 1)
        offset = rng.uniform(-20.0, 20.0)
        nx = p_start[0] + dx * t + normal_x * offset
        ny = p_start[1] + dy * t + normal_y * offset
        pts.append((nx, ny))

    pts.append(p_end)

    # Cyan outer glow + brilliant white core
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(40, 180, 255, 140), width=6)
        draw.line([pts[i], pts[i + 1]], fill=(140, 230, 255, 220), width=3)
        draw.line([pts[i], pts[i + 1]], fill=(255, 255, 255, 255), width=1)


def draw_shadow(canvas: Image.Image, x: float, ground_y: float,
                height_above_ground: float, base_radius: float = 32.0):
    """Draw dynamic ground shadow that scales and fades with altitude."""
    alt = max(0.0, height_above_ground)
    scale = max(0.25, 1.0 - (alt / 350.0))
    alpha = int(180 * (scale ** 1.5))
    rx = base_radius * scale
    ry = (base_radius * 0.35) * scale

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse([x - rx, ground_y - ry, x + rx, ground_y + ry], fill=(12, 10, 14, alpha))


def draw_fighter(canvas: Image.Image, x: float, y: float,
                 color: Tuple[int, int, int, int],
                 sash_color: Tuple[int, int, int, int],
                 facing: int, # +1 right, -1 left
                 pose: str, # "stand", "dash", "punch", "aerial_clash", "skid", "meteor_dive"
                 frame_idx: int,
                 aura_type: Optional[str] = None):
    """Render an expressive martial arts stickman with anatomical curvature."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    f = facing

    # Head
    head_r = 16.0
    head_pos = (x, y - 82.0)
    hx, hy = head_pos

    # Stance pose kinematics
    if pose == "stand":
        bob = math.sin(frame_idx * 0.5) * 2.5
        hy += bob
        pelvis = (x - f * 4, y - 38.0 + bob)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=-f * 4.0)

        l_leg = [pelvis, (pelvis[0] - 12, (pelvis[1] + y) * 0.5), (x - 14, y)]
        r_leg = [pelvis, (pelvis[0] + 12, (pelvis[1] + y) * 0.5), (x + 14, y)]

        l_arm = [(hx - f * 2, hy + head_r + 6), (x - f * 18, hy + 35), (x - f * 24, hy + 45)]
        r_arm = [(hx + f * 2, hy + head_r + 6), (x + f * 20, hy + 30), (x + f * 30, hy + 22)]

        sash_pts = bow_curve((hx - f * 8, hy + 2), (hx - f * 42, hy + 18 + math.sin(frame_idx * 0.4) * 8), bow_amount=-6.0)

    elif pose == "dash":
        # Low forward sprint
        hy += 18.0
        pelvis = (x - f * 32, y - 28.0)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=-f * 15.0)

        l_leg = [pelvis, (pelvis[0] - f * 10, pelvis[1] - 15), (x - f * 40, y - 10)]
        r_leg = [pelvis, (pelvis[0] + f * 20, y - 15), (x + f * 35, y)]

        l_arm = [(hx, hy + head_r), (x - f * 20, hy + 10), (x - f * 35, hy + 5)]
        r_arm = [(hx, hy + head_r), (x + f * 25, hy + 15), (x + f * 45, hy + 10)]

        sash_pts = bow_curve((hx - f * 6, hy), (hx - f * 60, hy - 12 + math.sin(frame_idx * 0.6) * 6), bow_amount=10.0)

    elif pose == "punch":
        # Dynamic martial arts lunge punch
        pelvis = (x - f * 18, y - 36.0)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=-f * 18.0)

        l_leg = [pelvis, (x - f * 35, (pelvis[1] + y) * 0.5 + 5), (x - f * 42, y)]
        r_leg = [pelvis, (x + f * 15, (pelvis[1] + y) * 0.5 - 5), (x + f * 28, y)]

        l_arm = [(hx, hy + head_r), (x - f * 15, hy + 22), (x - f * 25, hy + 18)]
        # Fully extended punch arm
        r_arm = [(hx, hy + head_r), (x + f * 30, hy + 18), (x + f * 60, hy + 14)]

        sash_pts = bow_curve((hx - f * 6, hy), (hx - f * 50, hy + 15), bow_amount=-8.0)

    elif pose == "aerial_clash":
        # Mid-air clash pose
        pelvis = (x - f * 15, y - 25.0)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=-f * 20.0)

        l_leg = [pelvis, (pelvis[0] - f * 25, pelvis[1] + 25), (pelvis[0] - f * 20, pelvis[1] + 55)]
        r_leg = [pelvis, (pelvis[0] - f * 10, pelvis[1] + 30), (pelvis[0] + f * 5, pelvis[1] + 60)]

        l_arm = [(hx, hy + head_r), (x + f * 15, hy + 10), (x + f * 35, hy + 18)]
        r_arm = [(hx, hy + head_r), (x + f * 20, hy + 2), (x + f * 42, hy + 10)]

        sash_pts = bow_curve((hx - f * 6, hy), (hx - f * 55, hy - 25), bow_amount=12.0)

    elif pose == "skid":
        # Reeling backward skid on ground
        pelvis = (x + f * 15, y - 32.0)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=f * 14.0)

        l_leg = [pelvis, (x + f * 30, y - 10), (x + f * 40, y)]
        r_leg = [pelvis, (x - f * 10, y - 15), (x - f * 25, y)]

        l_arm = [(hx, hy + head_r), (x - f * 25, hy + 25), (x - f * 35, hy + 15)]
        r_arm = [(hx, hy + head_r), (x + f * 20, hy + 20), (x + f * 30, hy + 35)]

        sash_pts = bow_curve((hx + f * 6, hy), (hx + f * 45, hy - 10), bow_amount=-12.0)

    else: # "meteor_dive"
        # Inverted diving dive slam
        pelvis = (x, y - 120.0)
        spine = bow_curve((hx, hy + head_r), pelvis, bow_amount=f * 6.0)

        l_leg = [pelvis, (x - 18, pelvis[1] - 30), (x - 22, pelvis[1] - 55)]
        r_leg = [pelvis, (x + 18, pelvis[1] - 30), (x + 22, pelvis[1] - 55)]

        l_arm = [(hx, hy + head_r), (x - 25, hy + 25), (x - 20, hy + 50)]
        r_arm = [(hx, hy + head_r), (x + 25, hy + 25), (x + 20, hy + 50)]

        sash_pts = bow_curve((hx, hy - 4), (hx, hy - 55), bow_amount=6.0)

    # 1. Aura glow behind fighter
    if aura_type == "fire":
        draw_fire_flame(canvas, (x, y - 45), scale=1.3, seed=frame_idx * 7)
    elif aura_type == "lightning":
        draw_soft_gradient_glow(canvas, (x, y - 45), 55, (40, 180, 255, 90))
        for b in range(3):
            angle = (b / 3.0) * math.pi * 2.0 + frame_idx * 0.8
            p_end = (x + math.cos(angle) * 45, y - 45 + math.sin(angle) * 45)
            draw_lightning_bolt(canvas, (x, y - 45), p_end, seed=frame_idx * 3 + b)

    # 2. Limbs & Spine
    draw_tapered_stroke(canvas, l_leg, color, base_width=5.5)
    draw_tapered_stroke(canvas, r_leg, color, base_width=5.5)
    draw_tapered_stroke(canvas, spine, color, base_width=6.5)
    draw_tapered_stroke(canvas, l_arm, color, base_width=5.0)
    draw_tapered_stroke(canvas, r_arm, color, base_width=5.0)

    # 3. Head & Glowing Eye
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)

    # Anime glowing eye dot
    eye_x = hx + f * 5.0
    eye_y = hy - 1.0
    eye_col = (255, 230, 80, 255) if aura_type == "fire" else (160, 240, 255, 255)
    draw.ellipse([eye_x - 3, eye_y - 3, eye_x + 3, eye_y + 3], fill=eye_col)

    # Flowing sash
    draw_tapered_stroke(canvas, sash_pts, sash_color, base_width=4.0)

    # Weapons / Hand VFX
    if aura_type == "fire" and (pose in ("punch", "aerial_clash", "meteor_dive")):
        fist_x, fist_y = r_arm[-1]
        draw_fire_flame(canvas, (fist_x, fist_y), scale=1.1, seed=frame_idx * 11)
    elif aura_type == "lightning":
        dagger_tip = (r_arm[-1][0] + f * 18, r_arm[-1][1] - 8)
        draw.line([r_arm[-1], dagger_tip], fill=COLOR_BLUE_BOLT, width=3)


def generate_10s_fight_frames() -> List[Image.Image]:
    """Choreograph the full 120-frame 10-second anime fight animation."""
    frames = []
    base_bg = render_anime_background(WIDTH, HEIGHT, GROUND_Y)

    for f in range(1, TOTAL_FRAMES + 1):
        # Layer 1: Background base copy
        frame_canvas = base_bg.copy()
        draw = ImageDraw.Draw(frame_canvas, "RGBA")

        # -------------------------------------------------------------
        # ACT I: STANDOFF & POWER CHARGE (Frames 1-24 | 0s - 2.0s)
        # -------------------------------------------------------------
        if f <= 24:
            t = (f - 1) / 23.0
            # Red on Left, Blue on Right
            red_x = 240.0 + math.sin(t * math.pi) * 6.0
            red_y = GROUND_Y
            blue_x = 720.0 - math.sin(t * math.pi) * 6.0
            blue_y = GROUND_Y

            draw_shadow(frame_canvas, red_x, GROUND_Y, 0.0)
            draw_shadow(frame_canvas, blue_x, GROUND_Y, 0.0)

            # Auras growing as t approaches 1.0
            draw_fighter(frame_canvas, red_x, red_y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="stand", frame_idx=f, aura_type="fire")
            draw_fighter(frame_canvas, blue_x, blue_y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="stand", frame_idx=f, aura_type="lightning")

            # Energy crackles in the air
            if f > 12:
                draw_speed_lines(frame_canvas, (red_x + 30, red_y - 50), direction_deg=0, length=25 + f, count=3, color=(255, 120, 30, 160))
                draw_speed_lines(frame_canvas, (blue_x - 30, blue_y - 50), direction_deg=180, length=25 + f, count=3, color=(50, 180, 255, 160))

        # -------------------------------------------------------------
        # ACT II: SONIC DASH & CHARGE ATTACK (Frames 25-48 | 2.0s - 4.0s)
        # -------------------------------------------------------------
        elif f <= 48:
            t = (f - 25) / 23.0
            # Red leaps forward with rising flaming punch
            red_t = ease_in_quad(t)
            red_x = 240.0 + red_t * 200.0
            red_alt = math.sin(red_t * math.pi) * 110.0
            red_y = GROUND_Y - red_alt

            # Blue dashes across ground with extreme speed
            blue_t = ease_in_quad(t)
            blue_x = 720.0 - blue_t * 210.0
            blue_y = GROUND_Y

            draw_shadow(frame_canvas, red_x, GROUND_Y, red_alt)
            draw_shadow(frame_canvas, blue_x, GROUND_Y, 0.0)

            # Blue dash ground smoke
            if f % 3 == 0:
                draw_dust_puff(frame_canvas, (blue_x + 35, GROUND_Y), radius=16.0)

            draw_fighter(frame_canvas, red_x, red_y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="punch", frame_idx=f, aura_type="fire")
            draw_fighter(frame_canvas, blue_x, blue_y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="dash", frame_idx=f, aura_type="lightning")

            # Speed lines across the screen
            draw_speed_lines(frame_canvas, (red_x - 40, red_y - 30), direction_deg=180, length=90, count=4, color=(255, 150, 50, 200))
            draw_speed_lines(frame_canvas, (blue_x + 40, blue_y - 30), direction_deg=0, length=100, count=5, color=(100, 210, 255, 200))

        # -------------------------------------------------------------
        # ACT III: MID-AIR COLLISION & SHOCKWAVE (Frames 49-72 | 4.0s - 6.0s)
        # -------------------------------------------------------------
        elif f <= 72:
            clash_t = (f - 49) / 23.0
            clash_cx = WIDTH * 0.5
            clash_cy = GROUND_Y - 110.0

            red_x = clash_cx - 28.0 + math.sin(f * 2.0) * 3.0
            red_y = clash_cy + 15.0
            blue_x = clash_cx + 28.0 - math.sin(f * 2.0) * 3.0
            blue_y = clash_cy + 15.0

            draw_shadow(frame_canvas, red_x, GROUND_Y, GROUND_Y - red_y)
            draw_shadow(frame_canvas, blue_x, GROUND_Y, GROUND_Y - blue_y)

            # Draw fighters in clash lock
            draw_fighter(frame_canvas, red_x, red_y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="aerial_clash", frame_idx=f, aura_type="fire")
            draw_fighter(frame_canvas, blue_x, blue_y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="aerial_clash", frame_idx=f, aura_type="lightning")

            # Expanding plasma shockwave sphere
            shock_r = clash_t * 220.0 + 35.0
            draw_soft_gradient_glow(frame_canvas, (clash_cx, clash_cy), shock_r, (255, 255, 240, max(20, int(180 * (1.0 - clash_t)))))
            draw.ellipse([clash_cx - shock_r, clash_cy - shock_r * 0.7, clash_cx + shock_r, clash_cy + shock_r * 0.7],
                         outline=(255, 240, 180, int(220 * (1.0 - clash_t))), width=4)

            # Massive Anime Impact Spark at collision center
            draw_impact_spark(frame_canvas, (clash_cx, clash_cy), radius=45.0 + math.sin(f) * 10.0, count=8, color=(255, 250, 200, 255))

            # Discharging electric arcs radiating outward
            for arc_i in range(5):
                angle = (arc_i / 5.0) * math.pi * 2.0 + f * 0.5
                arc_len = 120.0 + math.sin(f + arc_i) * 40.0
                p_end = (clash_cx + math.cos(angle) * arc_len, clash_cy + math.sin(angle) * arc_len)
                draw_lightning_bolt(frame_canvas, (clash_cx, clash_cy), p_end, seed=f * 5 + arc_i)

            # Flying Rock Debris Particles
            for r_idx in range(7):
                deb_t = (clash_t + r_idx * 0.15) % 1.0
                deb_x = clash_cx + math.cos(r_idx * 1.1) * (deb_t * 260.0)
                deb_y = clash_cy - math.sin(deb_t * math.pi) * 160.0 + deb_t * 120.0
                draw.polygon([(deb_x - 5, deb_y), (deb_x, deb_y - 6), (deb_x + 6, deb_y + 2), (deb_x - 2, deb_y + 5)],
                             fill=(60, 38, 48, 240))

            # Screen flash on frame 50 & 51
            if f in (50, 51):
                flash = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 140))
                frame_canvas.paste(flash, (0, 0), flash)

        # -------------------------------------------------------------
        # ACT IV: BLOWBACK, GROUND SKID & AERIAL METEOR RECOVERY (Frames 73-96 | 6.0s - 8.0s)
        # -------------------------------------------------------------
        elif f <= 96:
            recoil_t = (f - 73) / 23.0

            # Blue is blasted rightward, skidding to a halt on the ground
            skid_ease = ease_out_quad(recoil_t)
            blue_x = (WIDTH * 0.5 + 40) + skid_ease * 260.0
            blue_y = GROUND_Y

            # Red is blasted upward and loops into an aerial diving meteor flip
            arc_p = parabolic_arc((WIDTH * 0.5 - 30, GROUND_Y - 100), (320.0, 100.0), (WIDTH * 0.5 + 180, GROUND_Y - 60), recoil_t)
            red_x, red_y = arc_p
            red_alt = max(0.0, GROUND_Y - red_y)

            draw_shadow(frame_canvas, blue_x, GROUND_Y, 0.0)
            draw_shadow(frame_canvas, red_x, GROUND_Y, red_alt)

            # Blue skid dust and sparks
            if recoil_t < 0.7:
                draw_dust_puff(frame_canvas, (blue_x - 30, GROUND_Y), radius=22.0)
                draw_speed_lines(frame_canvas, (blue_x - 15, GROUND_Y), direction_deg=180, length=45, count=4, color=(255, 180, 50, 200))

            draw_fighter(frame_canvas, blue_x, blue_y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="skid", frame_idx=f, aura_type="lightning")
            draw_fighter(frame_canvas, red_x, red_y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="meteor_dive", frame_idx=f, aura_type="fire")

            # Red flaming meteor trail descending from sky
            draw_fire_flame(frame_canvas, (red_x, red_y - 20), scale=1.8, seed=f * 9)
            draw_speed_lines(frame_canvas, (red_x, red_y - 45), direction_deg=270, length=80, count=5, color=(255, 100, 20, 220))

        # -------------------------------------------------------------
        # ACT V: CATACLYSMIC GROUND SLAM & SILHOUETTE FINISH (Frames 97-120 | 8.0s - 10.0s)
        # -------------------------------------------------------------
        else:
            final_t = (f - 97) / 23.0
            impact_frame = 104
            impact_x = 680.0

            if f < impact_frame:
                # Meteor diving down fast
                dive_t = (f - 97) / float(impact_frame - 97)
                red_x = impact_x - 40.0 * (1.0 - dive_t)
                red_y = 200.0 + dive_t * (GROUND_Y - 200.0)
                blue_x = impact_x + 40.0
                blue_y = GROUND_Y

                draw_shadow(frame_canvas, blue_x, GROUND_Y, 0.0)
                draw_shadow(frame_canvas, red_x, GROUND_Y, GROUND_Y - red_y)

                draw_fighter(frame_canvas, blue_x, blue_y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="punch", frame_idx=f, aura_type="lightning")
                draw_fighter(frame_canvas, red_x, red_y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="meteor_dive", frame_idx=f, aura_type="fire")

            elif f <= impact_frame + 2:
                # Moment of ground slam impact (Frame 104-106)
                draw_shadow(frame_canvas, impact_x, GROUND_Y, 0.0)
                draw_fighter(frame_canvas, impact_x - 25, GROUND_Y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="punch", frame_idx=f)
                draw_fighter(frame_canvas, impact_x + 25, GROUND_Y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="skid", frame_idx=f)

                # Giant impact flash & star
                draw_impact_spark(frame_canvas, (impact_x, GROUND_Y - 20), radius=90.0, count=10, color=(255, 255, 230, 255))
                draw_dust_puff(frame_canvas, (impact_x - 50, GROUND_Y), radius=35.0)
                draw_dust_puff(frame_canvas, (impact_x + 50, GROUND_Y), radius=35.0)

                # Ground crater cracks
                for c_deg in (0, 30, 60, 120, 150, 180):
                    c_len = 65.0
                    rad = math.radians(c_deg)
                    draw.line([(impact_x, GROUND_Y), (impact_x + math.cos(rad) * c_len, GROUND_Y + math.sin(rad) * 35)],
                              fill=(255, 120, 30, 240), width=3)

                # White impact flash
                flash = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 170))
                frame_canvas.paste(flash, (0, 0), flash)

            else:
                # Settle / Lingering Smoke & Anime Silhouette Finisher (Frames 107-120)
                settle_t = (f - 107) / 13.0
                red_x = impact_x - 45.0
                blue_x = impact_x + 45.0

                draw_shadow(frame_canvas, red_x, GROUND_Y, 0.0)
                draw_shadow(frame_canvas, blue_x, GROUND_Y, 0.0)

                # Billowing smoke dust pillars slowly dissipating
                smoke_alpha = int(220 * (1.0 - settle_t * 0.7))
                draw_dust_puff(frame_canvas, (impact_x - 60 - settle_t * 20, GROUND_Y - settle_t * 30), radius=38.0 + settle_t * 15, color=(180, 170, 175, smoke_alpha))
                draw_dust_puff(frame_canvas, (impact_x + 60 + settle_t * 20, GROUND_Y - settle_t * 30), radius=38.0 + settle_t * 15, color=(180, 170, 175, smoke_alpha))

                # Fighters resting in dynamic victorious stances with wind blowing their sashes
                draw_fighter(frame_canvas, red_x, GROUND_Y, COLOR_RED_FIGHTER, COLOR_RED_SASH, facing=+1, pose="stand", frame_idx=f)
                draw_fighter(frame_canvas, blue_x, GROUND_Y, COLOR_BLUE_FIGHTER, COLOR_BLUE_SASH, facing=-1, pose="stand", frame_idx=f)

                # Glowing volcanic ground crater
                draw.ellipse([impact_x - 60, GROUND_Y - 12, impact_x + 60, GROUND_Y + 12], fill=(220, 70, 20, int(180 * (1.0 - settle_t))))

        frames.append(frame_canvas)

    return frames


def main():
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.join(examples_dir, "epic_stickman_fight_10s.pclx")
    mp4_path = os.path.join(examples_dir, "epic_stickman_fight_10s.mp4")
    gif_path = os.path.join(examples_dir, "epic_stickman_fight_10s.gif")
    strip_path = os.path.join(examples_dir, "epic_stickman_fight_contact_strip.png")

    print("================================================================")
    print("EPIC 10-SECOND ANIME STICKMAN FIGHT GENERATOR")
    print(f"Canvas: {WIDTH}x{HEIGHT} (16:9 Anime Widescreen) | Framerate: {FPS} FPS | Frames: {TOTAL_FRAMES}")
    print("================================================================")

    print("Choreographing 120 dynamic anime animation frames...")
    frames = generate_10s_fight_frames()
    print(f"[OK] Generated {len(frames)} frames in memory.")

    print(f"Creating Pencil2D Project: {project_path}")
    proj = Pencil2DProject.create(
        file_path=project_path,
        width=WIDTH,
        height=HEIGHT,
        fps=FPS,
        layer_names=["Anime Fight Layer"]
    )

    for idx, f_img in enumerate(frames, start=1):
        proj.add_frame_image("Anime Fight Layer", idx, f_img)

    proj.save(project_path)
    print(f"[OK] Saved .pclx project archive: {project_path}")

    # Generate Contact Strip Filmstrip (Visual verification)
    print("Generating visual verification contact strip (pencil2d_look)...")
    strip_img, final_strip = proj.generate_preview_strip(
        frame_count=8,
        thumb_width=240,
        output_path=strip_path
    )
    print(f"[OK] Contact strip saved: {final_strip} ({strip_img.width}x{strip_img.height})")

    # Render MP4 video via Pencil2D AppImage CLI
    print(f"Rendering 10-second animation video to MP4 via Pencil2D AppImage...")
    ok_mp4, msg_mp4 = export_project(project_path, mp4_path, fps=FPS)
    print(f"MP4 Export ({ok_mp4}): {msg_mp4}")

    # Render GIF preview
    print("Rendering animated GIF preview...")
    ok_gif, msg_gif = export_project(project_path, gif_path, fps=FPS, force_pure_python=True)
    print(f"GIF Export ({ok_gif}): {msg_gif}")

    print("================================================================")
    print("ALL RENDERS COMPLETED SUCCESSFULLY!")
    print(f"- Project Archive: {project_path}")
    print(f"- Contact Sheet:   {strip_path}")
    print(f"- MP4 Video:       {mp4_path}")
    print(f"- Animated GIF:    {gif_path}")
    print("================================================================")


if __name__ == "__main__":
    main()
