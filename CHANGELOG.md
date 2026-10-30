# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-10-30

### Added
- **Pure-Python Fallback Compositor**: Direct rendering of `.pclx` projects to animated GIF (`export_gif`), single frames (`render_frame`), and PNG sequences (`export_sequence`) using Pillow without needing the Pencil2D AppImage binary.
- **Headless Auto-Detection**: Automatically detects headless environments (missing `DISPLAY`) and wraps CLI export commands with `xvfb-run -a` when available.
- **`export_project` Enhancements**: Added `fps` override, configurable `timeout` (default 180s), and `force_pure_python` flag.
- **Detached GUI Process Lifetime**: `launch_gui` now runs with `start_new_session=True` so GUI windows remain open and detached on the desktop screen.
- **API Ergonomics & Aliases**:
  - `Pencil2DProject.create(file_path, width, height, fps, layer_names)` factory method.
  - `proj.validate()` alias for `proj.validate_integrity()`.
  - `render_animation` alias for `export_project`.
- **Dynamic Layer Auto-Creation**: `add_frame_image` and `pencil2d_add_frames_batch` automatically create missing bitmap layers when `auto_create_layer=True`.
- **Preserved Layer Stack Order**: Layer insertion in project creation now strictly preserves the declared input order.
- **CLI Flags**: Added `--fps`, `--timeout`, and `--pure-python` flags to the `pencil2d-mcp export` command.

## [0.2.0] - 2026-10-30

### Added
- **`pencil2d_add_frames_batch` tool**: Batch insert animation keyframes into projects from structured lists or directories in a single operation.
- **`pencil2d_add_layer` tool**: Dynamically create new Bitmap, Vector, Sound, or Camera layers.
- **`pencil2d_remove_layer` tool**: Delete layers by name or ID.
- **`pencil2d_add_audio` tool**: Embed audio clips (WAV/MP3) into sound layers at specific keyframes.
- **`pencil2d_set_camera` tool**: Keyframe camera pan (dx, dy), zoom/scale, and rotation angles.
- **`pencil2d_manage_palette` tool**: Add or update color swatches in the project palette.
- **`pencil2d_create_spritesheet` tool**: Pack animation frames into a sprite sheet with coordinate grid metadata.
- **`pencil2d_validate` tool**: Project integrity and diagnostic checker detecting missing frames, broken XML references, and layer structure errors.
- Enhanced `Pencil2DProject` core with audio embedding, spritesheet generator, and validation methods.

## [0.1.0] - 2026-10-30

### Added
- **MCP Server Implementation**: Full Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for AI agents.
- **`pencil2d_inspect` tool**: Inspect .pclx animation projects (dimensions, FPS, keyframe counts, layers, color palette).
- **`pencil2d_create` tool**: Generate fresh .pclx projects with customizable resolution, FPS, and layers.
- **`pencil2d_add_frame` tool**: Insert and update keyframe images from disk or base64 into bitmap layers.
- **`pencil2d_extract_frames` tool**: Extract individual PNG frames from any project for AI or image manipulation.
- **`pencil2d_export` tool**: Render animations to MP4, animated GIF, WebM, or PNG image sequence via the Pencil2D AppImage CLI.
- **`pencil2d_launch_gui` tool**: Launch projects directly in the interactive Pencil2D GUI.
- **Core Library (`pencil2d_mcp.core`)**: Python OOP interface (`Pencil2DProject`) for reading, modifying, and writing .pclx archives without requiring GUI dependencies.
- **CLI Utility (`pencil2d-mcp`)**: Command-line tool to test, inspect, run, and export animations.
