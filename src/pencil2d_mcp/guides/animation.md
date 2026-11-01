---
title: 2D Animation Principles & Timing
summary: The 12 principles of classical 2D animation, timing charts, squash & stretch, arcs, and avoiding robotic math motion in Pencil2D.
---

# 2D Animation Principles & Timing

Traditional 2D hand-drawn animation comes alive through physics, weight, and personality—not rigid mathematical linear interpolation.

## 1. Squash and Stretch (Volume Preservation)
Living bodies deform when moving, jumping, or landing.
- **Rule of Volume**: If an object compresses along one axis, it must expand along the perpendicular axis to preserve volume.
  $$\Delta X \cdot \Delta Y = 1 \implies \text{Width} = \frac{W_0}{\sqrt{S_y}}, \quad \text{Height} = H_0 \cdot S_y$$
- **Crouch/Preparation**: Squash ($S_y \approx 0.75$).
- **Launch/Descent**: Stretch along trajectory ($S_y \approx 1.25$).
- **Impact/Landing**: Squash against the ground plane ($S_y \approx 0.65$).
- **Rest/Recovery**: Settle back to standard ($S_y = 1.0$).

## 2. Anticipation & Overshoot
Never initiate a major action instantaneously.
- **Anticipation (1–3 frames)**: Wind up in the *opposite* direction before moving (e.g., squat before leaping, pull elbow back before punching).
- **Action (1–2 frames)**: Fast, dynamic movement across the canvas.
- **Overshoot & Settle (2–4 frames)**: The body travels slightly past the target pose, then springs back into rest.

## 3. Arcs of Motion
Real-world limbs, trajectories, and bodies move in smooth curves and parabolas—**never straight diagonal vectors**.
- Jumps follow parabolic arcs: $y(t) = 4 h \cdot t(1 - t)$.
- Arm swings and head turns pivot around joint centers in curved sweeps.
- When drawing in-betweens, plot the trajectory curve first, then space keyframe positions along that curve.

## 4. Slow In and Slow Out (Easing)
Uniform linear motion ($x = x_0 + v \cdot t$) feels like a conveyor belt or robot.
- **Ease In / Ease Out**: Dense spacing near key poses (extremes), wide spacing in the middle (fastest motion).
- Use cubic easing ($3t^2 - 2t^3$) or exponential decel ($1 - (1-t)^3$) instead of constant stepping.

## 5. Follow-Through and Overlapping Action
Not all parts of a character stop at once.
- Loose, secondary elements (hair bangs, cape, sword scabbard, tail, loose sleeves) lag behind the primary body by 2–4 frames.
- When the body stops, secondary elements overshoot forward and oscillate to a halt.

## 6. Pose-to-Pose Workflow in Pencil2D
1. **Key Poses (Extremes)**: Draw the most communicative, storytelling poses first (e.g., Frame 1 = Stand, Frame 5 = Crouch Anticipation, Frame 8 = Peak Leap, Frame 11 = Ground Impact).
2. **Breakdowns (Passing Poses)**: Define how the character transitions between extremes (e.g., Frame 3 = Mid-crouch, Frame 9 = Peak Arc).
3. **In-Betweens**: Fill the timing frames according to your spacing chart.
4. **Visual Inspection**: Call `pencil2d_look(mode="strip")` to inspect the entire animation strip side by side to ensure fluid continuity.
