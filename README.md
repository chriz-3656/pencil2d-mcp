# Pencil2D Model Context Protocol (MCP) Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.0-green.svg)](pyproject.toml)
[![PyPI](https://img.shields.io/pypi/v/pencil2d-mcp.svg)](https://pypi.org/project/pencil2d-mcp/)
[![Website](https://img.shields.io/badge/Showcase-Website-orange.svg)](https://github.com/chriz-3656/pencil2d-mcp-web)
[![Maintainer](https://img.shields.io/badge/developer-chriz--3656-blue.svg)](https://github.com/chriz-3656)

An open-source **Model Context Protocol (MCP)** server and procedural 2D animation toolkit that empowers AI agents (Google Antigravity, Claude Desktop, Cursor, Cline, Roo-Code, etc.) to programmatically author, inspect, edit, and render broadcast-grade traditional 2D hand-drawn animations using **[Pencil2D](https://www.pencil2d.org/)**.

---

## ✨ Key Features & Capabilities

- **🏃 Articulated 2-Bone Inverse Kinematics (IK)**: Analytic trigonometry ensures exact bone lengths ($L_1, L_2$) for elbows and knees with zero popping, stretching, or distortion.
- **🚶 Grounded Bipedal Locomotion Engine**: True stance foot ground-locking (zero sliding/ice-skating), swing knee lift arcs, double-frequency pelvic vertical bouncing, dynamic torso lean, and natural arm counter-swings.
- **⚡ Continuous Pose Interpolator**: Cubic Hermite ($C^1$) smoothstep blending across all 15 joints, completely eliminating teleporting and instantaneous joint snaps.
- **💥 Sakuga Anime Combat Engine**: Curved velocity motion smear wedges, inverted monochrome Sakuga impact frames, contact hit sparks, speed lines, and camera shake with damped harmonic decay.
- **🎨 5 Stylized Procedural Renderers**: Built-in production generators for *Stickman* (Martial Arts), *Anime* (Cel Shading & Hair Volumes), *Pencil Sketch* (Multi-Pass Graphite Hatching), *Studio Ghibli* (Rolling Meadow Hills & Painterly Clouds), and *Doodle* (Marker Wobble & Rubber-Hose Physics).
- **👁️ Visual Inspection & Feedback (`pencil2d_look`)**: Contact sheet filmstrip generator with customizable frame sampling and onion skinning so AI agents verify visual quality without a graphical desktop.
- **🎬 Headless & Pure-Python Dual Rendering**: Leverages official Pencil2D AppImage CLI or built-in pure-Python Pillow fallback to render animations to **MP4 (H.264)**, **animated GIF**, or **PNG image sequences**—even in headless Linux server environments without an X server.
- **🎨 Complete Project (.pclx) Support**: Read, construct, and modify native `.pclx` archives, layer structures (Bitmap, Vector, Sound, Camera, Palette), frame timings, and camera transformations.
- **🔊 Sound & Audio Integration**: Embed voiceovers and sound effects (WAV/MP3) directly into sound layers.
- **🎥 Dynamic Camera Controls**: Keyframe camera pan (dx, dy), zoom (scale), and rotation angles.
- **🖼️ Spritesheet Generator**: Pack animated frames into game-ready spritesheet PNGs with coordinate metadata.
- **🩺 Project Health & Validation**: Sanity check `.pclx` projects for broken links, missing frame gaps, and XML errors.
- **🔌 Standard MCP Compatibility**: Speaks JSON-RPC 2.0 over standard I/O (stdio transport).

---

## 🛠️ Complete MCP Toolset (17 Tools)

Every tool is exposed as a first-class AI tool over MCP:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| **`pencil2d_look`** | `project_path`, `mode` *(strip, frame)*, `frames`, `frame_count`, `onion_skin`, `output_path` | Visually inspect animation via multi-frame contact sheet filmstrip (with frame numbers and onion skinning) or single frame so the AI verifies its work. |
| **`pencil2d_generate_animation`** | `project_path`, `style` *(stickman, anime, pencil_sketch, ghibli, doodle)*, `action`, `frame_count`, `fps`, `width`, `height` | Generate complete stylized animations using authentic artistic presets, squash & stretch physics, and curved lines of action. |
| **`pencil2d_get_guide`** | `topic` *(animation, styles, drawing_techniques)* | Retrieve craft knowledge guides on 2D animation principles, timing charts, squash & stretch volume preservation, and style recipes. |
| **`pencil2d_inspect`** | `project_path` | Inspect a `.pclx` project file to inspect canvas resolution, framerate (FPS), total keyframes, layer breakdown, and color palette. |
| **`pencil2d_create`** | `project_path`, `width`, `height`, `fps`, `layer_names` | Create a fresh, valid `.pclx` project ready for drawing keyframes. |
| **`pencil2d_add_frame`** | `project_path`, `frame`, `image_path` / `base64_data`, `layer_name`, `top_left_x`, `top_left_y` | Insert or replace an animation frame in a bitmap layer using an image file or base64 data. |
| **`pencil2d_add_frames_batch`** | `project_path`, `frames` *(list)*, `directory_path` *(str)*, `layer_name`, `start_frame`, `step`, `auto_create_layers` | Batch import multiple animation frames from a folder or list in a single call with auto-layer creation. |
| **`pencil2d_add_layer`** | `project_path`, `name`, `layer_type` *(bitmap, vector, sound, camera)*, `visible` | Add a new layer to the project timeline. |
| **`pencil2d_remove_layer`** | `project_path`, `layer_name_or_id` | Delete a layer and its keyframes from the project. |
| **`pencil2d_add_audio`** | `project_path`, `audio_path`, `frame`, `layer_name` | Embed an audio track/clip (WAV/MP3) into a sound layer at a specific keyframe. |
| **`pencil2d_set_camera`** | `project_path`, `frame`, `dx`, `dy`, `scale`, `rotation` | Keyframe camera pan, zoom, and rotation angle at any frame. |
| **`pencil2d_manage_palette`** | `project_path`, `color_name`, `red`, `green`, `blue`, `alpha` | Add or update a color swatch in the project palette. |
| **`pencil2d_create_spritesheet`** | `project_path`, `output_image`, `layer_name`, `columns` | Pack animated frames into a sprite sheet with coordinate grid metadata. |
| **`pencil2d_validate`** | `project_path` | Deep project integrity test checking XML syntax, asset references, and frame continuity. |
| **`pencil2d_extract_frames`** | `project_path`, `output_dir` | Unpack all PNG frames from a `.pclx` file into a directory for AI inspection or external editing. |
| **`pencil2d_export`** | `project_path`, `output_path`, `width`, `height`, `fps`, `start_frame`, `end_frame`, `transparency`, `camera`, `timeout`, `force_pure_python` | Headlessly render an animation project to video (MP4), animated GIF, or PNG sequence (via AppImage CLI or pure-Python fallback). |
| **`pencil2d_launch_gui`** | `project_path` | Open the project in the visual Pencil2D GUI for interactive editing. |

---

## 🏃 Kinematics & Locomotion Architecture

```
                    [ Head ]
                       |
                   ( Neck )
                  /   |    \
     [L_Shoulder]  (MidSpine) [R_Shoulder]
          |           |            |
     (L_Elbow)*   [ Pelvis ]   (R_Elbow)*
          |         /    \         |
      [L_Hand]  [L_Hip] [R_Hip] [R_Hand]
                   |        |
              (L_Knee)*  (R_Knee)*
                   |        |
               [L_Foot]  [R_Foot]
  
  (*) Solved continuously via analytic 2-Bone Inverse Kinematics
```

- **`solve_2bone_ik(root, target, l1, l2, bend_positive)`**:
  Solves triangle angles via Law of Cosines with reach clamping:
  $$\cos(\alpha) = \frac{L_1^2 + d^2 - L_2^2}{2 L_1 d}$$
- **`generate_locomotion_pose(x, ground_y, phase, facing, speed)`**:
  Generates fully articulated walk, jog, and sprint cycles with true foot ground-locking and pelvic bob.
- **`blend_stickman_poses(pose_a, pose_b, t)`**:
  Cubic Hermite smoothstep blending ($s(t) = 3t^2 - 2t^3$) across all joints, ensuring zero teleport jumps.

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

### Pencil2D Executable Prerequisite (Optional for Headless Rendering)

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
        "PYTHONPATH": "/path/to/pencil2d-mcp/src",
        "PENCIL2D_APPIMAGE": "/path/to/pencil2d-linux-amd64-v0.7.2.AppImage"
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

### 3. Cursor IDE (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "pencil2d": {
      "command": "python3",
      "args": ["-m", "pencil2d_mcp", "serve"]
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

# Inspect animation filmstrip visually
pencil2d-mcp look animation.pclx -f 1,5,10,15,20 -o preview_strip.png --onion-skin

# Procedurally generate a stylized animation
pencil2d-mcp generate my_walk.pclx --style stickman --action walk --frames 24 --fps 24

# Read craft guide
pencil2d-mcp guide animation
pencil2d-mcp guide styles
pencil2d-mcp guide drawing_techniques

# Headlessly export animation to MP4 or GIF (supports AppImage CLI or pure-Python fallback)
pencil2d-mcp export animation.pclx -o output.mp4 --fps 24
pencil2d-mcp export animation.pclx -o preview.gif --width 800 --height 600 --pure-python

# Open project in GUI
pencil2d-mcp gui animation.pclx

# Start the MCP stdio server manually
pencil2d-mcp serve
```

---

## 🧪 Testing

Run the full unit test suite (23 unit tests):

```bash
PYTHONPATH=src python3 -m unittest discover tests
```

---

## 💬 Note from the Developer

> *"This is my first time building an MCP server as a 20-year-old solo developer! If you encounter any bugs, issues, or have feedback, please reach out directly at **[chrizmonsaji@proton.me](mailto:chrizmonsaji@proton.me)** or [open an issue on GitHub](https://github.com/chriz-3656/pencil2d-mcp/issues). Every piece of feedback helps!"*

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Maintained with ❤️ by **[chriz-3656](https://github.com/chriz-3656)** • Contact: [chrizmonsaji@proton.me](mailto:chrizmonsaji@proton.me).
