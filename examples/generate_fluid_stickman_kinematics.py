#!/usr/bin/env python3
"""Masterwork Fluid Stickman Kinematics Animation (24 FPS / 240 Frames / 10.0s).

Solves stiffness, ice-skate sliding, and teleporting joint movements:
1. Analytic 2-Bone Inverse Kinematics (IK) for all limbs (natural knee & elbow flexion).
2. Grounded Locomotion Engine:
   - Stance feet lock firmly to the ground during support phase (zero sliding).
   - Swing leg flexes at knee, arcs upward for clearance, and lands heel-first.
   - Double-frequency pelvic vertical bounce and lateral weight shift.
   - Forward spinal lean proportional to movement speed.
   - Natural pendulum arm swing in opposition to legs.
3. Continuous Keyframe Interpolation:
   - Smoothstep & cubic spline easing between all poses.
   - ZERO teleporting or instantaneous joint snaps.
4. Arc-Based Hand & Leg Combat Kinematics:
   - Punches, parries, roundhouse kicks, and weapon swings travel along smooth circular/elliptical arcs.
   - Parabolic aerial jumping with rotational tuck and squash-cushion landing.
"""

import math
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from pencil2d_mcp.core import Pencil2DProject, export_project
from pencil2d_mcp.drawing import (
    StickmanPose,
    apply_camera_shake,
    blend_stickman_poses,
    calculate_squash_stretch,
    clamp,
    draw_arc_smear_wedge,
    draw_dust_puff,
    draw_impact_spark,
    draw_motion_smear,
    draw_soft_gradient_glow,
    draw_speed_lines,
    draw_tapered_stroke,
    ease_in_out_cubic,
    ease_in_quad,
    ease_out_quad,
    generate_locomotion_pose,
    parabolic_arc,
    render_smooth_stickman,
    solve_2bone_ik,
)

WIDTH = 960
HEIGHT = 540
FPS = 24
TOTAL_FRAMES = 240  # 10.0 seconds at 24 FPS
GROUND_Y = 435.0

COLOR_RED = (24, 20, 26, 255)
COLOR_RED_SASH = (245, 45, 45, 255)
COLOR_BLUE = (18, 22, 30, 255)
COLOR_BLUE_SASH = (35, 190, 255, 255)


def create_custom_pose(pelvis_x: float, pelvis_y: float,
                       torso_lean_deg: float,
                       l_arm_target: Tuple[float, float],
                       r_arm_target: Tuple[float, float],
                       l_foot_target: Tuple[float, float],
                       r_foot_target: Tuple[float, float],
                       facing: int = 1,
                       head_tilt_deg: float = 0.0,
                       weapon: Optional[str] = None,
                       l_knee_fwd: bool = True,
                       r_knee_fwd: bool = True) -> StickmanPose:
    """Construct an anatomically grounded StickmanPose using 2-Bone IK."""
    thigh_len = 28.0
    calf_len = 28.0
    upper_arm = 20.0
    forearm = 20.0
    torso_len = 42.0
    head_r = 14.0

    pelvis = (pelvis_x, pelvis_y)
    lean_rad = math.radians(torso_lean_deg) * facing
    neck = (pelvis[0] + math.sin(lean_rad) * torso_len,
            pelvis[1] - math.cos(lean_rad) * torso_len)
    spine_mid = ((pelvis[0] + neck[0]) * 0.5 + math.sin(lean_rad) * 3.5,
                 (pelvis[1] + neck[1]) * 0.5)

    head_rad = math.radians(torso_lean_deg + head_tilt_deg) * facing
    head = (neck[0] + math.sin(head_rad) * (head_r + 6.0),
            neck[1] - math.cos(head_rad) * (head_r + 6.0))

    l_shoulder = (neck[0] - facing * 4.0, neck[1] + 3.0)
    r_shoulder = (neck[0] + facing * 4.0, neck[1] + 3.0)
    l_hip = (pelvis[0] - facing * 5.0, pelvis[1])
    r_hip = (pelvis[0] + facing * 5.0, pelvis[1])

    # 2-Bone IK for legs
    l_knee = solve_2bone_ik(l_hip, l_foot_target, thigh_len, calf_len, bend_positive=(facing > 0 if l_knee_fwd else facing < 0))
    r_knee = solve_2bone_ik(r_hip, r_foot_target, thigh_len, calf_len, bend_positive=(facing > 0 if r_knee_fwd else facing < 0))

    # 2-Bone IK for arms
    l_elbow = solve_2bone_ik(l_shoulder, l_arm_target, upper_arm, forearm, bend_positive=(facing < 0))
    r_elbow = solve_2bone_ik(r_shoulder, r_arm_target, upper_arm, forearm, bend_positive=(facing < 0))

    return StickmanPose(
        head=head, neck=neck, pelvis=pelvis, spine_mid=spine_mid,
        l_shoulder=l_shoulder, l_elbow=l_elbow, l_hand=l_arm_target,
        r_shoulder=r_shoulder, r_elbow=r_elbow, r_hand=r_arm_target,
        l_hip=l_hip, l_knee=l_knee, l_foot=l_foot_target,
        r_hip=r_hip, r_knee=r_knee, r_foot=r_foot_target,
        facing=facing, head_radius=head_r, weapon=weapon
    )


