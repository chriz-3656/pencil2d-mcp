# Pencil2D Model Context Protocol (MCP) Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![Maintainer](https://img.shields.io/badge/developer-chriz--3656-orange.svg)](https://github.com/chriz-3656)

An open-source **Model Context Protocol (MCP)** server and automation toolkit that empowers AI agents (Claude Desktop, Google Antigravity, Cursor, Cline, etc.) to programmatically create, inspect, edit, and render traditional 2D hand-drawn animations using **[Pencil2D](https://www.pencil2d.org/)**.

---

## ✨ Features

- **⚡ Zero Heavyweight Runtime Dependencies**: Pure Python implementation with standard library + Pillow.
- **🎬 Native Headless Rendering**: Leverages Pencil2D AppImage CLI to render animations directly to **MP4 (H.264)**, **animated GIF**, **WebM**, or **PNG image sequences**.
- **🎨 Complete Project (.pclx) Support**: Read, construct, and modify native `.pclx` archives, layer structures (Bitmap, Vector, Sound, Camera, Palette), frame timings, and camera transformations.
- **⚡ Batch Frame Operations**: Import whole animations from directories or structured lists in a single operation.
- **🔊 Sound & Audio Integration**: Embed voiceovers and sound effects (WAV/MP3) directly into sound layers.
- **🎥 Dynamic Camera Controls**: Keyframe camera pan (dx, dy), zoom (scale), and rotation angles.
- **🖼️ Spritesheet Generator**: Pack animated frames into game-ready spritesheet PNGs with coordinate metadata.
- **🩺 Project Health & Validation**: Sanity check `.pclx` projects for broken links, missing frame gaps, and XML errors.
- **🖥️ Dual Execution Modes**: Automated background pipelines or live visual GUI launching (`pencil2d_launch_gui`).
- **🔌 Standard MCP Compatibility**: Speaks JSON-RPC 2.0 over standard I/O (stdio transport).

---

## 🛠️ Complete MCP Toolset (14 Tools)

Every tool is exposed as a first-class AI tool over MCP:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| **`pencil2d_inspect`** | `project_path` | Inspect a `.pclx` project file to inspect canvas resolution, framerate (FPS), total keyframes, layer breakdown, and color palette. |
| **`pencil2d_create`** | `project_path`, `width`, `height`, `fps`, `layer_names` | Create a fresh, valid `.pclx` project ready for drawing keyframes. |
| **`pencil2d_add_frame`** | `project_path`, `frame`, `image_path` / `base64_data`, `layer_name`, `top_left_x`, `top_left_y` | Insert or replace an animation frame in a bitmap layer using an image file or base64 data. |
| **`pencil2d_add_frames_batch`** | `project_path`, `frames` *(list)*, `directory_path` *(str)*, `layer_name`, `start_frame`, `step` | Batch import multiple animation frames from a folder or list in a single call. |
| **`pencil2d_add_layer`** | `project_path`, `name`, `layer_type` *(bitmap, vector, sound, camera)*, `visible` | Add a new layer to the project timeline. |
| **`pencil2d_remove_layer`** | `project_path`, `layer_name_or_id` | Delete a layer and its keyframes from the project. |
| **`pencil2d_add_audio`** | `project_path`, `audio_path`, `frame`, `layer_name` | Embed an audio track/clip (WAV/MP3) into a sound layer at a specific keyframe. |
| **`pencil2d_set_camera`** | `project_path`, `frame`, `dx`, `dy`, `scale`, `rotation` | Keyframe camera pan, zoom, and rotation angle at any frame. |
| **`pencil2d_manage_palette`** | `project_path`, `color_name`, `red`, `green`, `blue`, `alpha` | Add or update a color swatch in the project palette. |
| **`pencil2d_create_spritesheet`** | `project_path`, `output_image`, `layer_name`, `columns` | Pack animated frames into a sprite sheet with coordinate grid metadata. |
| **`pencil2d_validate`** | `project_path` | Deep project integrity test checking XML syntax, asset references, and frame continuity. |
| **`pencil2d_extract_frames`** | `project_path`, `output_dir` | Unpack all PNG frames from a `.pclx` file into a directory for AI inspection or external editing. |
| **`pencil2d_export`** | `project_path`, `output_path`, `width`, `height`, `start_frame`, `end_frame`, `transparency`, `camera` | Headlessly render an animation project to video (MP4), animated GIF, WebM, or PNG sequence. |
| **`pencil2d_launch_gui`** | `project_path` | Open the project in the visual Pencil2D GUI for interactive editing. |

---

## 🚀 Installation

### Option 1: From PyPI

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

---

## ⚙️ Client Configuration

### 1. Google Antigravity (`~/.gemini/config/mcp_config.json`)

```json
{
  "mcpServers": {
    "pencil2d": {
      "command": "python3",
      "args": ["-m", "pencil2d_mcp", "serve"],
      "env": {
        "PYTHONPATH": "/home/demo/pencil2d-mcp/src",
        "PENCIL2D_APPIMAGE": "/home/demo/Downloads/pencil2d-linux-amd64-v0.7.2.AppImage",
        "DISPLAY": ":0.0"
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

## 🧪 Testing

```bash
python -m unittest discover tests
```

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Maintained with ❤️ by **[chriz-3656](https://github.com/chriz-3656)**.
