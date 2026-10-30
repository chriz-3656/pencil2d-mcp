#!/usr/bin/env python3
"""Example: Create a bouncing ball animation and export to MP4 and GIF."""

import os
from PIL import Image, ImageDraw
from pencil2d_mcp.core import Pencil2DProject, export_project

def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.join(out_dir, "bouncing_ball.pclx")
    gif_path = os.path.join(out_dir, "bouncing_ball.gif")
    mp4_path = os.path.join(out_dir, "bouncing_ball.mp4")

    print(f"Creating animation project: {project_path}")
    project = Pencil2DProject(width=800, height=600, fps=12)

    positions = [
        (150, 450),
        (250, 250),
        (350, 150),
        (450, 250),
        (550, 450),
        (650, 300),
    ]

    for idx, (x, y) in enumerate(positions, start=1):
        img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Ground contact shadow
        draw.ellipse([x - 30, 480, x + 30, 500], fill=(180, 180, 180, 120))

        # Ball
        r = 35
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(230, 60, 60, 255), outline=(20, 20, 20, 255), width=3)
        draw.ellipse([x - 12, y - 18, x, y - 6], fill=(255, 180, 180, 255))

        project.add_frame_image("Bitmap Layer", idx, img)

    project.save(project_path)
    print("Project saved. Rendering exports via Pencil2D...")

    ok_gif, msg_gif = export_project(project_path, gif_path)
    print(f"GIF Export ({ok_gif}): {gif_path}")

    ok_mp4, msg_mp4 = export_project(project_path, mp4_path)
    print(f"MP4 Export ({ok_mp4}): {mp4_path}")

if __name__ == "__main__":
    main()
