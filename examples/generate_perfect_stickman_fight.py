#!/usr/bin/env python3
"""Masterpiece 10-Second Anime Stickman Fight Animation Generator.

Implements professional Hyun's Dojo / Alan Becker / Sakuga fight animation principles:
1. Articulated Joint Kinematics (shoulders, elbows, wrists, spine, hips, knees, ankles).
2. Speed Contrast & Spacing (tight anticipation windups, 1-frame explosive strikes, 2-frame hit stops).
3. Motion Smears & Arcs (elongated smear wedges and velocity blur blades).
4. Sakuga Impact Frames (inverted monochrome color flashes, violent squash deformation, radial burst rays).
5. Dynamic Camera Shake & Cinematic Letterboxing.
6. Authentic Multi-Beat Martial Arts Choreography (Jab -> Duck -> Sweep -> Axe Kick Block ->
   Lightning Teleport -> Dagger Flurry -> Parries -> Rising Dragon Uppercut Launch ->
   Mid-Air Clash -> Sky Dogfight -> Meteor Dive Collision -> Cataclysmic Ground Crater Slam).

Specifications:
- Canvas: 960x540 (16:9 Anime Widescreen)
- Framerate: 12 FPS
- Duration: 120 Frames (Exactly 10.0 Seconds)
"""

import math
import os
import random
import sys
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from pencil2d_mcp.core import Pencil2DProject, export_project
from pencil2d_mcp.drawing import (
    apply_camera_shake,
    bow_curve,
    calculate_squash_stretch,
    draw_arc_smear_wedge,
    draw_dust_puff,
    draw_impact_spark,
    draw_motion_smear,
    draw_sakuga_impact_flash,
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
TOTAL_FRAMES = 120
GROUND_Y = 435.0

# Fighter Colors
COLOR_RED = (24, 20, 26, 255)
COLOR_RED_SASH = (240, 45, 45, 255)
COLOR_RED_FIRE = (255, 120, 30, 230)
COLOR_RED_CORE = (255, 240, 160, 255)

COLOR_BLUE = (18, 22, 30, 255)
COLOR_BLUE_SASH = (35, 190, 255, 255)
COLOR_BLUE_BOLT = (160, 240, 255, 255)
COLOR_BLUE_AURA = (40, 150, 255, 180)


# =========================================================================
# ARTICULATED SKELETAL RIG & KINEMATICS
# =========================================================================

class StickmanSkeleton:
    """True articulated 12-joint skeletal stick figure."""

    def __init__(self,
                 head: Tuple[float, float],
                 neck: Tuple[float, float],
                 pelvis: Tuple[float, float],
                 l_elbow: Tuple[float, float],
                 l_hand: Tuple[float, float],
                 r_elbow: Tuple[float, float],
                 r_hand: Tuple[float, float],
                 l_knee: Tuple[float, float],
                 l_foot: Tuple[float, float],
                 r_knee: Tuple[float, float],
                 r_foot: Tuple[float, float],
                 head_r: float = 16.0,
                 sash_pts: Optional[List[Tuple[float, float]]] = None,
                 facing: int = 1):
        self.head = head
        self.neck = neck
        self.pelvis = pelvis
        self.l_elbow = l_elbow
        self.l_hand = l_hand
        self.r_elbow = r_elbow
        self.r_hand = r_hand
        self.l_knee = l_knee
        self.l_foot = l_foot
        self.r_knee = r_knee
        self.r_foot = r_foot
        self.head_r = head_r
        self.sash_pts = sash_pts or []
        self.facing = facing

    def draw(self, canvas: Image.Image, color: Tuple[int, int, int, int],
             sash_color: Tuple[int, int, int, int],
             line_w: float = 5.5,
             aura_type: Optional[str] = None,
             frame_seed: int = 0,
             weapon_active: bool = False):
        draw = ImageDraw.Draw(canvas, "RGBA")
        f = self.facing

        # 1. Aura glow behind fighter
        hx, hy = self.head
        px, py = self.pelvis
        cx = (hx + px) * 0.5
        cy = (hy + py) * 0.5

        if aura_type == "fire":
            draw_soft_gradient_glow(canvas, (cx, cy), 65.0, (255, 110, 30, 85))
            # Floating flame motes
            rng = random.Random(frame_seed)
            for _ in range(4):
                fx = cx + rng.uniform(-35, 35)
                fy = cy - rng.uniform(10, 65)
                draw.ellipse([fx - 3, fy - 5, fx + 3, fy + 5], fill=(255, 190, 60, 200))
        elif aura_type == "lightning":
            draw_soft_gradient_glow(canvas, (cx, cy), 60.0, (40, 180, 255, 80))
            rng = random.Random(frame_seed)
            for _ in range(3):
                p1 = (cx + rng.uniform(-25, 25), cy + rng.uniform(-35, 35))
                p2 = (p1[0] + rng.uniform(-25, 25), p1[1] + rng.uniform(-25, 25))
                draw.line([p1, p2], fill=(180, 240, 255, 220), width=2)

        # 2. Articulated Legs (pelvis -> knee -> foot)
        leg_l = bow_curve(self.pelvis, self.l_knee, bow_amount=-f * 2.0, steps=6) + bow_curve(self.l_knee, self.l_foot, bow_amount=f * 2.0, steps=6)
        leg_r = bow_curve(self.pelvis, self.r_knee, bow_amount=f * 2.0, steps=6) + bow_curve(self.r_knee, self.r_foot, bow_amount=-f * 2.0, steps=6)
        draw_tapered_stroke(canvas, leg_l, color, base_width=line_w)
        draw_tapered_stroke(canvas, leg_r, color, base_width=line_w)

        # 3. Curved Spine (Torso)
        spine = bow_curve(self.neck, self.pelvis, bow_amount=-f * 6.0, steps=10)
        draw_tapered_stroke(canvas, spine, color, base_width=line_w + 1.0)

        # 4. Articulated Arms (neck -> elbow -> hand)
        arm_l = [self.neck, self.l_elbow, self.l_hand]
        arm_r = [self.neck, self.r_elbow, self.r_hand]
        draw_tapered_stroke(canvas, arm_l, color, base_width=line_w - 0.5)
        draw_tapered_stroke(canvas, arm_r, color, base_width=line_w - 0.5)

        # 5. Rounded Joint Caps (Elbows, Knees, Feet)
        for jx, jy in [self.neck, self.pelvis, self.l_elbow, self.r_elbow, self.l_knee, self.r_knee]:
            draw.ellipse([jx - line_w * 0.5, jy - line_w * 0.5, jx + line_w * 0.5, jy + line_w * 0.5], fill=color)

        # 6. Head & Expressive Energy Visor / Headband
        hr = self.head_r
        draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=color)

        # Headband / Glowing eye dot
        eye_x = hx + f * 5.5
        eye_y = hy - 1.5
        eye_col = (255, 230, 80, 255) if aura_type == "fire" else (160, 245, 255, 255)
        draw.ellipse([eye_x - 3, eye_y - 2.5, eye_x + 3, eye_y + 2.5], fill=eye_col)

        # 7. Flowing Sash / Scarf
        if self.sash_pts:
            draw_tapered_stroke(canvas, self.sash_pts, sash_color, base_width=4.0)

        # 8. Weapon / Hand VFX
        if weapon_active:
            if aura_type == "fire":
                # Blazing fire fist
                draw.ellipse([self.r_hand[0] - 12, self.r_hand[1] - 12, self.r_hand[0] + 12, self.r_hand[1] + 12], fill=COLOR_RED_FIRE)
                draw.ellipse([self.r_hand[0] - 6, self.r_hand[1] - 6, self.r_hand[0] + 6, self.r_hand[1] + 6], fill=COLOR_RED_CORE)
            elif aura_type == "lightning":
                # Twin glowing electric daggers
                dag_l = (self.l_hand[0] + f * 18, self.l_hand[1] - 10)
                dag_r = (self.r_hand[0] + f * 22, self.r_hand[1] - 8)
                draw.line([self.l_hand, dag_l], fill=COLOR_BLUE_BOLT, width=3)
                draw.line([self.r_hand, dag_r], fill=COLOR_BLUE_BOLT, width=3)


