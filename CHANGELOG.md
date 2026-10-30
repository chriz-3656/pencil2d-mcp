# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Complete documentation, configuration examples for Claude Desktop, Antigravity, and Cursor, issue templates, and CI workflows.
