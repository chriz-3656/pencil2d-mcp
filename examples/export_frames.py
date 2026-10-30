#!/usr/bin/env python3
"""Example: Inspect a Pencil2D project and unpack all frames into a folder."""

import os
import sys
from pencil2d_mcp.core import Pencil2DProject

def main():
    if len(sys.argv) < 2:
        print("Usage: python export_frames.py <path_to_project.pclx> [output_dir]")
        sys.exit(1)

    proj_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_frames"
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading project: {proj_path}")
    project = Pencil2DProject.load(proj_path)

    summary = project.inspect_summary()
    print(f"Canvas: {summary['resolution']}, FPS: {summary['fps']}, Layers: {summary['total_layers']}")

    count = 0
    for layer in project.layers:
        if layer["type"] == 1: # Bitmap
            for frame_idx, frame_data in sorted(layer["frames"].items()):
                if frame_data.get("bytes"):
                    clean_name = f"layer_{layer['id']}_{layer['name']}_frame_{frame_idx:03d}.png".replace(" ", "_")
                    dest = os.path.join(out_dir, clean_name)
                    with open(dest, "wb") as f:
                        f.write(frame_data["bytes"])
                    print(f"Saved: {dest}")
                    count += 1

    print(f"Extracted {count} frame(s) to '{out_dir}'.")

if __name__ == "__main__":
    main()