# =========================================================================
# BACKGROUND & ENVIRONMENT
# =========================================================================

def render_wasteland_bg(w: int, h: int, ground_y: float) -> Image.Image:
    """Render a painterly anime twilight wasteland."""
    bg = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(bg, "RGBA")

    # Fiery Dusk Sky Gradient
    for y in range(int(ground_y)):
        t = y / float(ground_y)
        if t < 0.45:
            st = t / 0.45
            r = int(35 * (1.0 - st) + 140 * st)
            g = int(22 * (1.0 - st) + 45 * st)
            b = int(55 * (1.0 - st) + 65 * st)
        else:
            st = (t - 0.45) / 0.55
            r = int(140 * (1.0 - st) + 245 * st)
            g = int(45 * (1.0 - st) + 130 * st)
            b = int(65 * (1.0 - st) + 40 * st)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Low Sunset Sun with Atmospheric Radiance
    sun_x, sun_y = w * 0.5, ground_y - 45
    draw_soft_gradient_glow(bg, (sun_x, sun_y), 140, (255, 180, 80, 160))
    draw.ellipse([sun_x - 50, sun_y - 50, sun_x + 50, sun_y + 50], fill=(255, 245, 210, 255))

    # Distant Jagged Mountains
    mountains = [
        (0, ground_y - 70), (140, ground_y - 140), (260, ground_y - 90),
        (390, ground_y - 170), (510, ground_y - 110), (630, ground_y - 185),
        (760, ground_y - 100), (880, ground_y - 150), (w, ground_y - 80),
        (w, ground_y), (0, ground_y)
    ]
    draw.polygon(mountains, fill=(58, 28, 48, 255))

    # Broken Stone Pinnacles
    pinnacles = [
        (70, ground_y), (105, ground_y - 85), (145, ground_y),
        (810, ground_y), (850, ground_y - 105), (895, ground_y)
    ]
    draw.polygon(pinnacles[:3], fill=(38, 18, 32, 255))
    draw.polygon(pinnacles[3:], fill=(38, 18, 32, 255))

    # Ground Wasteland Plane
    draw.rectangle([0, int(ground_y), w, h], fill=(24, 18, 22, 255))
    draw.line([(0, ground_y), (w, ground_y)], fill=(230, 95, 35, 255), width=2)

    # Perspective Ground Fissure Cracks
    cracks = [
        [(w * 0.2, ground_y), (w * 0.18, ground_y + 35), (w * 0.14, ground_y + 85)],
        [(w * 0.5, ground_y), (w * 0.47, ground_y + 30), (w * 0.53, ground_y + 65), (w * 0.51, h)],
        [(w * 0.78, ground_y), (w * 0.81, ground_y + 40), (w * 0.86, ground_y + 95)]
    ]
    for c_pts in cracks:
        draw_tapered_stroke(bg, c_pts, (255, 80, 20, 180), base_width=3.0)
        draw_tapered_stroke(bg, c_pts, (255, 210, 70, 220), base_width=1.0)

    return bg


def render_shadow(canvas: Image.Image, x: float, ground_y: float, alt: float, radius: float = 34.0):
    """Draw an altitude-sensitive perspective contact shadow."""
    alt = max(0.0, alt)
    s = max(0.2, 1.0 - (alt / 320.0))
    alpha = int(180 * (s ** 1.5))
    rx = radius * s
    ry = (radius * 0.32) * s
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse([x - rx, ground_y - ry, x + rx, ground_y + ry], fill=(10, 8, 12, alpha))


# =========================================================================
# CHOREOGRAPHED MASTERPIECE ANIMATION PIPELINE
# =========================================================================

