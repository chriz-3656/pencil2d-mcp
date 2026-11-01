"""Command Line Interface (CLI) entrypoint for pencil2d-mcp."""

import argparse
import json
import os
import sys

from .core import Pencil2DProject, export_project, get_appimage_path, launch_gui
from .server import run_server, TOOLS

def main():
    parser = argparse.ArgumentParser(
        prog="pencil2d-mcp",
        description="Pencil2D MCP Server and Command-Line Toolkit by chriz-3656"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP JSON-RPC stdio server")

    # check command
    check_parser = subparsers.add_parser("check", help="Verify Pencil2D AppImage installation & tools")

    # inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a Pencil2D (.pclx) file")
    inspect_parser.add_argument("project_file", help="Path to .pclx file")

    # export command
    export_parser = subparsers.add_parser("export", help="Export a Pencil2D project to video/GIF")
    export_parser.add_argument("project_file", help="Path to .pclx file")
    export_parser.add_argument("-o", "--output", required=True, help="Output destination (.mp4, .gif, .png)")
    export_parser.add_argument("--width", type=int, help="Target frame width")
    export_parser.add_argument("--height", type=int, help="Target frame height")
    export_parser.add_argument("--start", type=int, help="Start frame index")
    export_parser.add_argument("--end", type=int, help="End frame index")
    export_parser.add_argument("--fps", type=int, help="Framerate override")
    export_parser.add_argument("--timeout", type=int, default=180, help="Export timeout in seconds (default 180)")
    export_parser.add_argument("--pure-python", action="store_true", help="Use pure-Python compositor without AppImage")
    export_parser.add_argument("--transparency", action="store_true", help="Enable transparency")

    # gui command
    gui_parser = subparsers.add_parser("gui", help="Open a project in the Pencil2D GUI")
    gui_parser.add_argument("project_file", nargs="?", help="Optional project path")

    # look command (contact sheet preview strip)
    look_parser = subparsers.add_parser("look", help="Inspect animation as a visual contact strip or frame")
    look_parser.add_argument("project_file", help="Path to .pclx file")
    look_parser.add_argument("-o", "--output", help="Output PNG path for contact sheet strip")
    look_parser.add_argument("--count", type=int, default=6, help="Number of frames to sample (default 6)")
    look_parser.add_argument("--onion", action="store_true", help="Enable onion skinning overlay")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate stylized 2D animation (stickman, anime, sketch, ghibli, doodle)")
    gen_parser.add_argument("project_file", help="Target .pclx file to create")
    gen_parser.add_argument("--style", default="stickman", choices=["stickman", "anime", "pencil_sketch", "ghibli", "doodle"], help="Artistic style")
    gen_parser.add_argument("--action", help="Specific action to animate")
    gen_parser.add_argument("--frames", type=int, default=12, help="Frame count (default 12)")
    gen_parser.add_argument("--fps", type=int, default=12, help="Frames per second (default 12)")

    # guide command
    guide_parser = subparsers.add_parser("guide", help="Read craft knowledge guides on animation & styles")
    guide_parser.add_argument("topic", nargs="?", default="animation", help="Topic: animation, styles, drawing_techniques")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        run_server()

    elif args.command == "check":
        app_path = get_appimage_path()
        print("=== Pencil2D MCP Diagnostics ===")
        if app_path:
            print(f"[OK] Pencil2D binary detected: {app_path}")
        else:
            print("[WARN] Pencil2D binary not detected. Please install Pencil2D or set PENCIL2D_APPIMAGE.")
        print(f"[OK] Available MCP tools: {len(TOOLS)}")
        for t in TOOLS:
            print(f"     - {t['name']}: {t['description']}")
        print(f"[OK] Display environment: {os.environ.get('DISPLAY', 'Not set')}")

    elif args.command == "inspect":
        try:
            proj = Pencil2DProject.load(args.project_file)
            print(json.dumps(proj.inspect_summary(), indent=2))
        except Exception as e:
            print(f"Error inspecting project: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "export":
        ok, msg = export_project(
            project_path=args.project_file,
            output_path=args.output,
            width=args.width,
            height=args.height,
            fps=args.fps,
            start_frame=args.start,
            end_frame=args.end,
            transparency=args.transparency,
            timeout=args.timeout,
            force_pure_python=args.pure_python
        )
        print(msg)
        if not ok:
            sys.exit(1)

    elif args.command == "gui":
        ok, msg = launch_gui(args.project_file)
        print(msg)
        if not ok:
            sys.exit(1)

    elif args.command == "look":
        try:
            proj = Pencil2DProject.load(args.project_file)
            strip_img, out_path = proj.generate_preview_strip(
                frame_count=args.count, onion_skin=args.onion, output_path=args.output
            )
            print(f"[OK] Preview filmstrip created: {out_path} ({strip_img.width}x{strip_img.height})")
        except Exception as e:
            print(f"Error generating visual preview: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "generate":
        try:
            from .styles import generate_stylized_animation
            frames = generate_stylized_animation(
                style=args.style, action=args.action, frame_count=args.frames
            )
            proj = Pencil2DProject.create(
                file_path=args.project_file, fps=args.fps, layer_names=["Animation Layer"]
            )
            for idx, f_img in enumerate(frames, start=1):
                proj.add_frame_image("Animation Layer", idx, f_img)
            proj.save(args.project_file)

            # Auto-generate filmstrip preview
            strip_out = os.path.splitext(args.project_file)[0] + "_preview.png"
            proj.generate_preview_strip(frame_count=min(6, args.frames), output_path=strip_out)

            print(f"[OK] Created {len(frames)}-frame '{args.style}' animation: {args.project_file}")
            print(f"[OK] Contact sheet strip saved: {strip_out}")
        except Exception as e:
            print(f"Error generating stylized animation: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "guide":
        from .guides import get_guide
        print(get_guide(args.topic))

if __name__ == "__main__":
    main()
