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
    export_parser.add_argument("--transparency", action="store_true", help="Enable transparency")

    # gui command
    gui_parser = subparsers.add_parser("gui", help="Open a project in the Pencil2D GUI")
    gui_parser.add_argument("project_file", nargs="?", help="Optional project path")

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
            start_frame=args.start,
            end_frame=args.end,
            transparency=args.transparency
        )
        print(msg)
        if not ok:
            sys.exit(1)

    elif args.command == "gui":
        ok, msg = launch_gui(args.project_file)
        print(msg)
        if not ok:
            sys.exit(1)

if __name__ == "__main__":
    main()
