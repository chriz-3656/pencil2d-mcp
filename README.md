# Pencil2D Model Context Protocol (MCP) Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![Maintainer](https://img.shields.io/badge/developer-chriz--3656-orange.svg)](https://github.com/chriz-3656)

An open-source **Model Context Protocol (MCP)** server and automation toolkit that empowers AI agents (Claude Desktop, Google Antigravity, Cursor, Cline, etc.) to programmatically create, inspect, edit, and render traditional 2D hand-drawn animations using **[Pencil2D](https://www.pencil2d.org/)**.

---

## ✨ Features

- **⚡ Zero External Heavyweight Dependencies**: Pure Python implementation with standard library + Pillow. No Qt build required for project manipulation.
- **🎬 Native Headless Rendering**: Leverages Pencil2D AppImage CLI to render animations directly to **MP4 (H.264)**, **animated GIF**, **WebM**, or **PNG image sequences**.
- **🎨 Complete Project (.pclx) Support**: Read, construct, and modify native `.pclx` archives, layer structures (Bitmap, Camera, Palette), frame timings, and camera transformations.
- **🖥️ Dual Execution Modes**:
  - Headless automated pipelines for AI agent workflow.
  - Interactive GUI launching to preview and pair-draw with human artists.
- **🔌 Standard MCP Compatibility**: Speaks JSON-RPC 2.0 over standard I/O (stdio transport), compatible with Claude Desktop, Google Antigravity, Cursor, and any MCP-compliant client.

---

## 🛠️ Available MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| **`pencil2d_inspect`** | `project_path` *(string, required)* | Inspect a `.pclx` project file to inspect canvas resolution, framerate (FPS), total keyframes, layer breakdown, and color palette. |
| **`pencil2d_create`** | `project_path` *(string, required)*,<br>`width` *(int, default: 800)*,<br>`height` *(int, default: 600)*,<br>`fps` *(int, default: 12)*,<br>`layer_names` *(list[str])* | Create a fresh, valid `.pclx` project ready for drawing keyframes. |
| **`pencil2d_add_frame`** | `project_path` *(string, required)*,<br>`frame` *(int, required)*,<br>`image_path` *(string)* or `base64_data` *(string)*,<br>`layer_name` *(string)*,<br>`top_left_x` / `top_left_y` *(int)* | Insert or replace an animation frame in a bitmap layer using an image file or base64 data. |
| **`pencil2d_extract_frames`** | `project_path` *(string, required)*,<br>`output_dir` *(string, required)* | Unpack all PNG frames from a `.pclx` file into a directory for AI inspection or image manipulation. |
| **`pencil2d_export`** | `project_path` *(string, required)*,<br>`output_path` *(string, required)*,<br>`width` / `height` *(int)*,<br>`start_frame` / `end_frame` *(int)*,<br>`transparency` *(bool)*,<br>`camera` *(string)* | Headlessly render an animation project to video (MP4), animated GIF, WebM, or PNG sequence. |
| **`pencil2d_launch_gui`** | `project_path` *(string, optional)* | Open the project in the visual Pencil2D GUI for interactive editing. |

---

## 🚀 Installation

### Option 1: From PyPI (Recommended)

```bash
pip install pencil2d-mcp
```

### Option 2: From Source

```bash
git clone https://github.com/chriz-3656/pencil2d-mcp.git
cd pencil2d-mcp
pip install -e .
```

### Pencil2D Executable Prerequisite

Download the official [Pencil2D Linux AppImage](https://www.pencil2d.org/download/) (v0.7.2 or newer) and make it executable:

```bash
chmod +x ~/Downloads/pencil2d-linux-amd64-v0.7.2.AppImage
```

*(The server will automatically detect the AppImage in `~/Downloads`, `/usr/bin/pencil2d`, or via the `PENCIL2D_APPIMAGE` environment variable).*

---

## ⚙️ Client Configuration

### 1. Google Antigravity (`~/.gemini/config/mcp_config.json`)

```json
{
  "mcpServers": {
    "pencil2d": {
      "command": "pencil2d-mcp",
      "args": ["serve"],
      "env": {
        "DISPLAY": ":0.0",
        "PENCIL2D_APPIMAGE": "/home/demo/Downloads/pencil2d-linux-amd64-v0.7.2.AppImage"
      }
    }
  }
}
```

### 2. Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "pencil2d": {
      "command": "python3",
      "args": ["-m", "pencil2d_mcp", "serve"],
      "env": {
        "PENCIL2D_APPIMAGE": "/path/to/pencil2d-linux-amd64-v0.7.2.AppImage"
      }
    }
  }
}
```

### 3. Cursor / Cline / Roo-Code

Add to your MCP settings:

```json
{
  "mcpServers": {
    "pencil2d": {
      "command": "pencil2d-mcp",
      "args": ["serve"]
    }
  }
}
```

---

## 💻 CLI Usage

The package installs the `pencil2d-mcp` command-line tool:

```bash
# Verify system setup, AppImage detection, and display
pencil2d-mcp check

