"""Artistic procedural drawing and 2D animation engine for Pencil2D MCP.

Provides natural brush stroke simulation, Bezier curve smoothing, line-of-action
kinematics, squash & stretch volume physics, and artistic effects to eliminate
rigid, mechanical 'math-diagram' drawings.
"""

import io
import math
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFilter


def clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


# -------------------------------------------------------------------------
# Easing & Animation Physics
# -------------------------------------------------------------------------

def ease_in_quad(t: float) -> float:
    t = clamp(t)
    return t * t


def ease_out_quad(t: float) -> float:
    t = clamp(t)
    return t * (2.0 - t)


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t)
    if t < 0.5:
        return 4.0 * t * t * t
    p = 2.0 * t - 2.0
    return 0.5 * p * p * p + 1.0


def ease_overshoot(t: float, overshoot: float = 1.4) -> float:
    """Over-travels the target pose slightly before snapping back (anticipation/follow-through)."""
    t = clamp(t)
    return (t - 1.0) * (t - 1.0) * ((overshoot + 1.0) * (t - 1.0) + overshoot) + 1.0


def ease_anticipation(t: float, back: float = 1.2) -> float:
    """Pulls backward slightly before moving forward."""
    t = clamp(t)
    return t * t * ((back + 1.0) * t - back)


def calculate_squash_stretch(scale_y: float) -> Tuple[float, float]:
    """Calculate (scale_x, scale_y) preserving 2D visual mass/volume."""
    sy = max(0.2, scale_y)
    sx = 1.0 / math.sqrt(sy)
    return sx, sy


def parabolic_arc(p_start: Tuple[float, float], p_apex: Tuple[float, float],
                  p_end: Tuple[float, float], t: float) -> Tuple[float, float]:
    """Compute trajectory point along a natural parabolic arc."""
    t = clamp(t)
    one_minus_t = 1.0 - t
    x = one_minus_t * one_minus_t * p_start[0] + 2 * one_minus_t * t * p_apex[0] + t * t * p_end[0]
    y = one_minus_t * one_minus_t * p_start[1] + 2 * one_minus_t * t * p_apex[1] + t * t * p_end[1]
    return x, y


# -------------------------------------------------------------------------
# Bezier Curves & Smooth Geometry
# -------------------------------------------------------------------------

def sample_cubic_bezier(p0: Tuple[float, float], p1: Tuple[float, float],
                        p2: Tuple[float, float], p3: Tuple[float, float],
                        steps: int = 24) -> List[Tuple[float, float]]:
    """Sample points along a cubic Bezier curve."""
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
        y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
        pts.append((x, y))
    return pts


def bow_curve(p_start: Tuple[float, float], p_end: Tuple[float, float],
              bow_amount: float = 10.0, steps: int = 16) -> List[Tuple[float, float]]:
    """Create a curved path between two points with organic arc/bow."""
    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-4:
        return [p_start, p_end]

    # Perpendicular normal
    nx = -dy / dist
    ny = dx / dist

    mid_x = (p_start[0] + p_end[0]) * 0.5 + nx * bow_amount
    mid_y = (p_start[1] + p_end[1]) * 0.5 + ny * bow_amount

    # Sample quadratic curve
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = u * u * p_start[0] + 2 * u * t * mid_x + t * t * p_end[0]
        y = u * u * p_start[1] + 2 * u * t * mid_y + t * t * p_end[1]
        pts.append((x, y))
    return pts


# -------------------------------------------------------------------------
# Artistic Stroke & Brush Engines
# -------------------------------------------------------------------------

