"""Pencil2D Core Module: Direct manipulation of .pclx project archives and CLI/GUI interactions."""

import io
import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

DEFAULT_APPIMAGE_SEARCH_PATHS = [
    "/home/demo/Downloads/pencil2d-linux-amd64-v0.7.2.AppImage",
    os.path.expanduser("~/Downloads/pencil2d-linux-amd64-v0.7.2.AppImage"),
    os.path.expanduser("~/Applications/pencil2d.AppImage"),
    "/usr/local/bin/pencil2d",
    "/usr/bin/pencil2d",
]

def get_appimage_path() -> Optional[str]:
    """Find the Pencil2D AppImage or executable on the system."""
    env_path = os.environ.get("PENCIL2D_APPIMAGE") or os.environ.get("PENCIL2D_PATH")
    if env_path and os.path.exists(env_path) and os.access(env_path, os.X_OK):
        return os.path.abspath(env_path)

    which_path = shutil.which("pencil2d")
    if which_path:
        return which_path

    for candidate in DEFAULT_APPIMAGE_SEARCH_PATHS:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return os.path.abspath(candidate)

    # Check for any pencil2d*.AppImage in ~/Downloads or /tmp
    search_dirs = [
        os.path.expanduser("~/Downloads"),
        "/home/demo/Downloads",
        os.path.expanduser("~"),
        "/tmp",
    ]
    for d in search_dirs:
        if os.path.isdir(d):
            try:
                for fn in os.listdir(d):
                    if fn.lower().startswith("pencil2d") and fn.lower().endswith(".appimage"):
                        full_p = os.path.join(d, fn)
                        if os.access(full_p, os.X_OK):
                            return os.path.abspath(full_p)
            except OSError:
                pass

    return None