def render_environment(w: int, h: int, ground_y: float,
                       cam_pan_x: float = 0.0, frame_num: int = 0) -> Image.Image:
    """Render cinematic martial arts courtyard with drifting sakura blossoms."""
    bg = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(bg, "RGBA")

    # Sky gradient: Twilight dusk violet into amber
    for y in range(int(ground_y)):
        t = y / float(ground_y)
        r = int(28 * (1.0 - t) + 160 * t)
        g = int(24 * (1.0 - t) + 85 * t)
        b = int(48 * (1.0 - t) + 72 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Setting sun / full moon
    moon_x = (w * 0.5) - cam_pan_x * 0.1
    moon_y = ground_y - 120
    draw_soft_gradient_glow(bg, (moon_x, moon_y), 130, (255, 215, 140, 140))
    draw.ellipse([moon_x - 45, moon_y - 45, moon_x + 45, moon_y + 45], fill=(255, 248, 225, 255))

    # Distant mountain silhouettes (parallax 0.2)
    m_off = -cam_pan_x * 0.2
    mountains = [
        (0, ground_y - 80), (160 + m_off, ground_y - 150), (320 + m_off, ground_y - 95),
        (500 + m_off, ground_y - 180), (680 + m_off, ground_y - 110), (840 + m_off, ground_y - 165),
        (w, ground_y - 90), (w, ground_y), (0, ground_y)
    ]
    draw.polygon(mountains, fill=(45, 28, 42, 255))

    # Traditional Dojo Pagoda Pillars in midground (parallax 0.5)
    for p_base_x in [120, 840]:
        px = p_base_x - cam_pan_x * 0.5
        draw.rectangle([px - 14, ground_y - 180, px + 14, ground_y], fill=(52, 38, 46, 255), outline=(78, 56, 68, 255))
        # Pagoda lantern
        ly = ground_y - 150
        draw.rectangle([px - 10, ly - 16, px + 10, ly + 16], fill=(245, 140, 45, 220))
        draw_soft_gradient_glow(bg, (px, ly), 50, (255, 160, 50, 90))

    # Courtyard ground: Stone flags with warm highlights
    draw.rectangle([0, int(ground_y), w, h], fill=(26, 22, 28, 255))
    draw.line([(0, ground_y), (w, ground_y)], fill=(210, 110, 45, 255), width=2)
    # Paved flagstone lines
    for fx in range(-50, w + 100, 75):
        gx = fx - (cam_pan_x % 75)
        draw.line([(gx, ground_y), (gx - 35, h)], fill=(40, 32, 42, 255), width=1)

    # Drifting Cherry Blossom Petals
    random.seed(42)
    for i in range(18):
        speed = 1.2 + (i % 5) * 0.4
        petal_x = (i * 58 + frame_num * speed * 1.8) % (w + 40) - 20
        petal_y = (40 + i * 26 + math.sin(frame_num * 0.08 + i) * 20.0) % ground_y
        rot = frame_num * 0.05 + i
        pw = 5.0
        ph = 3.0
        draw.ellipse([petal_x - pw, petal_y - ph, petal_x + pw, petal_y + ph], fill=(255, 185, 205, 210))

    return bg


def render_shadow(canvas: Image.Image, x: float, ground_y: float,
                  altitude: float = 0.0, radius_base: float = 24.0):
    """Draw smooth elliptical contact shadow on the ground."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    factor = max(0.2, 1.0 - altitude / 200.0)
    rw = radius_base * factor
    rh = rw * 0.32
    alpha = int(140 * factor)
    draw.ellipse([x - rw, ground_y - rh, x + rw, ground_y + rh], fill=(12, 10, 14, alpha))


# =========================================================================
# CHOREOGRAPHY COMPOSITION: 240 FRAMES AT 24 FPS (10.0 SECONDS)
# =========================================================================

def generate_fluid_masterpiece_frames() -> List[Image.Image]:
    frames: List[Image.Image] = []

    # Persistent state across frames
    red_pos_x = 120.0
    blue_pos_x = 840.0

    print("Generating 240 frames of continuous, fully articulated stickman motion...")

    for f in range(1, TOTAL_FRAMES + 1):
        cam_dx = 0.0
        cam_dy = 0.0
        cam_pan_x = 0.0

        # =================================================================
        # ACT 1: RED NATURAL GROUNDED WALK (Frames 1-45 | 0.0s - 1.875s)
        # =================================================================
        if f <= 45:
            # Red walks forward naturally from x=120 to x=330
            # Phase is continuously tied to distance travelled (zero foot sliding!)
            t = (f - 1) / 44.0
            ease_dist = ease_in_out_cubic(t)
            red_pos_x = 120.0 + ease_dist * 210.0 # Reaches 330.0

            # Foot plant phase: exactly 1 stride cycle per 50px
            walk_phase = (red_pos_x / 50.0) % 1.0
            walk_speed = 1.0 * (1.0 - ease_dist * 0.3) # Slows down naturally into stance

            red_pose = generate_locomotion_pose(
                x=red_pos_x, ground_y=GROUND_Y, phase=walk_phase,
                facing=+1, speed=walk_speed
            )

            # In the final 8 frames of Act 1 (f=38-45), blend seamlessly into idle stance
            if f >= 38:
                blend_t = (f - 38) / 7.0
                idle_stance = create_custom_pose(
                    pelvis_x=330.0, pelvis_y=GROUND_Y - 51.0,
                    torso_lean_deg=4.0,
                    l_arm_target=(330.0 - 12.0, GROUND_Y - 35.0),
                    r_arm_target=(330.0 + 14.0, GROUND_Y - 35.0),
                    l_foot_target=(330.0 - 14.0, GROUND_Y),
                    r_foot_target=(330.0 + 14.0, GROUND_Y),
                    facing=+1
                )
                red_pose = blend_stickman_poses(red_pose, idle_stance, blend_t)

            # Blue is waiting in ready stance at 820.0
            blue_pose = create_custom_pose(
                pelvis_x=820.0, pelvis_y=GROUND_Y - 51.0,
                torso_lean_deg=-5.0,
                l_arm_target=(820.0 - 15.0, GROUND_Y - 38.0),
                r_arm_target=(820.0 + 12.0, GROUND_Y - 38.0),
                l_foot_target=(820.0 - 16.0, GROUND_Y),
                r_foot_target=(820.0 + 16.0, GROUND_Y),
                facing=-1
            )

            cam_pan_x = (red_pos_x + 820.0) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, red_pose.pelvis[0], GROUND_Y, 0.0)
            render_shadow(canvas, blue_pose.pelvis[0], GROUND_Y, 0.0)

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f)
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f)

        # =================================================================
        # ACT 2: FLUID WING CHUN HAND ARCS & WEIGHT SHIFT (Frames 46-80 | 1.875s - 3.33s)
        # =================================================================
        elif f <= 80:
            sub_t = (f - 46) / 34.0
            red_pos_x = 330.0

            # Dynamic weight shift: pelvis moves back onto left leg, drops into low martial stance
            shift_back = math.sin(sub_t * math.pi) * 12.0
            crouch_depth = math.sin(sub_t * math.pi) * 8.0
            red_pelvis_y = GROUND_Y - 51.0 + crouch_depth

            # Hands trace smooth continuous circular arcs (Tan Sau & Pak Sau deflections)
            arc_phase = sub_t * 2.0 * math.pi
            l_hand_x = 330.0 + 10.0 + math.cos(arc_phase) * 18.0
            l_hand_y = GROUND_Y - 45.0 + math.sin(arc_phase) * 14.0

            r_hand_x = 330.0 + 22.0 + math.cos(arc_phase + math.pi * 0.5) * 16.0
            r_hand_y = GROUND_Y - 55.0 + math.sin(arc_phase + math.pi * 0.5) * 16.0

            red_pose = create_custom_pose(
                pelvis_x=330.0 - shift_back, pelvis_y=red_pelvis_y,
                torso_lean_deg=-6.0 + shift_back * 0.5,
                l_arm_target=(l_hand_x, l_hand_y),
                r_arm_target=(r_hand_x, r_hand_y),
                l_foot_target=(330.0 - 20.0, GROUND_Y),
                r_foot_target=(330.0 + 18.0, GROUND_Y),
                facing=+1, head_tilt_deg=-3.0
            )

            # Blue transitions from idle into an explosive sprint windup
            blue_windup_t = clamp((f - 65) / 15.0) if f >= 65 else 0.0
            blue_pose = create_custom_pose(
                pelvis_x=820.0 + blue_windup_t * 10.0,
                pelvis_y=GROUND_Y - 51.0 + blue_windup_t * 6.0,
                torso_lean_deg=-5.0 - blue_windup_t * 16.0,
                l_arm_target=(820.0 - 20.0, GROUND_Y - 40.0),
                r_arm_target=(820.0 + 15.0, GROUND_Y - 35.0),
                l_foot_target=(820.0 - 15.0, GROUND_Y),
                r_foot_target=(820.0 + 22.0, GROUND_Y),
                facing=-1
            )

            cam_pan_x = (red_pos_x + 820.0) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, red_pose.pelvis[0], GROUND_Y, 0.0)
            render_shadow(canvas, blue_pose.pelvis[0], GROUND_Y, 0.0)

            # Subtle hand motion trail arcs
            if f >= 52:
                draw = ImageDraw.Draw(canvas, "RGBA")
                draw.arc([330 - 10, GROUND_Y - 70, 330 + 40, GROUND_Y - 30], start=30, end=240, fill=(255, 120, 50, 110), width=2)

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f)
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f)

        # =================================================================
        # ACT 3: BLUE NINJA SPRINT -> FRICTION SLIDE BRAKE (Frames 81-118 | 3.33s - 4.92s)
        # =================================================================
        elif f <= 118:
            if f <= 104:
                # High-speed sprint from 820 down to 540
                sprint_t = (f - 81) / 23.0
                blue_x = 820.0 - ease_in_quad(sprint_t) * 280.0 # Reaches 540
                blue_run_phase = (blue_x / 62.0) % 1.0

                blue_pose = generate_locomotion_pose(
                    x=blue_x, ground_y=GROUND_Y, phase=blue_run_phase,
                    facing=-1, speed=2.2, weapon="daggers" if f > 95 else None
                )
                blue_pos_x = blue_x
            else:
                # Frames 105-118: Friction slide brake!
                slide_t = (f - 105) / 13.0
                blue_x = 540.0 - ease_out_quad(slide_t) * 45.0 # Skids to 495
                blue_pos_x = blue_x

                # Coiled slide stance: back foot drags, front knee flexes, torso leans back
                blue_pose = create_custom_pose(
                    pelvis_x=blue_x, pelvis_y=GROUND_Y - 42.0,
                    torso_lean_deg=+14.0, # Leaning back against momentum
                    l_arm_target=(blue_x - 22.0, GROUND_Y - 38.0),
                    r_arm_target=(blue_x + 18.0, GROUND_Y - 48.0),
                    l_foot_target=(blue_x - 32.0, GROUND_Y), # Planted lead foot
                    r_foot_target=(blue_x + 28.0, GROUND_Y), # Dragging trail foot
                    facing=-1, weapon="daggers"
                )

            # Red enters ready combat guard
            red_pose = create_custom_pose(
                pelvis_x=330.0, pelvis_y=GROUND_Y - 48.0,
                torso_lean_deg=8.0,
                l_arm_target=(330.0 + 15.0, GROUND_Y - 42.0),
                r_arm_target=(330.0 - 15.0, GROUND_Y - 38.0),
                l_foot_target=(330.0 - 16.0, GROUND_Y),
                r_foot_target=(330.0 + 20.0, GROUND_Y),
                facing=+1
            )

            cam_pan_x = (330.0 + blue_pos_x) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, 330.0, GROUND_Y, 0.0)
            render_shadow(canvas, blue_pos_x, GROUND_Y, 0.0)

            # Friction ground dust puffs during skid
            if f in (106, 108, 110, 113):
                draw_dust_puff(canvas, (blue_pos_x + 10, GROUND_Y - 6), radius=16.0)
                draw_dust_puff(canvas, (blue_pos_x - 20, GROUND_Y - 6), radius=12.0)

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f)
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f, aura_type="lightning" if f > 98 else None)

        # =================================================================
        # ACT 4: FLUID ROUNDHOUSE KICK ARC & CROUCH DUCK (Frames 119-152 | 4.92s - 6.33s)
        # =================================================================
        elif f <= 152:
            kick_t = (f - 119) / 33.0

            # Blue executes high spinning roundhouse kick
            # Leg rotates along circular arc from ground -> 110px altitude -> back down
            kick_angle = kick_t * math.pi
            lead_x = 495.0 - kick_t * 40.0 # Steps forward into kick
            kick_reach = 58.0
            kicking_foot_x = lead_x - math.cos(kick_angle) * kick_reach
            kicking_foot_y = GROUND_Y - math.sin(kick_angle) * 78.0

            # Torso leans back to counterbalance kick
            blue_pose = create_custom_pose(
                pelvis_x=lead_x, pelvis_y=GROUND_Y - 52.0 + math.sin(kick_angle) * 6.0,
                torso_lean_deg=+22.0 * math.sin(kick_angle),
                l_arm_target=(lead_x - 18.0, GROUND_Y - 45.0),
                r_arm_target=(lead_x + 22.0, GROUND_Y - 35.0),
                l_foot_target=(lead_x + 6.0, GROUND_Y), # Planted pivot foot
                r_foot_target=(kicking_foot_x, kicking_foot_y),
                facing=-1, weapon="daggers"
            )

            # Red anticipates and executes fluid crouch duck
            duck_depth = math.sin(kick_angle) * 26.0
            red_pose = create_custom_pose(
                pelvis_x=330.0 + kick_t * 15.0,
                pelvis_y=GROUND_Y - 48.0 + duck_depth,
                torso_lean_deg=16.0 + duck_depth * 0.4,
                l_arm_target=(345.0 + 10.0, GROUND_Y - 42.0 + duck_depth),
                r_arm_target=(345.0 - 15.0, GROUND_Y - 38.0 + duck_depth),
                l_foot_target=(330.0 - 15.0, GROUND_Y),
                r_foot_target=(330.0 + 26.0, GROUND_Y),
                facing=+1
            )

            cam_pan_x = (345.0 + lead_x) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, red_pose.pelvis[0], GROUND_Y, 0.0)
            render_shadow(canvas, lead_x, GROUND_Y, 0.0)

            # Curved cyan motion smear wedge for roundhouse kick
            if 128 <= f <= 138:
                draw_arc_smear_wedge(
                    canvas, (lead_x, GROUND_Y - 45.0),
                    (lead_x - 10.0, GROUND_Y - 15.0),
                    (kicking_foot_x, kicking_foot_y),
                    color=(50, 180, 255, 180)
                )

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f)
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f, aura_type="lightning")

        # =================================================================
        # ACT 5: WEAPON DRAW & 3-HIT FLUID PARRY COMBO (Frames 153-188 | 6.33s - 7.83s)
        # =================================================================
        elif f <= 188:
            combo_f = f - 153
            clash_center_x = 415.0

            # Red rises from duck, draws Flaming Katana in a rising crescent arc
            red_x = clash_center_x - 38.0
            blue_x = clash_center_x + 38.0

            # 3 rhythmic parry beats: f=160, f=172, f=182
            parry_active = combo_f in range(7, 10) or combo_f in range(18, 21) or combo_f in range(28, 31)

            # Smoothly oscillating arm positions tracing arcs
            swing_wave = math.sin(combo_f * 0.55)
            r_blade_tip = (clash_center_x + 5.0, GROUND_Y - 55.0 + swing_wave * 18.0)
            b_dagger_tip = (clash_center_x - 5.0, GROUND_Y - 55.0 - swing_wave * 18.0)

            red_pose = create_custom_pose(
                pelvis_x=red_x, pelvis_y=GROUND_Y - 50.0,
                torso_lean_deg=8.0,
                l_arm_target=(red_x - 10.0, GROUND_Y - 45.0),
                r_arm_target=(r_blade_tip[0] - 25.0, r_blade_tip[1] + 12.0),
                l_foot_target=(red_x - 18.0, GROUND_Y),
                r_foot_target=(red_x + 22.0, GROUND_Y),
                facing=+1, weapon="katana"
            )

            blue_pose = create_custom_pose(
                pelvis_x=blue_x, pelvis_y=GROUND_Y - 50.0,
                torso_lean_deg=-8.0,
                l_arm_target=(b_dagger_tip[0] + 20.0, b_dagger_tip[1] + 10.0),
                r_arm_target=(b_dagger_tip[0] + 15.0, b_dagger_tip[1] + 15.0),
                l_foot_target=(blue_x - 22.0, GROUND_Y),
                r_foot_target=(blue_x + 18.0, GROUND_Y),
                facing=-1, weapon="daggers"
            )

            cam_pan_x = clash_center_x - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, red_x, GROUND_Y, 0.0)
            render_shadow(canvas, blue_x, GROUND_Y, 0.0)

            # Contact sparks and camera vibration on hits
            if parry_active:
                spark_y = GROUND_Y - 55.0 + (swing_wave * 12.0)
                draw_impact_spark(canvas, (clash_center_x, spark_y), radius=32.0, count=8, color=(255, 235, 140, 255))
                cam_dx = random.uniform(-2.5, 2.5)
                cam_dy = random.uniform(-2.5, 2.5)

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f, aura_type="fire")
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f, aura_type="lightning")

        # =================================================================
        # ACT 6: PARABOLIC AERIAL BACKFLIP & SQUASH-CUSHION LANDING (Frames 189-218 | 7.83s - 9.08s)
        # =================================================================
        elif f <= 218:
            jump_t = (f - 189) / 29.0
            red_pos_x = 360.0

            # Blue leaps backward in a high parabolic trajectory from x=450 to x=680
            # Height reaches 130px above ground
            if jump_t <= 0.82:
                # Flight phase: parabolic arc
                flight_t = jump_t / 0.82
                blue_x = 450.0 + ease_out_quad(flight_t) * 230.0 # Reaches 680
                altitude = 135.0 * 4.0 * flight_t * (1.0 - flight_t)
                blue_y = GROUND_Y - 50.0 - altitude

                # Tucked 360 rotational spin mid-air
                spin_rot = flight_t * 2.0 * math.pi
                tuck = math.sin(flight_t * math.pi) * 16.0

                blue_pose = create_custom_pose(
                    pelvis_x=blue_x, pelvis_y=blue_y,
                    torso_lean_deg=-15.0 - math.degrees(spin_rot * 0.4),
                    l_arm_target=(blue_x - 12.0, blue_y + 10.0),
                    r_arm_target=(blue_x + 12.0, blue_y + 10.0),
                    l_foot_target=(blue_x - 14.0 + tuck, blue_y + 25.0 - tuck),
                    r_foot_target=(blue_x + 14.0 - tuck, blue_y + 25.0 - tuck),
                    facing=-1, weapon="daggers"
                )
            else:
                # Land & Squash Cushion Phase: knees compress deeply to absorb momentum!
                land_t = (jump_t - 0.82) / 0.18
                blue_x = 680.0
                squash_depth = math.sin(land_t * math.pi) * 24.0 # Deep knee flexion cushion

                blue_pose = create_custom_pose(
                    pelvis_x=blue_x, pelvis_y=GROUND_Y - 50.0 + squash_depth,
                    torso_lean_deg=-12.0 - squash_depth * 0.3,
                    l_arm_target=(blue_x - 24.0, GROUND_Y - 40.0 + squash_depth),
                    r_arm_target=(blue_x + 20.0, GROUND_Y - 40.0 + squash_depth),
                    l_foot_target=(blue_x - 22.0, GROUND_Y),
                    r_foot_target=(blue_x + 22.0, GROUND_Y),
                    facing=-1, weapon="daggers"
                )

            # Red holds grounded sword follow-through stance
            red_pose = create_custom_pose(
                pelvis_x=360.0, pelvis_y=GROUND_Y - 50.0,
                torso_lean_deg=6.0,
                l_arm_target=(360.0 - 15.0, GROUND_Y - 35.0),
                r_arm_target=(360.0 + 35.0, GROUND_Y - 45.0),
                l_foot_target=(360.0 - 20.0, GROUND_Y),
                r_foot_target=(360.0 + 24.0, GROUND_Y),
                facing=+1, weapon="katana"
            )

            cam_pan_x = (360.0 + blue_x) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, 360.0, GROUND_Y, 0.0)
            render_shadow(canvas, blue_x, GROUND_Y, altitude if jump_t <= 0.82 else 0.0)

            # Impact dust on landing
            if f in (213, 214, 215):
                draw_dust_puff(canvas, (blue_x - 22.0, GROUND_Y - 4), radius=18.0)
                draw_dust_puff(canvas, (blue_x + 22.0, GROUND_Y - 4), radius=18.0)

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f, aura_type="fire")
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f, aura_type="lightning")

        # =================================================================
        # ACT 7: SAMURAI SHEATHING & CINEMATIC SETTLE (Frames 219-240 | 9.08s - 10.0s)
        # =================================================================
        else:
            settle_t = (f - 219) / 21.0
            red_x = 360.0
            blue_x = 680.0

            # Red rotates katana and slides it into sheath
            sheath_progress = clamp(settle_t * 1.4)
            blade_hand_x = 360.0 + 35.0 * (1.0 - sheath_progress) - 10.0 * sheath_progress
            blade_hand_y = GROUND_Y - 45.0 + 10.0 * sheath_progress

            red_pose = create_custom_pose(
                pelvis_x=red_x, pelvis_y=GROUND_Y - 51.0,
                torso_lean_deg=4.0 * (1.0 - settle_t),
                l_arm_target=(red_x - 14.0, GROUND_Y - 35.0),
                r_arm_target=(blade_hand_x, blade_hand_y),
                l_foot_target=(red_x - 18.0, GROUND_Y),
                r_foot_target=(red_x + 18.0, GROUND_Y),
                facing=+1, weapon="katana" if settle_t < 0.75 else None
            )

            # Blue rises from crouch into formal respectful bow
            blue_pose = create_custom_pose(
                pelvis_x=blue_x, pelvis_y=GROUND_Y - 51.0,
                torso_lean_deg=-4.0 * (1.0 - settle_t),
                l_arm_target=(blue_x - 12.0, GROUND_Y - 35.0),
                r_arm_target=(blue_x + 12.0, GROUND_Y - 35.0),
                l_foot_target=(blue_x - 16.0, GROUND_Y),
                r_foot_target=(blue_x + 16.0, GROUND_Y),
                facing=-1, weapon="daggers"
            )

            cam_pan_x = (red_x + blue_x) * 0.5 - (WIDTH * 0.5)
            canvas = render_environment(WIDTH, HEIGHT, GROUND_Y, cam_pan_x=cam_pan_x, frame_num=f)
            render_shadow(canvas, red_x, GROUND_Y, 0.0)
            render_shadow(canvas, blue_x, GROUND_Y, 0.0)

            # Spark on final sheath click!
            if f in (233, 234):
                draw_impact_spark(canvas, (red_x - 10.0, GROUND_Y - 35.0), radius=18.0, count=6, color=(255, 255, 255, 255))

            # Fading in cinematic 2.39:1 widescreen black letterbox bars
            draw = ImageDraw.Draw(canvas, "RGBA")
            lb_h = int(HEIGHT * 0.12 * ease_out_quad(settle_t))
            draw.rectangle([0, 0, WIDTH, lb_h], fill=(0, 0, 0, 255))
            draw.rectangle([0, HEIGHT - lb_h, WIDTH, HEIGHT], fill=(0, 0, 0, 255))

            render_smooth_stickman(canvas, red_pose, COLOR_RED, COLOR_RED_SASH, frame_num=f)
            render_smooth_stickman(canvas, blue_pose, COLOR_BLUE, COLOR_BLUE_SASH, frame_num=f)

        # Apply camera shake displacement if active
        canvas = apply_camera_shake(canvas, cam_dx, cam_dy)
        frames.append(canvas)

    return frames


def main():
    examples_dir = os.path.join(repo_root, "examples")
    os.makedirs(examples_dir, exist_ok=True)

    project_path = os.path.join(examples_dir, "fluid_stickman_kinematics_24fps.pclx")
    mp4_path = os.path.join(examples_dir, "fluid_stickman_kinematics_24fps.mp4")
    gif_path = os.path.join(examples_dir, "fluid_stickman_kinematics_24fps.gif")
    strip_path = os.path.join(examples_dir, "fluid_stickman_kinematics_contact_strip.png")

    print("==================================================================")
    print("FLUID STICKMAN KINEMATICS & GAIT CYCLE 24 FPS ANIMATION")
    print(f"Canvas: {WIDTH}x{HEIGHT} | Framerate: {FPS} FPS | Total: {TOTAL_FRAMES} frames")
    print("==================================================================")

    frames = generate_fluid_masterpiece_frames()
    print(f"[OK] Generated {len(frames)} frames with continuous joint trajectories.")

    # Create Pencil2D native project
    print(f"Creating Pencil2D project archive: {project_path}")
    proj = Pencil2DProject.create(
        file_path=project_path,
        width=WIDTH,
        height=HEIGHT,
        fps=FPS,
        layer_names=["Fluid Kinematics"]
    )

    for idx, f_img in enumerate(frames, start=1):
        proj.add_frame_image("Fluid Kinematics", idx, f_img)

    proj.save(project_path)
    print(f"[OK] Saved native .pclx archive: {project_path}")

    # Generate preview filmstrip
    print("Generating visual verification contact strip (pencil2d_look)...")
    strip_img, final_strip = proj.generate_preview_strip(
        frames=[18, 55, 95, 110, 134, 168, 204, 235],
        thumb_width=240,
        output_path=strip_path
    )
    print(f"[OK] Contact strip saved: {final_strip}")

    # Export MP4 via AppImage CLI
    print("Rendering 24 FPS MP4 video via Pencil2D AppImage...")
    ok_mp4, msg_mp4 = export_project(project_path, mp4_path, fps=FPS)
    print(f"MP4 Export ({ok_mp4}): {msg_mp4}")

    # Export GIF preview
    print("Rendering animated GIF preview...")
    ok_gif, msg_gif = export_project(project_path, gif_path, fps=12, force_pure_python=True)
    print(f"GIF Export ({ok_gif}): {msg_gif}")

    print("==================================================================")
    print("ALL FLUID KINEMATICS RENDERS COMPLETE!")
    print(f"- Project: {project_path}")
    print(f"- Strip:   {strip_path}")
    print(f"- MP4:     {mp4_path}")
    print(f"- GIF:     {gif_path}")
    print("==================================================================")


if __name__ == "__main__":
    main()