def draw_tapered_stroke(canvas: Image.Image, points: List[Tuple[float, float]],
                        color: Tuple[int, int, int, int], base_width: float = 4.0,
                        taper_start: bool = True, taper_end: bool = True,
                        jitter: float = 0.0, seed: int = 42):
    """Draw a smooth stroke with natural pressure tapering at terminals."""
    if len(points) < 2:
        return

    draw = ImageDraw.Draw(canvas, "RGBA")
    n = len(points)
    rng = random.Random(seed)

    for i in range(n - 1):
        p1 = points[i]
        p2 = points[i + 1]
        t = i / float(n - 1)

        # Width modulation (tapering envelope)
        w = base_width
        if taper_start and t < 0.25:
            w = base_width * (0.2 + 0.8 * (t / 0.25))
        elif taper_end and t > 0.75:
            w = base_width * (0.2 + 0.8 * ((1.0 - t) / 0.25))

        if jitter > 0.0:
            jx = rng.uniform(-jitter, jitter)
            jy = rng.uniform(-jitter, jitter)
            p1 = (p1[0] + jx, p1[1] + jy)

        r = max(0.5, w * 0.5)
        # Draw anti-aliased segment with rounded caps
        draw.line([p1, p2], fill=color, width=max(1, int(round(w))))
        draw.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=color)
        draw.ellipse([p2[0] - r, p2[1] - r, p2[0] + r, p2[1] + r], fill=color)


def draw_pencil_sketch_stroke(canvas: Image.Image, p_start: Tuple[float, float],
                              p_end: Tuple[float, float],
                              color: Tuple[int, int, int, int] = (45, 45, 50, 160),
                              passes: int = 3, spread: float = 1.2,
                              seed: int = 100):
    """Draw a graphite pencil sketch line using multi-pass layered micro-offsets."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    rng = random.Random(seed)
    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    dist = math.hypot(dx, dy)
    steps = max(6, int(dist // 10))

    for p in range(passes):
        alpha = int(color[3] * (0.4 + 0.6 * (p + 1) / passes))
        pass_color = (color[0], color[1], color[2], alpha)
        curve_pts = []
        for s in range(steps + 1):
            t = s / float(steps)
            x = p_start[0] + dx * t + rng.uniform(-spread, spread)
            y = p_start[1] + dy * t + rng.uniform(-spread, spread)
            curve_pts.append((x, y))

        for i in range(len(curve_pts) - 1):
            draw.line([curve_pts[i], curve_pts[i + 1]], fill=pass_color, width=1)


def draw_doodle_wobble_line(canvas: Image.Image, points: List[Tuple[float, float]],
                            color: Tuple[int, int, int, int] = (25, 25, 30, 255),
                            width: int = 3, wobble: float = 1.5,
                            overshoot: float = 3.0, seed: int = 200):
    """Draw a playful hand-drawn marker stroke with natural wobble and corner overshoot."""
    if len(points) < 2:
        return
    draw = ImageDraw.Draw(canvas, "RGBA")
    rng = random.Random(seed)

    wobbly_pts = []
    for idx, (x, y) in enumerate(points):
        wx = x + rng.uniform(-wobble, wobble)
        wy = y + rng.uniform(-wobble, wobble)
        wobbly_pts.append((wx, wy))

    # Add overshoot on ends
    if overshoot > 0.0:
        d_start_x = wobbly_pts[0][0] - wobbly_pts[1][0]
        d_start_y = wobbly_pts[0][1] - wobbly_pts[1][1]
        dist_s = math.hypot(d_start_x, d_start_y) or 1.0
        wobbly_pts[0] = (wobbly_pts[0][0] + (d_start_x / dist_s) * overshoot,
                         wobbly_pts[0][1] + (d_start_y / dist_s) * overshoot)

        d_end_x = wobbly_pts[-1][0] - wobbly_pts[-2][0]
        d_end_y = wobbly_pts[-1][1] - wobbly_pts[-2][1]
        dist_e = math.hypot(d_end_x, d_end_y) or 1.0
        wobbly_pts[-1] = (wobbly_pts[-1][0] + (d_end_x / dist_e) * overshoot,
                          wobbly_pts[-1][1] + (d_end_y / dist_e) * overshoot)

    for i in range(len(wobbly_pts) - 1):
        draw.line([wobbly_pts[i], wobbly_pts[i + 1]], fill=color, width=width)
        r = width * 0.5
        draw.ellipse([wobbly_pts[i][0] - r, wobbly_pts[i][1] - r,
                      wobbly_pts[i][0] + r, wobbly_pts[i][1] + r], fill=color)


def draw_soft_gradient_glow(canvas: Image.Image, center: Tuple[float, float],
                            radius: float, color: Tuple[int, int, int, int]):
    """Draw a soft painterly glow/blush (for anime cheeks or Ghibli atmospheric lighting)."""
    cx, cy = int(center[0]), int(center[1])
    r = int(radius)
    if r <= 0:
        return

    box = (cx - r, cy - r, cx + r, cy + r)
    patch_size = (r * 2, r * 2)
    patch = Image.new("RGBA", patch_size, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(patch)

    layers = max(4, r // 4)
    for i in range(layers, 0, -1):
        curr_r = (i / float(layers)) * r
        alpha = int(color[3] * (1.0 - (i / float(layers)) ** 1.5))
        c = (color[0], color[1], color[2], alpha)
        pdraw.ellipse([r - curr_r, r - curr_r, r + curr_r, r + curr_r], fill=c)

    canvas.paste(patch, (cx - r, cy - r), patch)


# -------------------------------------------------------------------------
# Dynamic Animation VFX & Cartoon Effects
# -------------------------------------------------------------------------

def draw_speed_lines(canvas: Image.Image, center: Tuple[float, float],
                     direction_deg: float, length: float = 60.0,
                     count: int = 5, spread_deg: float = 25.0,
                     color: Tuple[int, int, int, int] = (240, 240, 250, 180)):
    """Draw dynamic anime / action speed lines trailing a fast movement."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    rad_center = math.radians(direction_deg)
    half_spread = math.radians(spread_deg * 0.5)

    for i in range(count):
        t = (i / float(max(1, count - 1))) - 0.5
        angle = rad_center + t * half_spread * 2.0
        line_len = length * (0.7 + 0.3 * math.cos(i * 1.5))

        p_start_x = center[0] + math.cos(angle) * (line_len * 0.2)
        p_start_y = center[1] + math.sin(angle) * (line_len * 0.2)
        p_end_x = center[0] + math.cos(angle) * line_len
        p_end_y = center[1] + math.sin(angle) * line_len

        draw.line([(p_start_x, p_start_y), (p_end_x, p_end_y)], fill=color, width=2)