class Pencil2DProject:
    """In-memory representation and serializer for Pencil2D (.pclx) projects."""

    def __init__(self, width: int = 800, height: int = 600, fps: int = 12):
        self.width = width
        self.height = height
        self.fps = fps
        self.current_frame = 1
        self.mark_in = 1
        self.mark_out = 12
        self.is_loop = True
        self.palette: List[Dict[str, Any]] = [
            {"name": "Black", "red": 0, "green": 0, "blue": 0, "alpha": 255},
            {"name": "White", "red": 255, "green": 255, "blue": 255, "alpha": 255},
            {"name": "Red", "red": 230, "green": 50, "blue": 50, "alpha": 255},
            {"name": "Blue", "red": 50, "green": 120, "blue": 230, "alpha": 255},
            {"name": "Yellow", "red": 240, "green": 210, "blue": 40, "alpha": 255},
            {"name": "Green", "red": 40, "green": 180, "blue": 70, "alpha": 255},
        ]
        self.layers: List[Dict[str, Any]] = []
        # Layer 1: Bitmap Layer (type 1)
        self.layers.append({
            "id": 1,
            "name": "Bitmap Layer",
            "type": 1,
            "visible": True,
            "frames": {}
        })
        # Layer 2: Camera Layer (type 5)
        self.layers.append({
            "id": 2,
            "name": "Camera Layer",
            "type": 5,
            "visible": True,
            "width": width,
            "height": height,
            "frames": {
                1: {"r": 0.0, "s": 1.0, "dx": 0.0, "dy": 0.0}
            }
        })
        self.next_layer_id = 3

    @classmethod
    def load(cls, file_path: str) -> "Pencil2DProject":
        """Load a .pclx project from disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Pencil2D project file not found: {file_path}")

        proj = cls()
        proj.layers = []

        with zipfile.ZipFile(file_path, "r") as zf:
            main_xml_bytes = zf.read("main.xml")
            root = ET.fromstring(main_xml_bytes)

            projdata = root.find("projectdata")
            if projdata is not None:
                fps_elem = projdata.find("fps")
                if fps_elem is not None and "value" in fps_elem.attrib:
                    proj.fps = int(fps_elem.attrib["value"])
                curr_elem = projdata.find("currentFrame")
                if curr_elem is not None and "value" in curr_elem.attrib:
                    proj.current_frame = int(curr_elem.attrib["value"])
                in_elem = projdata.find("markInFrame")
                if in_elem is not None and "value" in in_elem.attrib:
                    proj.mark_in = int(in_elem.attrib["value"])
                out_elem = projdata.find("markOutFrame")
                if out_elem is not None and "value" in out_elem.attrib:
                    proj.mark_out = int(out_elem.attrib["value"])

            try:
                pal_bytes = zf.read("data/palette.xml")
                pal_root = ET.fromstring(pal_bytes)
                proj.palette = []
                for c in pal_root.findall("Color"):
                    proj.palette.append({
                        "name": c.attrib.get("name", "Color"),
                        "red": int(c.attrib.get("red", 0)),
                        "green": int(c.attrib.get("green", 0)),
                        "blue": int(c.attrib.get("blue", 0)),
                        "alpha": int(c.attrib.get("alpha", 255)),
                    })
            except KeyError:
                pass

            obj_elem = root.find("object")
            max_id = 0
            if obj_elem is not None:
                for layer_el in obj_elem.findall("layer"):
                    lid = int(layer_el.attrib.get("id", 1))
                    max_id = max(max_id, lid)
                    ltype = int(layer_el.attrib.get("type", 1))
                    lname = layer_el.attrib.get("name", f"Layer {lid}")
                    lvis = bool(int(layer_el.attrib.get("visibility", 1)))

                    layer_dict: Dict[str, Any] = {
                        "id": lid,
                        "name": lname,
                        "type": ltype,
                        "visible": lvis,
                        "frames": {}
                    }

                    if ltype == 5: # Camera
                        w = int(layer_el.attrib.get("width", 800))
                        h = int(layer_el.attrib.get("height", 600))
                        layer_dict["width"] = w
                        layer_dict["height"] = h
                        proj.width = w
                        proj.height = h
                        for c_elem in layer_el.findall("camera"):
                            f_idx = int(c_elem.attrib.get("frame", 1))
                            layer_dict["frames"][f_idx] = {
                                "r": float(c_elem.attrib.get("r", 0.0)),
                                "s": float(c_elem.attrib.get("s", 1.0)),
                                "dx": float(c_elem.attrib.get("dx", 0.0)),
                                "dy": float(c_elem.attrib.get("dy", 0.0)),
                            }
                    elif ltype == 1: # Bitmap
                        for img_elem in layer_el.findall("image"):
                            f_idx = int(img_elem.attrib.get("frame", 1))
                            src = img_elem.attrib.get("src", "")
                            top_x = int(img_elem.attrib.get("topLeftX", 0))
                            top_y = int(img_elem.attrib.get("topLeftY", 0))
                            opacity = float(img_elem.attrib.get("opacity", 1.0))
                            img_data = b""
                            if src:
                                try:
                                    img_data = zf.read(f"data/{src}")
                                except KeyError:
                                    pass
                            layer_dict["frames"][f_idx] = {
                                "src": src,
                                "bytes": img_data,
                                "top_left_x": top_x,
                                "top_left_y": top_y,
                                "opacity": opacity,
                            }
                    elif ltype == 2: # Vector
                        for v_elem in layer_el.findall("vector"):
                            f_idx = int(v_elem.attrib.get("frame", 1))
                            src = v_elem.attrib.get("src", "")
                            v_data = b""
                            if src:
                                try:
                                    v_data = zf.read(f"data/{src}")
                                except KeyError:
                                    pass
                            layer_dict["frames"][f_idx] = {
                                "src": src,
                                "bytes": v_data
                            }
                    elif ltype == 4: # Sound
                        for s_elem in layer_el.findall("sound"):
                            f_idx = int(s_elem.attrib.get("frame", 1))
                            src = s_elem.attrib.get("src", "")
                            layer_dict["frames"][f_idx] = {"src": src}

                    proj.layers.append(layer_dict)

            proj.next_layer_id = max_id + 1

        return proj

    def save(self, file_path: str):
        """Save the project state to a .pclx file."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        doc = ET.Element("document")
        projdata = ET.SubElement(doc, "projectdata")
        ET.SubElement(projdata, "currentFrame", {"value": str(self.current_frame)})
        ET.SubElement(projdata, "currentColor", {"r": "0", "g": "0", "b": "0", "a": "255"})
        ET.SubElement(projdata, "currentLayer", {"value": "1"})
        ET.SubElement(projdata, "currentView", {"m11": "1", "m12": "0", "m21": "0", "m22": "1", "dx": "0", "dy": "0"})
        ET.SubElement(projdata, "fps", {"value": str(self.fps)})
        ET.SubElement(projdata, "isLoop", {"value": "true" if self.is_loop else "false"})
        ET.SubElement(projdata, "isRangedPlayback", {"value": "false"})
        ET.SubElement(projdata, "markInFrame", {"value": str(self.mark_in)})

        max_f = 1
        for l in self.layers:
            if l["frames"]:
                max_f = max(max_f, max(l["frames"].keys()))
        ET.SubElement(projdata, "markOutFrame", {"value": str(max(max_f, self.mark_out))})

        obj_el = ET.SubElement(doc, "object")
        file_assets: Dict[str, bytes] = {}

        for l in self.layers:
            layer_attrib = {
                "id": str(l["id"]),
                "name": str(l["name"]),
                "visibility": "1" if l.get("visible", True) else "0",
                "type": str(l["type"])
            }
            if l["type"] == 5: # Camera
                layer_attrib["width"] = str(l.get("width", self.width))
                layer_attrib["height"] = str(l.get("height", self.height))
                l_el = ET.SubElement(obj_el, "layer", layer_attrib)
                for f_idx, cam_data in sorted(l["frames"].items()):
                    ET.SubElement(l_el, "camera", {
                        "frame": str(f_idx),
                        "r": str(cam_data.get("r", 0.0)),
                        "s": str(cam_data.get("s", 1.0)),
                        "dx": str(cam_data.get("dx", 0.0)),
                        "dy": str(cam_data.get("dy", 0.0)),
                    })
            elif l["type"] == 1: # Bitmap
                l_el = ET.SubElement(obj_el, "layer", layer_attrib)
                for f_idx, frame_data in sorted(l["frames"].items()):
                    filename = f"{l['id']:03d}.{f_idx:03d}.png"
                    top_x = frame_data.get("top_left_x", -self.width // 2)
                    top_y = frame_data.get("top_left_y", -self.height // 2)
                    opacity = frame_data.get("opacity", 1.0)
                    ET.SubElement(l_el, "image", {
                        "frame": str(f_idx),
                        "src": filename,
                        "topLeftX": str(top_x),
                        "topLeftY": str(top_y),
                        "opacity": str(opacity)
                    })
                    if "bytes" in frame_data and frame_data["bytes"]:
                        file_assets[f"data/{filename}"] = frame_data["bytes"]
            elif l["type"] == 2: # Vector
                l_el = ET.SubElement(obj_el, "layer", layer_attrib)
                for f_idx, frame_data in sorted(l["frames"].items()):
                    filename = f"{l['id']:03d}.{f_idx:03d}.vec"
                    ET.SubElement(l_el, "vector", {
                        "frame": str(f_idx),
                        "src": filename
                    })
                    if "bytes" in frame_data and frame_data["bytes"]:
                        file_assets[f"data/{filename}"] = frame_data["bytes"]
            elif l["type"] == 4: # Sound
                l_el = ET.SubElement(obj_el, "layer", layer_attrib)
                for f_idx, frame_data in sorted(l["frames"].items()):
                    ET.SubElement(l_el, "sound", {
                        "frame": str(f_idx),
                        "src": frame_data.get("src", "")
                    })

        xml_str = ET.tostring(doc, encoding="utf-8")
        full_xml = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE PencilDocument>\n' + xml_str

        # Build palette.xml
        pal_el = ET.Element("palette")
        for col in self.palette:
            ET.SubElement(pal_el, "Color", {
                "name": col["name"],
                "red": str(col["red"]),
                "green": str(col["green"]),
                "blue": str(col["blue"]),
                "alpha": str(col["alpha"])
            })
        pal_xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(pal_el, encoding="utf-8")
        file_assets["data/palette.xml"] = pal_xml

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("main.xml", full_xml)
            for path, data in file_assets.items():
                zf.writestr(path, data)

    def add_bitmap_layer(self, name: str = "New Bitmap Layer") -> int:
        """Create a new bitmap layer and return its ID."""
        lid = self.next_layer_id
        self.next_layer_id += 1
        self.layers.insert(0, {
            "id": lid,
            "name": name,
            "type": 1,
            "visible": True,
            "frames": {}
        })
        return lid

    def add_frame_image(self, layer_id_or_name: Any, frame_num: int,
                         image_bytes_or_path: Union[str, bytes, Image.Image],
                         top_left_x: Optional[int] = None, top_left_y: Optional[int] = None):
        """Add or update an image frame in a bitmap layer."""
        target_layer = None
        for l in self.layers:
            if l["type"] == 1:
                if l["id"] == layer_id_or_name or l["name"] == layer_id_or_name:
                    target_layer = l
                    break

        if target_layer is None:
            for l in self.layers:
                if l["type"] == 1:
                    target_layer = l
                    break

        if target_layer is None:
            self.add_bitmap_layer("Bitmap Layer")
            target_layer = self.layers[0]

        img_bytes: bytes
        if isinstance(image_bytes_or_path, str):
            with open(image_bytes_or_path, "rb") as f:
                img_bytes = f.read()
        elif isinstance(image_bytes_or_path, bytes):
            img_bytes = image_bytes_or_path
        elif isinstance(image_bytes_or_path, Image.Image):
            buf = io.BytesIO()
            image_bytes_or_path.save(buf, format="PNG")
            img_bytes = buf.getvalue()
        else:
            raise ValueError("Image must be a file path string, bytes, or a PIL Image instance.")

        if top_left_x is None:
            top_left_x = -self.width // 2
        if top_left_y is None:
            top_left_y = -self.height // 2

        target_layer["frames"][frame_num] = {
            "bytes": img_bytes,
            "top_left_x": top_left_x,
            "top_left_y": top_left_y,
            "opacity": 1.0
        }

    def inspect_summary(self) -> Dict[str, Any]:
        """Return structural metadata and keyframe summary."""
        layer_summaries = []
        total_keyframes = 0
        max_frame = 1

        for l in self.layers:
            frames_list = sorted(list(l["frames"].keys()))
            total_keyframes += len(frames_list)
            if frames_list:
                max_frame = max(max_frame, max(frames_list))
            layer_summaries.append({
                "id": l["id"],
                "name": l["name"],
                "type": {1: "Bitmap", 2: "Vector", 4: "Sound", 5: "Camera"}.get(l["type"], "Unknown"),
                "visible": l.get("visible", True),
                "frame_count": len(frames_list),
                "frames": frames_list,
            })

        return {
            "resolution": f"{self.width}x{self.height}",
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "current_frame": self.current_frame,
            "total_layers": len(self.layers),
            "total_keyframes": total_keyframes,
            "max_frame": max_frame,
            "layers": layer_summaries,
            "palette_colors_count": len(self.palette),
        }

def export_project(project_path: str, output_path: str,
                   width: Optional[int] = None, height: Optional[int] = None,
                   start_frame: Optional[int] = None, end_frame: Optional[int] = None,
                   camera: Optional[str] = None, transparency: bool = False,
                   appimage_path: Optional[str] = None) -> Tuple[bool, str]:
    """Render a Pencil2D project headlessly using the AppImage CLI."""
    app_bin = appimage_path or get_appimage_path()
    if not app_bin or not os.path.exists(app_bin):
        return False, f"Pencil2D executable not found. Set PENCIL2D_APPIMAGE env var or install Pencil2D."

    cmd = [app_bin, os.path.abspath(project_path), "-o", os.path.abspath(output_path)]
    if width:
        cmd.extend(["--width", str(width)])
    if height:
        cmd.extend(["--height", str(height)])
    if start_frame:
        cmd.extend(["--start", str(start_frame)])
    if end_frame:
        cmd.extend(["--end", str(end_frame)])
    if camera:
        cmd.extend(["--camera", camera])
    if transparency:
        cmd.append("--transparency")

    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0.0"

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=120)
        output = (proc.stdout + "\n" + proc.stderr).strip()
        if proc.returncode == 0:
            return True, f"Export completed successfully to {output_path}.\n{output}"
        else:
            return False, f"Export failed with code {proc.returncode}:\n{output}"
    except Exception as e:
        return False, f"Export execution error: {str(e)}"

def launch_gui(project_path: Optional[str] = None, appimage_path: Optional[str] = None) -> Tuple[bool, str]:
    """Launch Pencil2D in visual GUI mode as a background process."""
    app_bin = appimage_path or get_appimage_path()
    if not app_bin or not os.path.exists(app_bin):
        return False, f"Pencil2D executable not found. Set PENCIL2D_APPIMAGE env var or install Pencil2D."

    cmd = [app_bin]
    if project_path:
        cmd.append(os.path.abspath(project_path))

    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0.0"

    try:
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, f"Launched Pencil2D GUI (PID {proc.pid}) with project: {project_path or 'New Workspace'}"
    except Exception as e:
        return False, f"Failed to launch GUI: {str(e)}"