# Inspect a .pclx project
pencil2d-mcp inspect animation.pclx

# Headlessly export animation to MP4 or GIF
pencil2d-mcp export animation.pclx -o output.mp4
pencil2d-mcp export animation.pclx -o preview.gif --width 800 --height 600

# Open project in GUI
pencil2d-mcp gui animation.pclx

# Start the MCP stdio server manually
pencil2d-mcp serve
```

---

## 🐍 Python Library Usage

You can also use `pencil2d-mcp` directly as a Python library:

```python
from PIL import Image, ImageDraw
from pencil2d_mcp import Pencil2DProject, export_project

# 1. Initialize project
project = Pencil2DProject(width=800, height=600, fps=12)

# 2. Add animation frames
for frame_idx in range(1, 10):
    img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([100 + frame_idx * 50, 300, 160 + frame_idx * 50, 360], fill=(230, 50, 50, 255))
    project.add_frame_image("Bitmap Layer", frame_idx, img)

# 3. Save project
project.save("my_animation.pclx")

# 4. Render to video and animated GIF
export_project("my_animation.pclx", "my_animation.mp4")
export_project("my_animation.pclx", "my_animation.gif")
```

---

## 📦 File Architecture

```text
pencil2d-mcp/
├── .github/
│   ├── workflows/ci.yml           # Multi-version Python CI tests
│   ├── workflows/release.yml      # PyPI publishing on git tags
│   └── ISSUE_TEMPLATE/            # GitHub issue templates
├── src/
│   └── pencil2d_mcp/
│       ├── __init__.py            # Public package exports
│       ├── __main__.py            # python -m pencil2d_mcp entrypoint
│       ├── core.py                # Pencil2DProject & CLI exporter
│       ├── server.py              # Pure-Python MCP JSON-RPC 2.0 stdio server
│       └── cli.py                 # CLI interface
├── tests/
│   ├── test_core.py               # Unit tests for project serialization
│   └── test_server.py             # Unit tests for MCP server tools
├── examples/
│   ├── demo_animation.py          # Bouncing ball example
│   └── export_frames.py           # Frame extraction utility
├── pyproject.toml                 # Modern PEP 517 build config
├── setup.py                       # Setup script
├── setup.cfg                      # Package metadata
├── requirements.txt               # Pillow
├── requirements-dev.txt           # Test & build tools
├── LICENSE                        # MIT License
├── CHANGELOG.md                   # Keep a Changelog standard
├── CONTRIBUTING.md                # Contribution guide
├── CODE_OF_CONDUCT.md             # Contributor Covenant
└── mcp.json                       # MCP registry manifest
```

---

## 🧪 Testing

Run the test suite:

```bash
python -m unittest discover tests
```

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Developed with ❤️ by **[chriz-3656](https://github.com/chriz-3656)**.