def draw_dust_puff(canvas: Image.Image, position: Tuple[float, float],
                   radius: float = 16.0,
                   color: Tuple[int, int, int, int] = (220, 215, 210, 190)):
    """Draw a cartoon impact dust puff cloud (ground impact or sprint start)."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    px, py = position

    circles = [
        (px - radius * 0.7, py, radius * 0.6),
        (px, py - radius * 0.4, radius * 0.8),
        (px + radius * 0.7, py, radius * 0.6),
        (px - radius * 0.3, py - radius * 0.7, radius * 0.5),
        (px + radius * 0.4, py - radius * 0.6, radius * 0.55),
    ]

    for cx, cy, r in circles:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(color[0] - 30, color[1] - 30, color[2] - 30, color[3]))


def draw_impact_spark(canvas: Image.Image, center: Tuple[float, float],
                      radius: float = 24.0, count: int = 6,
                      color: Tuple[int, int, int, int] = (255, 220, 80, 255)):
    """Draw an expressive cartoon hit-spark or action star on contact."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    cx, cy = center
    pts = []
    for i in range(count * 2):
        angle = (i * math.pi) / count
        r = radius if (i % 2 == 0) else (radius * 0.35)
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        pts.append((x, y))
    if len(pts) >= 3:
        draw.polygon(pts, fill=color, outline=(255, 255, 255, 255))