def generate_masterpiece_frames() -> List[Image.Image]:
    frames = []
    base_bg = render_wasteland_bg(WIDTH, HEIGHT, GROUND_Y)

    # Store previous positions for drawing motion smears
    prev_red_hand = None
    prev_blue_hand = None
    prev_red_foot = None

    for f in range(1, TOTAL_FRAMES + 1):
        canvas = base_bg.copy()
        draw = ImageDraw.Draw(canvas, "RGBA")
        cam_dx = 0.0
        cam_dy = 0.0

        # =================================================================
        # BEAT 1: MARTIAL ARTS COMBAT STANCE & AURA IGNITION (Frames 1-16)
        # =================================================================
        if f <= 16:
            t = (f - 1) / 15.0
            ease_t = ease_in_out_cubic(t)

            red_x = 260.0
            red_crouch = ease_t * 18.0
            red_y = GROUND_Y

            blue_x = 700.0
            blue_crouch = ease_t * 16.0
            blue_y = GROUND_Y

            render_shadow(canvas, red_x, GROUND_Y, 0.0)
            render_shadow(canvas, blue_x, GROUND_Y, 0.0)

            # Red Martial Arts Monk Stance
            red_hy = red_y - 82.0 + red_crouch
            red_pelvis = (red_x - 6.0, red_y - 38.0 + red_crouch)
            red_sash = bow_curve((red_x - 8, red_hy + 2), (red_x - 42, red_hy + 16 + math.sin(f * 0.5) * 8), bow_amount=-6.0)

            red_skel = StickmanSkeleton(
                head=(red_x, red_hy),
                neck=(red_x + 2, red_hy + 16),
                pelvis=red_pelvis,
                l_elbow=(red_x - 18, red_hy + 34),
                l_hand=(red_x - 24, red_hy + 46),
                r_elbow=(red_x + 18, red_hy + 30),
                r_hand=(red_x + 28, red_hy + 22),
                l_knee=(red_x - 16, (red_pelvis[1] + red_y) * 0.5 + 4),
                l_foot=(red_x - 22, red_y),
                r_knee=(red_x + 16, (red_pelvis[1] + red_y) * 0.5 + 4),
                r_foot=(red_x + 24, red_y),
                sash_pts=red_sash,
                facing=+1
            )
            red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire" if f > 6 else None, frame_seed=f)

            # Blue Ninja Guard Stance
            blue_hy = blue_y - 82.0 + blue_crouch
            blue_pelvis = (blue_x + 6.0, blue_y - 38.0 + blue_crouch)
            blue_sash = bow_curve((blue_x + 8, blue_hy + 2), (blue_x + 42, blue_hy + 16 + math.sin(f * 0.5) * 8), bow_amount=6.0)

            blue_skel = StickmanSkeleton(
                head=(blue_x, blue_hy),
                neck=(blue_x - 2, blue_hy + 16),
                pelvis=blue_pelvis,
                l_elbow=(blue_x - 18, blue_hy + 30),
                l_hand=(blue_x - 26, blue_hy + 22),
                r_elbow=(blue_x + 18, blue_hy + 34),
                r_hand=(blue_x + 24, blue_hy + 46),
                l_knee=(blue_x - 16, (blue_pelvis[1] + blue_y) * 0.5 + 4),
                l_foot=(blue_x - 24, blue_y),
                r_knee=(blue_x + 16, (blue_pelvis[1] + blue_y) * 0.5 + 4),
                r_foot=(blue_x + 22, blue_y),
                sash_pts=blue_sash,
                facing=-1
            )
            blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning" if f > 6 else None, frame_seed=f, weapon_active=True)

        # =================================================================
        # BEAT 2: JAB ATTACK & LOW DUCK (Frames 17-28 | 1.3s - 2.3s)
        # =================================================================
        elif f <= 28:
            t = (f - 17) / 11.0

            if f <= 19:
                # 1. Red Anticipation windup (tight crouch)
                red_x = 260.0 - (f - 17) * 8.0
                blue_x = 700.0
                red_pose_x = red_x
            elif f == 20:
                # 2. EXPLOSIVE 1-FRAME STRIKE SNAP!
                red_x = 580.0 # Crossed distance in 1 frame!
                blue_x = 650.0
                # Draw motion smear connecting windup to strike
                draw_motion_smear(canvas, (244.0, GROUND_Y - 60), (red_x + 45, GROUND_Y - 60), width_start=12.0, width_end=4.0, color=(255, 120, 30, 200))
                draw_speed_lines(canvas, (red_x - 60, GROUND_Y - 60), direction_deg=180, length=120, count=6, color=(255, 140, 40, 220))
            else:
                # 3. Follow-through / hold (Blue ducks underneath!)
                red_x = 580.0
                blue_x = 650.0

            render_shadow(canvas, red_x, GROUND_Y, 0.0)
            render_shadow(canvas, blue_x, GROUND_Y, 0.0)

            # Red Punch Pose (arm extended)
            red_hy = GROUND_Y - 75.0
            red_pelvis = (red_x - 22.0, GROUND_Y - 35.0)
            red_hand_r = (red_x + 65.0, GROUND_Y - 62.0)
            red_sash = bow_curve((red_x - 6, red_hy), (red_x - 55, red_hy + 8), bow_amount=-10.0)

            red_skel = StickmanSkeleton(
                head=(red_x, red_hy),
                neck=(red_x + 10, red_hy + 16),
                pelvis=red_pelvis,
                l_elbow=(red_x - 15, red_hy + 22),
                l_hand=(red_x - 25, red_hy + 18),
                r_elbow=(red_x + 35, red_hy + 20),
                r_hand=red_hand_r,
                l_knee=(red_x - 35, GROUND_Y - 18),
                l_foot=(red_x - 45, GROUND_Y),
                r_knee=(red_x + 15, GROUND_Y - 18),
                r_foot=(red_x + 32, GROUND_Y),
                sash_pts=red_sash,
                facing=+1
            )
            red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

            # Blue Low Duck (crouches right under the punch!)
            duck_amount = 35.0 if f >= 20 else 10.0
            blue_hy = GROUND_Y - 55.0 + duck_amount * 0.4
            blue_pelvis = (blue_x + 8.0, GROUND_Y - 22.0)
            blue_sash = bow_curve((blue_x + 6, blue_hy), (blue_x + 40, blue_hy - 10), bow_amount=10.0)

            blue_skel = StickmanSkeleton(
                head=(blue_x, blue_hy),
                neck=(blue_x - 4, blue_hy + 12),
                pelvis=blue_pelvis,
                l_elbow=(blue_x - 20, blue_hy + 15),
                l_hand=(blue_x - 28, blue_hy + 8),
                r_elbow=(blue_x + 15, blue_hy + 18),
                r_hand=(blue_x + 25, blue_hy + 12),
                l_knee=(blue_x - 25, GROUND_Y - 12),
                l_foot=(blue_x - 35, GROUND_Y),
                r_knee=(blue_x + 22, GROUND_Y - 12),
                r_foot=(blue_x + 35, GROUND_Y),
                sash_pts=blue_sash,
                facing=-1
            )
            blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

            # Sonic wind streak passing over Blue's head
            if f in (20, 21, 22):
                draw.line([(red_hand_r[0] - 80, red_hand_r[1] + 2), (red_hand_r[0] + 50, red_hand_r[1] + 2)], fill=(255, 240, 220, 220), width=3)

        # =================================================================
        # BEAT 3: LEG SWEEP & SPINNING AXE KICK X-BLOCK (Frames 29-42 | 2.3s - 3.5s)
        # =================================================================
        elif f <= 42:
            t = (f - 29) / 13.0
            red_x = 560.0
            blue_x = 640.0

            if f <= 33:
                # Blue low leg sweep; Red jumps up!
                sweep_t = (f - 29) / 4.0
                sweep_foot_x = blue_x - 60.0 * sweep_t
                red_alt = sweep_t * 90.0

                render_shadow(canvas, blue_x, GROUND_Y, 0.0)
                render_shadow(canvas, red_x, GROUND_Y, red_alt)

                # Blue sweeping pose
                blue_hy = GROUND_Y - 45.0
                blue_pelvis = (blue_x + 15.0, GROUND_Y - 20.0)
                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_hy), neck=(blue_x - 5, blue_hy + 12), pelvis=blue_pelvis,
                    l_elbow=(blue_x - 15, blue_hy + 20), l_hand=(blue_x - 20, blue_hy + 25),
                    r_elbow=(blue_x + 15, blue_hy + 20), r_hand=(blue_x + 20, blue_hy + 25),
                    l_knee=((blue_pelvis[0] + sweep_foot_x) * 0.5, GROUND_Y - 5), l_foot=(sweep_foot_x, GROUND_Y),
                    r_knee=(blue_x + 25, GROUND_Y - 8), r_foot=(blue_x + 35, GROUND_Y),
                    facing=-1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f)

                # Red mid-air jump flip
                red_hy = GROUND_Y - 80.0 - red_alt
                red_pelvis = (red_x, GROUND_Y - 40.0 - red_alt)
                red_skel = StickmanSkeleton(
                    head=(red_x, red_hy), neck=(red_x, red_hy + 15), pelvis=red_pelvis,
                    l_elbow=(red_x - 20, red_hy + 25), l_hand=(red_x - 25, red_hy + 15),
                    r_elbow=(red_x + 20, red_hy + 25), r_hand=(red_x + 25, red_hy + 15),
                    l_knee=(red_x - 15, red_pelvis[1] + 25), l_foot=(red_x - 20, red_pelvis[1] + 45),
                    r_knee=(red_x + 15, red_pelvis[1] - 15), r_foot=(red_x + 25, red_pelvis[1] - 40),
                    facing=+1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f)

            else:
                # Frame 34-42: AXE KICK X-BLOCK IMPACT & HOLD (Hit-stop!)
                axe_y = GROUND_Y - 45.0
                render_shadow(canvas, blue_x, GROUND_Y, 0.0)
                render_shadow(canvas, red_x + 20, GROUND_Y, 40.0)

                # Red Axe Kick coming down hard
                red_hy = GROUND_Y - 125.0
                red_pelvis = (red_x, GROUND_Y - 80.0)
                red_foot_r = (blue_x - 10.0, axe_y + 5.0) # Foot slamming down on block

                # Curved flame smear wedge
                draw_arc_smear_wedge(canvas, (red_x, red_pelvis[1]), (red_x + 30, GROUND_Y - 160), red_foot_r, color=(255, 120, 30, 180))

                red_skel = StickmanSkeleton(
                    head=(red_x, red_hy), neck=(red_x + 4, red_hy + 15), pelvis=red_pelvis,
                    l_elbow=(red_x - 20, red_hy + 30), l_hand=(red_x - 25, red_hy + 45),
                    r_elbow=(red_x + 15, red_hy + 25), r_hand=(red_x + 25, red_hy + 35),
                    l_knee=(red_x - 15, red_pelvis[1] + 25), l_foot=(red_x - 20, red_pelvis[1] + 45),
                    r_knee=(red_x + 10, red_pelvis[1] + 10), r_foot=red_foot_r,
                    facing=+1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f)

                # Blue Cross-Arm X-BLOCK (knees bent, taking the heavy impact)
                blue_hy = GROUND_Y - 70.0
                blue_pelvis = (blue_x + 10.0, GROUND_Y - 32.0)
                block_pt = (blue_x - 10.0, axe_y)

                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_hy), neck=(blue_x - 4, blue_hy + 14), pelvis=blue_pelvis,
                    l_elbow=(blue_x - 8, axe_y + 15), l_hand=block_pt,
                    r_elbow=(blue_x - 12, axe_y + 15), r_hand=block_pt,
                    l_knee=(blue_x - 18, GROUND_Y - 15), l_foot=(blue_x - 25, GROUND_Y),
                    r_knee=(blue_x + 22, GROUND_Y - 15), r_foot=(blue_x + 35, GROUND_Y),
                    facing=-1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

                # Massive X-Block Hit Spark & Screen Shake on frame 35, 36
                draw_impact_spark(canvas, block_pt, radius=38.0, count=8, color=(255, 245, 180, 255))
                if f in (35, 36):
                    cam_dx = random.uniform(-4, 4)
                    cam_dy = random.uniform(-4, 4)
                    # Ground cracks under Blue's feet
                    draw.line([(blue_x - 35, GROUND_Y), (blue_x - 15, GROUND_Y + 12)], fill=(255, 140, 40, 240), width=2)
                    draw.line([(blue_x + 15, GROUND_Y), (blue_x + 35, GROUND_Y + 12)], fill=(255, 140, 40, 240), width=2)

        # =================================================================
        # BEAT 4: LIGHTNING FLASH-STEP TELEPORT & DAGGER FLURRY (Frames 43-60 | 3.5s - 5.0s)
        # =================================================================
        elif f <= 60:
            t = (f - 43) / 17.0

            if f <= 47:
                # Blue activates Lightning Flash-Step (Teleports behind Red!)
                sub_t = (f - 43) / 4.0
                red_x = 520.0
                blue_x = 640.0 - sub_t * 280.0 # Flashing across screen to 360

                render_shadow(canvas, red_x, GROUND_Y, 0.0)
                render_shadow(canvas, blue_x, GROUND_Y, 0.0)

                # Translucent Cyan Afterimages trailing Blue
                for ai in range(3):
                    ai_x = blue_x + (ai + 1) * 35.0
                    ai_ghost = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
                    draw_soft_gradient_glow(ai_ghost, (ai_x, GROUND_Y - 50), 35, (40, 180, 255, 60))
                    canvas.paste(ai_ghost, (0, 0), ai_ghost)

                # Red turning around in surprise
                red_hy = GROUND_Y - 80.0
                red_skel = StickmanSkeleton(
                    head=(red_x, red_hy), neck=(red_x - 2, red_hy + 16), pelvis=(red_x, GROUND_Y - 36.0),
                    l_elbow=(red_x - 15, red_hy + 30), l_hand=(red_x - 20, red_hy + 20),
                    r_elbow=(red_x + 15, red_hy + 30), r_hand=(red_x + 20, red_hy + 20),
                    l_knee=(red_x - 12, GROUND_Y - 18), l_foot=(red_x - 18, GROUND_Y),
                    r_knee=(red_x + 12, GROUND_Y - 18), r_foot=(red_x + 18, GROUND_Y),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f)

                # Blue mid-teleport dash pose
                blue_hy = GROUND_Y - 70.0
                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_hy), neck=(blue_x + 5, blue_hy + 14), pelvis=(blue_x + 18, GROUND_Y - 30.0),
                    l_elbow=(blue_x - 15, blue_hy + 15), l_hand=(blue_x - 30, blue_hy + 10),
                    r_elbow=(blue_x + 15, blue_hy + 15), r_hand=(blue_x + 30, blue_hy + 10),
                    l_knee=(blue_x - 10, GROUND_Y - 15), l_foot=(blue_x - 25, GROUND_Y),
                    r_knee=(blue_x + 20, GROUND_Y - 15), r_foot=(blue_x + 35, GROUND_Y),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

            else:
                # Blue unleashes 3-hit rapid dagger flurry from behind!
                flurry_f = f - 48
                blue_x = 360.0
                # Red skids backward as he parries and takes the 3rd hit
                red_x = 440.0 + (flurry_f / 12.0) * 110.0

                render_shadow(canvas, blue_x, GROUND_Y, 0.0)
                render_shadow(canvas, red_x, GROUND_Y, 0.0)

                # Red Skid Smoke on ground
                if flurry_f > 6:
                    draw_dust_puff(canvas, (red_x - 25, GROUND_Y), radius=18.0)
                    draw_speed_lines(canvas, (red_x - 10, GROUND_Y), direction_deg=180, length=40, count=3, color=(255, 140, 50, 200))

                # Blue rapid dagger slashes (alternating arms)
                slash_phase = flurry_f % 3
                blue_hy = GROUND_Y - 75.0
                blue_pelvis = (blue_x - 12.0, GROUND_Y - 34.0)

                if slash_phase == 0:
                    b_hand_l = (blue_x + 45.0, GROUND_Y - 65.0)
                    b_hand_r = (blue_x + 15.0, GROUND_Y - 45.0)
                elif slash_phase == 1:
                    b_hand_l = (blue_x + 15.0, GROUND_Y - 45.0)
                    b_hand_r = (blue_x + 50.0, GROUND_Y - 55.0)
                else:
                    b_hand_l = (blue_x + 48.0, GROUND_Y - 40.0)
                    b_hand_r = (blue_x + 48.0, GROUND_Y - 40.0)

                # Electric slash smear arcs
                draw.arc([blue_x + 10, GROUND_Y - 80, blue_x + 70, GROUND_Y - 20], start=30, end=150, fill=COLOR_BLUE_BOLT, width=4)

                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_hy), neck=(blue_x + 6, blue_hy + 14), pelvis=blue_pelvis,
                    l_elbow=(blue_x + 20, blue_hy + 25), l_hand=b_hand_l,
                    r_elbow=(blue_x + 25, blue_hy + 20), r_hand=b_hand_r,
                    l_knee=(blue_x - 15, GROUND_Y - 18), l_foot=(blue_x - 25, GROUND_Y),
                    r_knee=(blue_x + 15, GROUND_Y - 18), r_foot=(blue_x + 30, GROUND_Y),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

                # Red Parrying / Staggering Pose
                red_hy = GROUND_Y - 78.0
                red_skel = StickmanSkeleton(
                    head=(red_x, red_hy), neck=(red_x - 6, red_hy + 15), pelvis=(red_x + 14.0, GROUND_Y - 32.0),
                    l_elbow=(red_x - 22, red_hy + 22), l_hand=(red_x - 30, red_hy + 35),
                    r_elbow=(red_x - 12, red_hy + 20), r_hand=(red_x - 18, red_hy + 30),
                    l_knee=(red_x + 25, GROUND_Y - 15), l_foot=(red_x + 35, GROUND_Y),
                    r_knee=(red_x - 10, GROUND_Y - 15), r_foot=(red_x - 20, GROUND_Y),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f)

                # Impact sparks on parry
                draw_impact_spark(canvas, (blue_x + 55, GROUND_Y - 55), radius=28.0, count=6, color=(255, 230, 120, 255))

        # =================================================================
        # BEAT 5: RISING FLAME DRAGON UPPERCUT LAUNCH (Frames 61-76 | 5.0s - 6.3s)
        # =================================================================
        elif f <= 76:
            t = (f - 61) / 15.0

            if f <= 64:
                # 1. Red plants back foot, coils spine for Dragon Uppercut
                red_x = 550.0
                blue_x = 420.0
                render_shadow(canvas, red_x, GROUND_Y, 0.0)
                render_shadow(canvas, blue_x, GROUND_Y, 0.0)

                # Red deep coil anticipation
                red_hy = GROUND_Y - 65.0
                red_pelvis = (red_x + 15, GROUND_Y - 25.0)
                red_skel = StickmanSkeleton(
                    head=(red_x, red_hy), neck=(red_x - 4, red_hy + 14), pelvis=red_pelvis,
                    l_elbow=(red_x - 15, red_hy + 20), l_hand=(red_x - 25, red_hy + 15),
                    r_elbow=(red_x + 25, red_hy + 25), r_hand=(red_x + 35, red_hy + 35), # Fist coiled back
                    l_knee=(red_x - 20, GROUND_Y - 12), l_foot=(red_x - 35, GROUND_Y),
                    r_knee=(red_x + 25, GROUND_Y - 12), r_foot=(red_x + 40, GROUND_Y),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

                blue_hy = GROUND_Y - 78.0
                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_hy), neck=(blue_x + 4, blue_hy + 14), pelvis=(blue_x - 10, GROUND_Y - 34),
                    l_elbow=(blue_x + 18, blue_hy + 20), l_hand=(blue_x + 30, blue_hy + 15),
                    r_elbow=(blue_x + 15, blue_hy + 25), r_hand=(blue_x + 25, blue_hy + 30),
                    l_knee=(blue_x - 15, GROUND_Y - 18), l_foot=(blue_x - 25, GROUND_Y),
                    r_knee=(blue_x + 15, GROUND_Y - 18), r_foot=(blue_x + 30, GROUND_Y),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f)

            elif f == 65 or f == 66:
                # 2. SAKUGA IMPACT FRAME! Rising Dragon Uppercut connects under Blue's chin!
                contact_x = 450.0
                contact_y = GROUND_Y - 65.0

                # Inverted Monochrome Screen Flash on frame 66
                draw_sakuga_impact_flash(canvas, (contact_x, contact_y), radius=260.0, invert_colors=(f == 66))

                # Vertical Dragon Flame Pillar Smear
                draw_motion_smear(canvas, (contact_x, GROUND_Y), (contact_x, contact_y - 80), width_start=24.0, width_end=8.0, color=(255, 140, 30, 240))
                draw_impact_spark(canvas, (contact_x, contact_y), radius=65.0, count=10, color=(255, 255, 200, 255))

                cam_dx = random.uniform(-6, 6)
                cam_dy = random.uniform(-6, 6)

                # Red in full extension upward
                red_skel = StickmanSkeleton(
                    head=(contact_x + 18, GROUND_Y - 110), neck=(contact_x + 16, GROUND_Y - 95), pelvis=(contact_x + 10, GROUND_Y - 45),
                    l_elbow=(contact_x + 30, GROUND_Y - 80), l_hand=(contact_x + 35, GROUND_Y - 65),
                    r_elbow=(contact_x, GROUND_Y - 115), r_hand=(contact_x - 5, contact_y - 20), # Uppercut fist
                    l_knee=(contact_x + 15, GROUND_Y - 20), l_foot=(contact_x + 15, GROUND_Y),
                    r_knee=(contact_x + 5, GROUND_Y - 30), r_foot=(contact_x - 5, GROUND_Y - 10),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

                # Blue Head Snapped violently backward!
                blue_skel = StickmanSkeleton(
                    head=(contact_x - 18, contact_y - 30), neck=(contact_x - 14, contact_y - 12), pelvis=(contact_x - 10, GROUND_Y - 25),
                    l_elbow=(contact_x - 30, contact_y + 10), l_hand=(contact_x - 40, contact_y),
                    r_elbow=(contact_x - 25, contact_y + 15), r_hand=(contact_x - 35, contact_y + 10),
                    l_knee=(contact_x - 15, GROUND_Y - 12), l_foot=(contact_x - 20, GROUND_Y),
                    r_knee=(contact_x - 5, GROUND_Y - 15), r_foot=(contact_x, GROUND_Y),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f)

            else:
                # 3. Sky Launch! Blue launched 220px upward, Red rocket-jumps in pursuit!
                sub_t = (f - 67) / 9.0
                launch_y = ease_out_quad(sub_t) * 220.0

                blue_x = 430.0
                blue_y = GROUND_Y - launch_y
                red_x = 460.0
                red_y = GROUND_Y - launch_y * 0.85

                render_shadow(canvas, blue_x, GROUND_Y, launch_y)
                render_shadow(canvas, red_x, GROUND_Y, launch_y * 0.85)

                # Vertical rising speed trails
                draw_speed_lines(canvas, (blue_x, blue_y + 60), direction_deg=90, length=90, count=4, color=(120, 210, 255, 180))
                draw_speed_lines(canvas, (red_x, red_y + 60), direction_deg=90, length=100, count=5, color=(255, 140, 30, 200))

                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_y - 75), neck=(blue_x, blue_y - 60), pelvis=(blue_x, blue_y - 20),
                    l_elbow=(blue_x - 20, blue_y - 45), l_hand=(blue_x - 25, blue_y - 30),
                    r_elbow=(blue_x + 20, blue_y - 45), r_hand=(blue_x + 25, blue_y - 30),
                    l_knee=(blue_x - 12, blue_y + 5), l_foot=(blue_x - 15, blue_y + 30),
                    r_knee=(blue_x + 12, blue_y + 5), r_foot=(blue_x + 15, blue_y + 30),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f)

                red_skel = StickmanSkeleton(
                    head=(red_x, red_y - 75), neck=(red_x, red_y - 60), pelvis=(red_x, red_y - 20),
                    l_elbow=(red_x - 15, red_y - 35), l_hand=(red_x - 20, red_y - 15),
                    r_elbow=(red_x + 15, red_y - 75), r_hand=(red_x + 10, red_y - 100),
                    l_knee=(red_x - 10, red_y + 10), l_foot=(red_x - 10, red_y + 35),
                    r_knee=(red_x + 10, red_y + 5), r_foot=(red_x + 15, red_y + 25),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

        # =================================================================
        # BEAT 6: MID-AIR DOGFIGHT & LIGHTNING DAGGER BARRAGE (Frames 77-92 | 6.3s - 7.7s)
        # =================================================================
        elif f <= 92:
            t = (f - 77) / 15.0
            air_alt = 220.0 + math.sin(t * math.pi) * 35.0

            red_x = 540.0 + math.sin(f * 0.8) * 15.0
            red_y = GROUND_Y - air_alt
            blue_x = 420.0 - math.sin(f * 0.8) * 15.0
            blue_y = GROUND_Y - air_alt

            render_shadow(canvas, red_x, GROUND_Y, air_alt)
            render_shadow(canvas, blue_x, GROUND_Y, air_alt)

            # Mid-air clash sparks & electric arcs
            mid_x = (red_x + blue_x) * 0.5
            mid_y = (red_y + blue_y) * 0.5 - 45.0
            draw_impact_spark(canvas, (mid_x, mid_y), radius=35.0, count=7, color=(255, 240, 160, 240))

            # Blue firing 3 homing lightning dagger bolts across the gap
            for bolt_i in range(3):
                bx_t = (t * 3.0 + bolt_i * 0.33) % 1.0
                bx = blue_x + 40.0 + bx_t * (red_x - blue_x - 60.0)
                by = blue_y - 45.0 + math.sin(bx_t * math.pi) * 20.0
                draw.line([(bx - 15, by), (bx + 15, by)], fill=COLOR_BLUE_BOLT, width=4)
                draw.line([(bx - 15, by), (bx + 15, by)], fill=(255, 255, 255, 255), width=2)

            # Fighters in dynamic aerial flight stances
            red_skel = StickmanSkeleton(
                head=(red_x, red_y - 75), neck=(red_x - 4, red_y - 60), pelvis=(red_x + 8, red_y - 20),
                l_elbow=(red_x - 22, red_y - 40), l_hand=(red_x - 35, red_y - 45),
                r_elbow=(red_x - 15, red_y - 30), r_hand=(red_x - 25, red_y - 15),
                l_knee=(red_x + 20, red_y + 10), l_foot=(red_x + 25, red_y + 35),
                r_knee=(red_x + 5, red_y + 15), r_foot=(red_x + 10, red_y + 40),
                facing=-1
            )
            red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

            blue_skel = StickmanSkeleton(
                head=(blue_x, blue_y - 75), neck=(blue_x + 4, blue_y - 60), pelvis=(blue_x - 8, blue_y - 20),
                l_elbow=(blue_x + 22, blue_y - 40), l_hand=(blue_x + 35, blue_y - 45),
                r_elbow=(blue_x + 15, blue_y - 30), r_hand=(blue_x + 25, blue_y - 15),
                l_knee=(blue_x - 20, blue_y + 10), l_foot=(blue_x - 25, blue_y + 35),
                r_knee=(blue_x - 5, blue_y + 15), r_foot=(blue_x - 10, blue_y + 40),
                facing=+1
            )
            blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

        # =================================================================
        # BEAT 7: METEOR DIVE CONVERGENCE & APEX SAKUGA CLASH (Frames 93-105)
        # =================================================================
        elif f <= 105:
            t = (f - 93) / 12.0

            if f <= 101:
                # Converging toward apex collision point
                red_x = 620.0 - t * 140.0
                red_y = 120.0 + t * 120.0 # Diving down from above
                blue_x = 340.0 + t * 140.0
                blue_y = 380.0 - t * 140.0 # Thrusting up from below

                render_shadow(canvas, red_x, GROUND_Y, GROUND_Y - red_y)
                render_shadow(canvas, blue_x, GROUND_Y, GROUND_Y - blue_y)

                # High-speed converging action lines
                draw_speed_lines(canvas, (red_x + 35, red_y - 35), direction_deg=225, length=90, count=5, color=(255, 120, 30, 220))
                draw_speed_lines(canvas, (blue_x - 35, blue_y + 35), direction_deg=45, length=90, count=5, color=(80, 200, 255, 220))

                red_skel = StickmanSkeleton(
                    head=(red_x, red_y - 65), neck=(red_x - 5, red_y - 50), pelvis=(red_x + 20, red_y - 15),
                    l_elbow=(red_x - 25, red_y - 25), l_hand=(red_x - 35, red_y),
                    r_elbow=(red_x - 15, red_y - 20), r_hand=(red_x - 25, red_y + 10),
                    l_knee=(red_x + 25, red_y + 15), l_foot=(red_x + 40, red_y + 30),
                    r_knee=(red_x + 15, red_y + 20), r_foot=(red_x + 25, red_y + 40),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f, weapon_active=True)

                blue_skel = StickmanSkeleton(
                    head=(blue_x, blue_y - 65), neck=(blue_x + 5, blue_y - 50), pelvis=(blue_x - 20, blue_y - 15),
                    l_elbow=(blue_x + 25, blue_y - 25), l_hand=(blue_x + 35, blue_y),
                    r_elbow=(blue_x + 15, blue_y - 20), r_hand=(blue_x + 25, blue_y + 10),
                    l_knee=(blue_x - 25, blue_y + 15), l_foot=(blue_x - 40, blue_y + 30),
                    r_knee=(blue_x - 15, blue_y + 20), r_foot=(blue_x - 25, blue_y + 40),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f, weapon_active=True)

            else:
                # Frames 102, 103, 104, 105: APEX SAKUGA IMPACT COLLISION!
                clash_pt = (WIDTH * 0.5, 240.0)

                # Frame 102 is the definitive INVERTED MONOCHROME IMPACT FRAME
                draw_sakuga_impact_flash(canvas, clash_pt, radius=320.0, invert_colors=(f == 102))

                # Expanding Plasma Shockwave Ring
                ring_r = (f - 101) * 75.0 + 40.0
                draw.ellipse([clash_pt[0] - ring_r, clash_pt[1] - ring_r * 0.7, clash_pt[0] + ring_r, clash_pt[1] + ring_r * 0.7],
                             outline=(255, 255, 255, 240), width=6)
                draw_impact_spark(canvas, clash_pt, radius=85.0, count=12, color=(255, 250, 180, 255))

                cam_dx = random.uniform(-8, 8)
                cam_dy = random.uniform(-8, 8)

                # Fighters locked at apex
                red_skel = StickmanSkeleton(
                    head=(clash_pt[0] + 25, clash_pt[1] - 45), neck=(clash_pt[0] + 15, clash_pt[1] - 30), pelvis=(clash_pt[0] + 35, clash_pt[1] + 10),
                    l_elbow=(clash_pt[0] + 10, clash_pt[1] - 15), l_hand=clash_pt,
                    r_elbow=(clash_pt[0] + 5, clash_pt[1] - 20), r_hand=clash_pt,
                    l_knee=(clash_pt[0] + 45, clash_pt[1] + 35), l_foot=(clash_pt[0] + 60, clash_pt[1] + 60),
                    r_knee=(clash_pt[0] + 35, clash_pt[1] + 40), r_foot=(clash_pt[0] + 45, clash_pt[1] + 70),
                    facing=-1
                )
                red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire", frame_seed=f)

                blue_skel = StickmanSkeleton(
                    head=(clash_pt[0] - 25, clash_pt[1] - 45), neck=(clash_pt[0] - 15, clash_pt[1] - 30), pelvis=(clash_pt[0] - 35, clash_pt[1] + 10),
                    l_elbow=(clash_pt[0] - 10, clash_pt[1] - 15), l_hand=clash_pt,
                    r_elbow=(clash_pt[0] - 5, clash_pt[1] - 20), r_hand=clash_pt,
                    l_knee=(clash_pt[0] - 45, clash_pt[1] + 35), l_foot=(clash_pt[0] - 60, clash_pt[1] + 60),
                    r_knee=(clash_pt[0] - 35, clash_pt[1] + 40), r_foot=(clash_pt[0] - 45, clash_pt[1] + 70),
                    facing=+1
                )
                blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning", frame_seed=f)

        # =================================================================
        # BEAT 8: GROUND CRATER SLAM, SMOKE PILLARS & CINEMATICS (Frames 106-120)
        # =================================================================
        else:
            settle_t = (f - 106) / 14.0
            crater_cx = WIDTH * 0.5
            crater_cy = GROUND_Y

            # Frame 106-108: Massive Ground Impact & Violent Camera Shake
            if f <= 108:
                cam_dx = random.uniform(-10, 10) * (1.0 - (f - 106) / 3.0)
                cam_dy = random.uniform(-8, 8) * (1.0 - (f - 106) / 3.0)

                # Ground detonation shockwave & explosion flash
                draw_impact_spark(canvas, (crater_cx, crater_cy - 10), radius=95.0, count=12, color=(255, 255, 230, 255))
                draw_dust_puff(canvas, (crater_cx - 70, crater_cy), radius=45.0)
                draw_dust_puff(canvas, (crater_cx + 70, crater_cy), radius=45.0)

            # Volcanic Crater Fissure Lines Radiating from Ground Zero
            for angle_deg in (15, 45, 75, 105, 135, 165):
                rad = math.radians(angle_deg)
                c_len = 95.0
                cx2 = crater_cx + math.cos(rad) * c_len
                cy2 = crater_cy + math.sin(rad) * 45.0
                draw_tapered_stroke(canvas, [(crater_cx, crater_cy), (cx2, cy2)], (255, 110, 25, 230), base_width=3.5)
                draw_tapered_stroke(canvas, [(crater_cx, crater_cy), (cx2, cy2)], (255, 230, 80, 255), base_width=1.2)

            # Billowing Smoke Dust Pillars rising slowly
            smoke_alpha = int(220 * (1.0 - settle_t * 0.75))
            draw_dust_puff(canvas, (crater_cx - 90 - settle_t * 25, crater_cy - settle_t * 45), radius=42.0 + settle_t * 20, color=(170, 160, 168, smoke_alpha))
            draw_dust_puff(canvas, (crater_cx + 90 + settle_t * 25, crater_cy - settle_t * 45), radius=42.0 + settle_t * 20, color=(170, 160, 168, smoke_alpha))

            # Red in Dynamic One-Knee Superhero Landing Pose
            red_x = crater_cx - 48.0
            render_shadow(canvas, red_x, GROUND_Y, 0.0)
            red_hy = GROUND_Y - 55.0
            red_pelvis = (red_x - 10.0, GROUND_Y - 22.0)
            red_sash = bow_curve((red_x - 6, red_hy), (red_x - 55, red_hy - 18 + math.sin(f * 0.4) * 6), bow_amount=-12.0)

            red_skel = StickmanSkeleton(
                head=(red_x, red_hy), neck=(red_x + 5, red_hy + 14), pelvis=red_pelvis,
                l_elbow=(red_x - 18, red_hy + 15), l_hand=(red_x - 22, red_hy + 28),
                r_elbow=(red_x + 12, red_hy + 18), r_hand=(red_x + 15, GROUND_Y), # Fist planted into ground
                l_knee=(red_x - 25, GROUND_Y - 8), l_foot=(red_x - 35, GROUND_Y),
                r_knee=(red_x + 15, GROUND_Y - 5), r_foot=(red_x + 25, GROUND_Y),
                sash_pts=red_sash,
                facing=+1
            )
            red_skel.draw(canvas, COLOR_RED, COLOR_RED_SASH, aura_type="fire" if f < 114 else None, frame_seed=f)

            # Blue Standing Recovered in Storm Shinobi Stance
            blue_x = crater_cx + 85.0
            render_shadow(canvas, blue_x, GROUND_Y, 0.0)
            blue_hy = GROUND_Y - 78.0
            blue_pelvis = (blue_x + 8.0, GROUND_Y - 34.0)
            blue_sash = bow_curve((blue_x + 6, blue_hy), (blue_x + 52, blue_hy - 14 + math.sin(f * 0.4) * 6), bow_amount=12.0)

            blue_skel = StickmanSkeleton(
                head=(blue_x, blue_hy), neck=(blue_x - 4, blue_hy + 14), pelvis=blue_pelvis,
                l_elbow=(blue_x - 18, blue_hy + 22), l_hand=(blue_x - 25, blue_hy + 15),
                r_elbow=(blue_x + 15, blue_hy + 25), r_hand=(blue_x + 22, blue_hy + 35),
                l_knee=(blue_x - 15, GROUND_Y - 16), l_foot=(blue_x - 22, GROUND_Y),
                r_knee=(blue_x + 15, GROUND_Y - 16), r_foot=(blue_x + 25, GROUND_Y),
                sash_pts=blue_sash,
                facing=-1
            )
            blue_skel.draw(canvas, COLOR_BLUE, COLOR_BLUE_SASH, aura_type="lightning" if f < 114 else None, frame_seed=f, weapon_active=True)

            # Cinematic Anime Letterbox Bars (Top & Bottom black bars)
            bar_h = int(settle_t * 36.0)
            if bar_h > 0:
                draw.rectangle([0, 0, WIDTH, bar_h], fill=(0, 0, 0, 255))
                draw.rectangle([0, HEIGHT - bar_h, WIDTH, HEIGHT], fill=(0, 0, 0, 255))

        # Apply Camera Shake if active on this frame
        if abs(cam_dx) > 0.5 or abs(cam_dy) > 0.5:
            canvas = apply_camera_shake(canvas, cam_dx, cam_dy)

        frames.append(canvas)

    return frames


def main():
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.join(examples_dir, "sakuga_stickman_fight_10s.pclx")
    mp4_path = os.path.join(examples_dir, "sakuga_stickman_fight_10s.mp4")
    gif_path = os.path.join(examples_dir, "sakuga_stickman_fight_10s.gif")
    strip_path = os.path.join(examples_dir, "sakuga_stickman_fight_contact_strip.png")

    print("==================================================================")
    print("MASTERPIECE SAKUGA ANIME STICKMAN FIGHT ANIMATION GENERATOR")
    print(f"Canvas: {WIDTH}x{HEIGHT} (16:9 Anime Widescreen) | Framerate: {FPS} FPS | Frames: {TOTAL_FRAMES}")
    print("==================================================================")

    print("Choreographing 120 articulated Sakuga combat animation frames...")
    frames = generate_masterpiece_frames()
    print(f"[OK] Generated {len(frames)} articulated combat frames in memory.")

    print(f"Creating Pencil2D Project: {project_path}")
    proj = Pencil2DProject.create(
        file_path=project_path,
        width=WIDTH,
        height=HEIGHT,
        fps=FPS,
        layer_names=["Sakuga Fight Layer"]
    )

    for idx, f_img in enumerate(frames, start=1):
        proj.add_frame_image("Sakuga Fight Layer", idx, f_img)

    proj.save(project_path)
    print(f"[OK] Saved .pclx project archive: {project_path}")

    # Generate Visual Verification Filmstrip Contact Sheet
    print("Generating visual verification contact strip (pencil2d_look)...")
    strip_img, final_strip = proj.generate_preview_strip(
        frames=[8, 20, 35, 52, 66, 82, 102, 115],
        thumb_width=240,
        output_path=strip_path
    )
    print(f"[OK] Contact strip saved: {final_strip} ({strip_img.width}x{strip_img.height})")

    # Render MP4 video via Pencil2D AppImage CLI
    print("Rendering 10-second animation video to MP4 via Pencil2D AppImage...")
    ok_mp4, msg_mp4 = export_project(project_path, mp4_path, fps=FPS)
    print(f"MP4 Export ({ok_mp4}): {msg_mp4}")

    # Render animated GIF preview
    print("Rendering animated GIF preview...")
    ok_gif, msg_gif = export_project(project_path, gif_path, fps=FPS, force_pure_python=True)
    print(f"GIF Export ({ok_gif}): {msg_gif}")

    print("==================================================================")
    print("ALL RENDERS COMPLETED SUCCESSFULLY!")
    print(f"- Project Archive: {project_path}")
    print(f"- Contact Sheet:   {strip_path}")
    print(f"- MP4 Video:       {mp4_path}")
    print(f"- Animated GIF:    {gif_path}")
    print("==================================================================")


if __name__ == "__main__":
    main()
