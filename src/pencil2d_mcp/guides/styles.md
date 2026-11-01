---
title: Animation Art Styles Guide
summary: Visual formulas, palettes, proportions, and stroke techniques for Stickman, Anime, Pencil Sketch, Studio Ghibli, and Doodle animations.
---

# Animation Art Styles Guide

When drawing in Pencil2D through code, avoid sterile geometrical shapes. Follow these distinct stylistic recipes:

---

## 1. Dynamic Stickman (Action / Martial Arts)
Do not draw stiff lollipop sticks with rigid compass circles!

- **Line of Action**: Give the torso a curved spine arc ($C$-shape or $S$-shape) indicating momentum and effort.
- **Anatomy & Proportions**:
  - Head: Circle or tilted oval (radius $R$).
  - Neck to Pelvis: $2.2 \times R$.
  - Legs (Thigh + Shin): $2.8 \times R$ with clear knee joint bend.
  - Arms (Bicep + Forearm): $2.0 \times R$ with bent elbows.
- **Stroke Dynamics**: Thick, confident outlines (4–7px) with rounded caps (`joint="curve"`).
- **Action Accents**: Add dynamic motion blur arcs (speed streaks), ground impact dust puffs, and hit sparks on contact.
- **Colors**: Deep charcoal black (`#1A1A24`) or ninja navy, with vivid accent colors for headbands, energy trails, or weapons.

---

## 2. Anime & Manga (Cel-Shaded Traditional 2D)
Anime drawing relies on clean silhouettes, stylized facial proportions, and two-tone cel shading.

- **Proportions**:
  - Head: Triangular taper toward the chin, wide eye level at the lower 40% of the face.
  - Eyes: Large expressive irises with upper dark shadow, prominent pupil, and 1–2 crisp white specular highlights (catchlights).
  - Hair: Group hair into dimensional sculptural locks/bangs rather than individual hairline strands. Add a horizontal sheen/highlight band across the crown.
- **Coloring Technique (Two-Tone Cel-Shading)**:
  - Base Color (Midtone): The primary flat hue.
  - Shadow Color (Core Shadow): Shift hue slightly towards purple/blue and drop value by 20–30%. Avoid dirty black shadows!
  - Specular Highlight: High-value warm accent on hair crest, nose tip, and eye gleam.
- **Line Art**: Fine, tapered ink lines (2–3px) with dark sepia or deep plum tint (`#2A1D2B`) instead of harsh pure black.

---

## 3. Traditional Pencil Sketch (Graphite & Charcoal)
Emulate the organic warmth and texture of hand-drawn paper animation.

- **Multi-Pass Construction**:
  - **Pass 1 (Underdrawing / Gesture)**: Loose, low-opacity (20–30% alpha) sketch lines in light cerulean blue (`#7EA0C4`) or faint graphite (`#9A9A9A`) establishing anatomy and gesture.
  - **Pass 2 (Key Contours)**: Confident graphite lines (`#2C2C2E`) with subtle stroke wobble and pressure variation.
  - **Pass 3 (Shading & Hatching)**: Diagonal parallel cross-hatch lines indicating core shadows and form volume.
- **Texture Simulation**: Layer slightly offset micro-strokes to emulate graphite grain and paper tooth.

---

## 4. Studio Ghibli Aesthetic (Painterly & Whimsical)
Known for breathtaking natural beauty, soft watercolor washes, and warm nostalgic light.

- **Color Palette**:
  - Sky: Soft cerulean blue (`#5D9CEC`) fading to warm horizon cream (`#F5E6CC`).
  - Foliage/Grass: Rich moss green (`#4A7C59`), spring lime (`#88D49E`), and deep forest shadow (`#1D3E2E`).
  - Warm Earth & Cloud: Puffy cumulus clouds with lilac/soft pink undertones (`#E8DCED`) and crisp sunlit rim (`#FFFDF7`).
- **Character Design**: Gentle rounded curves, button noses, expressive wide eyes with soft dark pupils, cozy hand-tailored clothing with gentle folds.
- **Atmospheric Effects**: Floating dandelion seeds, falling leaves, shimmering water ripples, moving wind dust.

---

## 5. Hand-Drawn Doodle & Cartoon (Notebook Fun)
Playful, expressive, loose, and instantly charming.

- **Wobbly Line Magic**: Intentionally introduce slight natural jitter and hand-drawn variation to all line paths.
- **Overlapping Corners**: Let stroke intersections overshoot by 2–4 pixels—this immediately screams "drawn by hand".
- **Cartoons Expressions**:
  - Elastic squash and stretch: Characters bend and squash like rubber hoses.
  - Emotion symbols: Oversized sweat drops, exclamation stars, swirly dizziness eyes, speed puff clouds behind running feet.
- **Palette**: Monoline black marker (`#101018`) on off-white parchment/notebook paper (`#FAF7EE`), with single-color marker spot highlights (e.g., cheerful pastel yellow or cyan).