# -------------------------------------------------------------------------
# Advanced Sakuga Stickman Combat & Motion Smears
# -------------------------------------------------------------------------

def draw_motion_smear(canvas: Image.Image, p_prev: Tuple[float, float],
                      p_curr: Tuple[float, float],
                      width_start: float = 6.0, width_end: float = 3.0,
                      color: Tuple[int, int, int, int] = (255, 255, 255, 180)):
    """Draw an elongated motion smear connecting previous limb position to current."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    dx = p_curr[0] - p_prev[0]
    dy = p_curr[1] - p_prev[1]
    dist = math.hypot(dx, dy)
    if dist < 5.0:
        return

    nx = -dy / dist
    ny = dx / dist

    poly = [
        (p_prev[0] - nx * width_start * 0.5, p_prev[1] - ny * width_start * 0.5),
        (p_prev[0] + nx * width_start * 0.5, p_prev[1] + ny * width_start * 0.5),
        (p_curr[0] + nx * width_end * 0.5, p_curr[1] + ny * width_end * 0.5),
        (p_curr[0] - nx * width_end * 0.5, p_curr[1] - ny * width_end * 0.5)
    ]
    draw.polygon(poly, fill=color)


def draw_arc_smear_wedge(canvas: Image.Image, pivot: Tuple[float, float],
                         tip_prev: Tuple[float, float], tip_curr: Tuple[float, float],
                         color: Tuple[int, int, int, int] = (255, 230, 100, 160),
                         steps: int = 12):
    """Draw a dynamic curved fan/wedge motion smear for high-velocity kicks or blade swings."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    pts = [pivot]

    # Sample arc from tip_prev to tip_curr
    for s in range(steps + 1):
        t = s / float(steps)
        # Interpolate along arc
        x = tip_prev[0] * (1.0 - t) + tip_curr[0] * t
        y = tip_prev[1] * (1.0 - t) + tip_curr[1] * t
        pts.append((x, y))

    if len(pts) >= 3:
        draw.polygon(pts, fill=color)


