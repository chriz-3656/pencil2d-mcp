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