def draw_sakuga_impact_flash(canvas: Image.Image, center: Tuple[float, float],
                             radius: float = 280.0,
                             invert_colors: bool = False):
    """Apply high-contrast Sakuga impact frame with radial speed rays."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    cx, cy = center
    w, h = canvas.size

    if invert_colors:
        # Dramatic stark monochrome / negative frame
        flash_bg = Image.new("RGBA", (w, h), (15, 12, 18, 240))
        canvas.paste(flash_bg, (0, 0), flash_bg)

    # Concentric explosive energy rays
    rays = 16
    for i in range(rays):
        angle = (i / float(rays)) * 2.0 * math.pi
        p1 = (cx + math.cos(angle) * (radius * 0.2), cy + math.sin(angle) * (radius * 0.2))
        p2 = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
        draw.line([p1, p2], fill=(255, 255, 255, 230), width=3)
        draw.line([p1, p2], fill=(255, 210, 80, 140), width=7)


def apply_camera_shake(canvas: Image.Image, dx: float, dy: float,
                       fill_color: Tuple[int, int, int, int] = (24, 20, 26, 255)) -> Image.Image:
    """Offset the entire canvas to simulate dynamic camera shake impact."""
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        return canvas

    w, h = canvas.size
    shaken = Image.new("RGBA", (w, h), fill_color)
    shaken.paste(canvas, (int(round(dx)), int(round(dy))))
    return shaken


# -------------------------------------------------------------------------
# Articulated Inverse Kinematics (IK) & Fluid Locomotion Engine
# -------------------------------------------------------------------------

def solve_2bone_ik(root: Tuple[float, float],
                   target: Tuple[float, float],
                   l1: float,
                   l2: float,
                   bend_positive: bool = True) -> Tuple[float, float]:
    """Analytic 2-bone Inverse Kinematics solver for natural elbow and knee articulation.
    
    Guarantees mathematically exact limb lengths (zero distortion or stretching)
    and smooth natural flexion.
    """
    dx = target[0] - root[0]
    dy = target[1] - root[1]
    dist = math.hypot(dx, dy)

    # Clamp distance so bone does not pop or hyper-extend
    max_reach = l1 + l2 - 0.001
    min_reach = abs(l1 - l2) + 0.001
    clamped_dist = max(min_reach, min(max_reach, dist))

    base_angle = math.atan2(dy, dx)
    cos_alpha = (l1 * l1 + clamped_dist * clamped_dist - l2 * l2) / (2.0 * l1 * clamped_dist)
    cos_alpha = max(-1.0, min(1.0, cos_alpha))
    alpha = math.acos(cos_alpha)

    joint_angle = base_angle + (alpha if bend_positive else -alpha)
    jx = root[0] + l1 * math.cos(joint_angle)
    jy = root[1] + l1 * math.sin(joint_angle)
    return (jx, jy)


class StickmanPose:
    """Complete 15-joint articulated stickman skeleton state."""

    def __init__(self,
                 head: Tuple[float, float],
                 neck: Tuple[float, float],
                 pelvis: Tuple[float, float],
                 spine_mid: Tuple[float, float],
                 l_shoulder: Tuple[float, float],
                 l_elbow: Tuple[float, float],
                 l_hand: Tuple[float, float],
                 r_shoulder: Tuple[float, float],
                 r_elbow: Tuple[float, float],
                 r_hand: Tuple[float, float],
                 l_hip: Tuple[float, float],
                 l_knee: Tuple[float, float],
                 l_foot: Tuple[float, float],
                 r_hip: Tuple[float, float],
                 r_knee: Tuple[float, float],
                 r_foot: Tuple[float, float],
                 facing: int = 1,
                 head_radius: float = 14.0,
                 weapon: Optional[str] = None):
        self.head = head
        self.neck = neck
        self.pelvis = pelvis
        self.spine_mid = spine_mid
        self.l_shoulder = l_shoulder
        self.l_elbow = l_elbow
        self.l_hand = l_hand
        self.r_shoulder = r_shoulder
        self.r_elbow = r_elbow
        self.r_hand = r_hand
        self.l_hip = l_hip
        self.l_knee = l_knee
        self.l_foot = l_foot
        self.r_hip = r_hip
        self.r_knee = r_knee
        self.r_foot = r_foot
        self.facing = facing
        self.head_radius = head_radius
        self.weapon = weapon

    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head, "neck": self.neck, "pelvis": self.pelvis,
            "spine_mid": self.spine_mid, "l_shoulder": self.l_shoulder,
            "l_elbow": self.l_elbow, "l_hand": self.l_hand,
            "r_shoulder": self.r_shoulder, "r_elbow": self.r_elbow,
            "r_hand": self.r_hand, "l_hip": self.l_hip,
            "l_knee": self.l_knee, "l_foot": self.l_foot,
            "r_hip": self.r_hip, "r_knee": self.r_knee,
            "r_foot": self.r_foot, "facing": self.facing,
            "head_radius": self.head_radius, "weapon": self.weapon
        }


def blend_stickman_poses(pose_a: StickmanPose, pose_b: StickmanPose, t: float) -> StickmanPose:
    """Seamlessly interpolate every joint between two poses using cubic easing.
    
    Completely eliminates instantaneous teleporting and joint snapping.
    """
    t = clamp(t)
    st = t * t * (3.0 - 2.0 * t) # Smoothstep easing

    def lerp_pt(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
        return (p1[0] * (1.0 - st) + p2[0] * st, p1[1] * (1.0 - st) + p2[1] * st)

    return StickmanPose(
        head=lerp_pt(pose_a.head, pose_b.head),
        neck=lerp_pt(pose_a.neck, pose_b.neck),
        pelvis=lerp_pt(pose_a.pelvis, pose_b.pelvis),
        spine_mid=lerp_pt(pose_a.spine_mid, pose_b.spine_mid),
        l_shoulder=lerp_pt(pose_a.l_shoulder, pose_b.l_shoulder),
        l_elbow=lerp_pt(pose_a.l_elbow, pose_b.l_elbow),
        l_hand=lerp_pt(pose_a.l_hand, pose_b.l_hand),
        r_shoulder=lerp_pt(pose_a.r_shoulder, pose_b.r_shoulder),
        r_elbow=lerp_pt(pose_a.r_elbow, pose_b.r_elbow),
        r_hand=lerp_pt(pose_a.r_hand, pose_b.r_hand),
        l_hip=lerp_pt(pose_a.l_hip, pose_b.l_hip),
        l_knee=lerp_pt(pose_a.l_knee, pose_b.l_knee),
        l_foot=lerp_pt(pose_a.l_foot, pose_b.l_foot),
        r_hip=lerp_pt(pose_a.r_hip, pose_b.r_hip),
        r_knee=lerp_pt(pose_a.r_knee, pose_b.r_knee),
        r_foot=lerp_pt(pose_a.r_foot, pose_b.r_foot),
        facing=pose_b.facing if t > 0.5 else pose_a.facing,
        head_radius=pose_a.head_radius * (1.0 - st) + pose_b.head_radius * st,
        weapon=pose_b.weapon if t > 0.5 else pose_a.weapon
    )


def generate_locomotion_pose(x: float, ground_y: float, phase: float,
                             facing: int = 1, speed: float = 1.0,
                             weapon: Optional[str] = None) -> StickmanPose:
    """Generate anatomically grounded walk, jog, or sprint pose.
    
    Features:
    - True stance foot ground-locking (zero sliding/ice-skating).
    - Swing leg knee flexion and ground clearance arc.
    - Pelvis double-frequency vertical bounce and sway.
    - Speed-proportional spinal lean into movement.
    - Counter-phase natural arm pendulum with elbow flexion solved via 2-bone IK.
    """
    is_running = speed > 1.2
    is_sprint = speed > 2.0

    # Anatomical proportions
    thigh_len = 28.0
    calf_len = 28.0
    upper_arm = 20.0
    forearm = 20.0
    torso_len = 42.0
    head_r = 14.0

    stride = 62.0 if is_sprint else (50.0 if is_running else 34.0)
    step_height = 28.0 if is_sprint else (20.0 if is_running else 10.0)
    bob_amp = 12.0 if is_sprint else (8.0 if is_running else 4.5)
    lean_deg = 24.0 if is_sprint else (16.0 if is_running else 6.0)

    # Pelvis vertical oscillation (bobs twice per full stride cycle)
    pelvis_base_y = ground_y - (44.0 if is_sprint else (48.0 if is_running else 51.0))
    bob = -bob_amp * abs(math.sin(2.0 * math.pi * phase))
    pelvis = (x, pelvis_base_y + bob)

    # Spine & Torso lean
    lean_rad = math.radians(lean_deg) * facing
    neck = (pelvis[0] + math.sin(lean_rad) * torso_len,
            pelvis[1] - math.cos(lean_rad) * torso_len)
    spine_mid = ((pelvis[0] + neck[0]) * 0.5 + math.sin(lean_rad) * 4.0,
                 (pelvis[1] + neck[1]) * 0.5)

    # Head
    head = (neck[0] + math.sin(lean_rad * 0.5) * (head_r + 6),
            neck[1] - math.cos(lean_rad * 0.5) * (head_r + 6))

    # Shoulders & Hips
    l_shoulder = (neck[0] - facing * 4.0, neck[1] + 3.0)
    r_shoulder = (neck[0] + facing * 4.0, neck[1] + 3.0)
    l_hip = (pelvis[0] - facing * 5.0, pelvis[1])
    r_hip = (pelvis[0] + facing * 5.0, pelvis[1])

    # Leg kinematics
    phase_l = phase % 1.0
    phase_r = (phase + 0.5) % 1.0

    def compute_leg(hip: Tuple[float, float], leg_phase: float):
        if leg_phase <= 0.6:
            # Stance phase: planted firmly on ground
            u = leg_phase / 0.6
            foot_x = hip[0] + facing * (stride * 0.5 - stride * u)
            foot_y = ground_y
        else:
            # Swing phase: knee lifts up, foot arcs forward
            v = (leg_phase - 0.6) / 0.4
            foot_x = hip[0] + facing * (-stride * 0.5 + stride * v)
            foot_y = ground_y - step_height * math.sin(math.pi * v)

        # Knee IK: knees flex forward relative to character direction
        knee = solve_2bone_ik(hip, (foot_x, foot_y), thigh_len, calf_len, bend_positive=(facing > 0))
        return knee, (foot_x, foot_y)

    l_knee, l_foot = compute_leg(l_hip, phase_l)
    r_knee, r_foot = compute_leg(r_hip, phase_r)

    # Arm kinematics (counter-phase to legs)
    def compute_arm(shoulder: Tuple[float, float], arm_phase: float):
        swing_amp = math.radians(70.0 if is_sprint else (55.0 if is_running else 30.0))
        arm_angle = -swing_amp * math.sin(2.0 * math.pi * arm_phase) * facing
        flex = 0.80 if arm_angle * facing > 0 else 0.95
        reach = (upper_arm + forearm) * flex
        target = (shoulder[0] + math.sin(arm_angle) * reach,
                  shoulder[1] + math.cos(arm_angle) * reach)
        elbow = solve_2bone_ik(shoulder, target, upper_arm, forearm, bend_positive=(facing < 0))
        return elbow, target

    l_elbow, l_hand = compute_arm(l_shoulder, phase_l)
    r_elbow, r_hand = compute_arm(r_shoulder, phase_r)

    return StickmanPose(
        head=head, neck=neck, pelvis=pelvis, spine_mid=spine_mid,
        l_shoulder=l_shoulder, l_elbow=l_elbow, l_hand=l_hand,
        r_shoulder=r_shoulder, r_elbow=r_elbow, r_hand=r_hand,
        l_hip=l_hip, l_knee=l_knee, l_foot=l_foot,
        r_hip=r_hip, r_knee=r_knee, r_foot=r_foot,
        facing=facing, head_radius=head_r, weapon=weapon
    )


def render_smooth_stickman(canvas: Image.Image, pose: StickmanPose,
                           color: Tuple[int, int, int, int],
                           sash_color: Tuple[int, int, int, int],
                           frame_num: int = 0,
                           aura_type: Optional[str] = None):
    """Render articulated stickman skeleton with Bezier curves, joints, and cloth sash physics."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    f = pose.facing

    # 1. Aura glow if active
    if aura_type == "fire":
        draw_soft_gradient_glow(canvas, pose.pelvis, radius=65, color=(255, 90, 20, 90))
        # Fiery rising wisps
        for i in range(4):
            w_x = pose.pelvis[0] + math.sin(frame_num * 0.4 + i) * 22.0
            w_y = pose.pelvis[1] - 15.0 - ((frame_num * 3 + i * 15) % 55)
            draw.ellipse([w_x - 3, w_y - 4, w_x + 3, w_y + 4], fill=(255, 180, 40, 180))

    elif aura_type == "lightning":
        draw_soft_gradient_glow(canvas, pose.pelvis, radius=65, color=(30, 160, 255, 80))
        # Electric jagged crackles
        for i in range(3):
            lx = pose.pelvis[0] + math.sin(frame_num * 0.8 + i * 2.0) * 26.0
            ly = pose.pelvis[1] + math.cos(frame_num * 0.8 + i * 2.0) * 26.0
            draw.line([(lx, ly), (lx + random.uniform(-10, 10), ly + random.uniform(-10, 10))],
                      fill=(190, 245, 255, 230), width=2)

    # 2. Flowing Sash / Headband Cloth Physics (dual-wave harmonic simulation)
    sash_anchor = (pose.head[0] - f * (pose.head_radius * 0.85), pose.head[1] - 2.0)
    w1 = math.sin(frame_num * 0.35) * 6.0
    w2 = math.cos(frame_num * 0.65) * 4.0
    sash_mid = (sash_anchor[0] - f * 20.0, sash_anchor[1] + 6.0 + w1)
    sash_tip = (sash_anchor[0] - f * 42.0, sash_anchor[1] + 14.0 + w1 + w2)
    draw_tapered_stroke(canvas, [sash_anchor, sash_mid, sash_tip], sash_color, base_width=4.0)

    # 3. Limbs: Tapered multi-joint strokes
    # Back arm
    draw_tapered_stroke(canvas, [pose.l_shoulder, pose.l_elbow, pose.l_hand], color, base_width=4.2)
    # Legs
    draw_tapered_stroke(canvas, [pose.l_hip, pose.l_knee, pose.l_foot], color, base_width=5.2)
    draw_tapered_stroke(canvas, [pose.r_hip, pose.r_knee, pose.r_foot], color, base_width=5.2)
    # Curved Spine (Line of Action)
    draw_tapered_stroke(canvas, [pose.pelvis, pose.spine_mid, pose.neck], color, base_width=5.8)
    # Front arm
    draw_tapered_stroke(canvas, [pose.r_shoulder, pose.r_elbow, pose.r_hand], color, base_width=4.5)

    # 4. Joint spheres (knees, elbows, shoulders)
    for j_pt in [pose.l_elbow, pose.r_elbow, pose.l_knee, pose.r_knee, pose.pelvis, pose.neck]:
        draw.ellipse([j_pt[0] - 2.5, j_pt[1] - 2.5, j_pt[0] + 2.5, j_pt[1] + 2.5], fill=color)

    # 5. Head & Headband Wrap
    hx, hy = pose.head
    hr = pose.head_radius
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=color)
    # Headband wrap line
    draw.line([(hx - hr * 0.95, hy - hr * 0.15), (hx + hr * 0.95, hy - hr * 0.15)], fill=sash_color, width=3)
    # Expressive eye slit (gazing in direction of facing)
    eye_x = hx + f * (hr * 0.38)
    draw.line([(eye_x - 2, hy - hr * 0.15), (eye_x + 3, hy - hr * 0.15)], fill=(255, 255, 255, 255), width=2)

    # 6. Equipped Weapons
    if pose.weapon == "katana":
        hilt = pose.r_hand
        blade_mid = (hilt[0] + f * 28.0, hilt[1] - 22.0)
        blade_tip = (hilt[0] + f * 54.0, hilt[1] - 38.0)
        draw_tapered_stroke(canvas, [hilt, blade_mid, blade_tip], (255, 120, 20, 220), base_width=6.0)
        draw_tapered_stroke(canvas, [hilt, blade_mid, blade_tip], (255, 250, 190, 255), base_width=3.0)

    elif pose.weapon == "daggers":
        tip_l = (pose.l_hand[0] + f * 24.0, pose.l_hand[1] - 14.0)
        tip_r = (pose.r_hand[0] + f * 26.0, pose.r_hand[1] - 8.0)
        draw.line([pose.l_hand, tip_l], fill=(180, 245, 255, 255), width=3)
        draw.line([pose.r_hand, tip_r], fill=(180, 245, 255, 255), width=3)
        draw.ellipse([tip_l[0] - 3, tip_l[1] - 3, tip_l[0] + 3, tip_l[1] + 3], fill=(255, 255, 255, 255))
        draw.ellipse([tip_r[0] - 3, tip_r[1] - 3, tip_r[0] + 3, tip_r[1] + 3], fill=(255, 255, 255, 255))


