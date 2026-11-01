"""Pencil2D Core Module: Direct manipulation of .pclx project archives and CLI/GUI interactions."""

import io
import math
import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw

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
    def create(cls, file_path: Optional[str] = None, width: int = 800, height: int = 600, fps: int = 12,
               layer_names: Optional[List[str]] = None) -> "Pencil2DProject":
        """Factory method to create a new Pencil2D project instance, optionally saving to disk."""
        proj = cls(width=width, height=height, fps=fps)
        if layer_names:
            proj.layers = [l for l in proj.layers if l["type"] == 5]
            for lname in reversed(layer_names):
                proj.add_bitmap_layer(lname)
        if file_path:
            proj.save(file_path)
        return proj

    def validate(self) -> Dict[str, Any]:
        """Alias for validate_integrity()."""
        return self.validate_integrity()

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
                            name = s_elem.attrib.get("name", "Audio")
                            s_data = b""
                            if src:
                                try:
                                    s_data = zf.read(f"data/{src}")
                                except KeyError:
                                    pass
                            layer_dict["frames"][f_idx] = {
                                "src": src,
                                "name": name,
                                "bytes": s_data
                            }

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
                    src_filename = frame_data.get("src") or f"audio_{l['id']}_{f_idx:03d}.wav"
                    name = frame_data.get("name", "Audio")
                    ET.SubElement(l_el, "sound", {
                        "frame": str(f_idx),
                        "name": name,
                        "src": src_filename
                    })
                    if "bytes" in frame_data and frame_data["bytes"]:
                        file_assets[f"data/{src_filename}"] = frame_data["bytes"]

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

    def add_sound_layer(self, name: str = "Sound Layer") -> int:
        """Create a new sound layer and return its ID."""
        lid = self.next_layer_id
        self.next_layer_id += 1
        self.layers.append({
            "id": lid,
            "name": name,
            "type": 4,
            "visible": True,
            "frames": {}
        })
        return lid

    def add_layer(self, name: str, layer_type: Union[int, str] = 1, visible: bool = True) -> int:
        """Add any layer type: 1: Bitmap, 2: Vector, 4: Sound, 5: Camera."""
        type_map = {
            "bitmap": 1,
            "vector": 2,
            "sound": 4,
            "audio": 4,
            "camera": 5
        }
        if isinstance(layer_type, str):
            ltype = type_map.get(layer_type.lower(), 1)
        else:
            ltype = int(layer_type)

        lid = self.next_layer_id
        self.next_layer_id += 1

        new_layer = {
            "id": lid,
            "name": name,
            "type": ltype,
            "visible": visible,
            "frames": {}
        }
        if ltype == 5:
            new_layer["width"] = self.width
            new_layer["height"] = self.height
            new_layer["frames"][1] = {"r": 0.0, "s": 1.0, "dx": 0.0, "dy": 0.0}

        self.layers.insert(0, new_layer)
        return lid

    def remove_layer(self, layer_id_or_name: Any) -> bool:
        """Remove a layer by its ID or name."""
        for i, l in enumerate(self.layers):
            if l["id"] == layer_id_or_name or l["name"] == layer_id_or_name:
                self.layers.pop(i)
                return True
        return False

    def add_frame_image(self, layer_id_or_name: Any, frame_num: int,
                         image_bytes_or_path: Union[str, bytes, Image.Image],
                         top_left_x: Optional[int] = None, top_left_y: Optional[int] = None,
                         auto_create_layer: bool = True):
        """Add or update an image frame in a bitmap layer. Auto-creates layer if missing."""
        target_layer = None
        if layer_id_or_name is not None:
            for l in self.layers:
                if l["type"] == 1:
                    if l["id"] == layer_id_or_name or str(l["id"]) == str(layer_id_or_name) or str(l["name"]).lower() == str(layer_id_or_name).lower():
                        target_layer = l
                        break

        if target_layer is None and layer_id_or_name and auto_create_layer and isinstance(layer_id_or_name, str):
            lid = self.add_bitmap_layer(layer_id_or_name)
            target_layer = [l for l in self.layers if l["id"] == lid][0]

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

    def add_audio_clip(self, audio_path: str, frame_num: int = 1, layer_name_or_id: Optional[Any] = None) -> bool:
        """Add an audio file to a sound layer at a specific keyframe."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        target_layer = None
        for l in self.layers:
            if l["type"] == 4:
                if layer_name_or_id is None or l["id"] == layer_name_or_id or l["name"] == layer_name_or_id:
                    target_layer = l
                    break

        if target_layer is None:
            lid = self.add_sound_layer("Sound Layer")
            target_layer = [l for l in self.layers if l["id"] == lid][0]

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        base_fn = os.path.basename(audio_path)
        src_fn = f"sound_{target_layer['id']}_{frame_num:03d}_{base_fn}"

        target_layer["frames"][frame_num] = {
            "name": os.path.splitext(base_fn)[0],
            "src": src_fn,
            "bytes": audio_bytes
        }
        return True

    def set_camera_keyframe(self, frame_num: int = 1, dx: float = 0.0, dy: float = 0.0,
                             scale: float = 1.0, rotation: float = 0.0,
                             layer_name_or_id: Optional[Any] = None):
        """Set a camera keyframe with translation, zoom (scaling), and rotation."""
        cam_layer = None
        for l in self.layers:
            if l["type"] == 5:
                if layer_name_or_id is None or l["id"] == layer_name_or_id or l["name"] == layer_name_or_id:
                    cam_layer = l
                    break

        if cam_layer is None:
            lid = self.add_layer("Camera Layer", layer_type=5)
            cam_layer = [l for l in self.layers if l["id"] == lid][0]

        cam_layer["frames"][frame_num] = {
            "dx": float(dx),
            "dy": float(dy),
            "s": float(scale),
            "r": float(rotation),
        }

    def add_palette_color(self, name: str, red: int, green: int, blue: int, alpha: int = 255):
        """Add or update a color in the project palette."""
        for c in self.palette:
            if c["name"].lower() == name.lower():
                c["red"] = red
                c["green"] = green
                c["blue"] = blue
                c["alpha"] = alpha
                return
        self.palette.append({
            "name": name,
            "red": red,
            "green": green,
            "blue": blue,
            "alpha": alpha
        })

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

    def validate_integrity(self) -> Dict[str, Any]:
        """Deep sanity verification of project integrity and missing asset checks."""
        issues = []
        warnings = []

        if not self.layers:
            issues.append("Project contains no layers.")

        camera_layers = [l for l in self.layers if l["type"] == 5]
        if not camera_layers:
            warnings.append("Project has no camera layer; default canvas framing will be used.")

        bitmap_layers = [l for l in self.layers if l["type"] == 1]
        sound_layers = [l for l in self.layers if l["type"] == 4]

        total_bitmap_frames = sum(len(l["frames"]) for l in bitmap_layers)
        if not bitmap_layers or total_bitmap_frames == 0:
            warnings.append("Project contains no bitmap keyframes.")

        # Check for empty frames
        for l in bitmap_layers:
            for f_idx, f_data in l["frames"].items():
                if not f_data.get("bytes"):
                    issues.append(f"Layer '{l['name']}' frame {f_idx} has empty image data.")

        return {
            "status": "valid" if not issues else "invalid",
            "is_valid": len(issues) == 0,
            "errors": issues,
            "warnings": warnings,
            "metrics": {
                "layers_count": len(self.layers),
                "bitmap_layers": len(bitmap_layers),
                "sound_layers": len(sound_layers),
                "camera_layers": len(camera_layers),
                "total_frames": max([max(l["frames"].keys()) for l in self.layers if l["frames"]] or [1]),
                "fps": self.fps,
                "resolution": f"{self.width}x{self.height}"
            }
        }

    def generate_spritesheet(self, output_path: str, layer_name_or_id: Optional[Any] = None,
                              columns: Optional[int] = None) -> Dict[str, Any]:
        """Pack bitmap frames into an organized spritesheet image."""
        target_layer = None
        for l in self.layers:
            if l["type"] == 1:
                if layer_name_or_id is None or l["id"] == layer_name_or_id or l["name"] == layer_name_or_id:
                    target_layer = l
                    break

        if not target_layer or not target_layer["frames"]:
            raise ValueError("No frames found to generate spritesheet.")

        frame_numbers = sorted(list(target_layer["frames"].keys()))
        total_frames = len(frame_numbers)

        cols = columns if columns and columns > 0 else total_frames
        rows = math.ceil(total_frames / cols)

        sheet_w = cols * self.width
        sheet_h = rows * self.height

        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

        frame_metadata = []

        for idx, f_num in enumerate(frame_numbers):
            fdata = target_layer["frames"][f_num]
            if fdata.get("bytes"):
                frame_img = Image.open(io.BytesIO(fdata["bytes"])).convert("RGBA")
                row = idx // cols
                col = idx % cols
                pos_x = col * self.width
                pos_y = row * self.height
                sheet.paste(frame_img, (pos_x, pos_y), frame_img)
                frame_metadata.append({
                    "frame": f_num,
                    "x": pos_x,
                    "y": pos_y,
                    "width": self.width,
                    "height": self.height
                })

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        sheet.save(output_path, format="PNG")

        return {
            "spritesheet_path": output_path,
            "dimensions": f"{sheet_w}x{sheet_h}",
            "columns": cols,
            "rows": rows,
            "total_frames": total_frames,
            "frames": frame_metadata
        }

    def render_frame(self, frame_num: int) -> Image.Image:
        """Render a single composited frame as an RGBA Image from all visible bitmap layers."""
        canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        # Composite from bottom layer to top layer
        for l in reversed(self.layers):
            if l.get("type") != 1 or not l.get("visible", True):
                continue
            frames = l.get("frames", {})
            if not frames:
                continue
            # Find active keyframe (hold frame principle)
            active_frame_key = None
            for k in sorted(frames.keys()):
                if k <= frame_num:
                    active_frame_key = k
                else:
                    break
            if active_frame_key is not None and active_frame_key in frames:
                fdata = frames[active_frame_key]
                img_bytes = fdata.get("bytes")
                if img_bytes:
                    try:
                        frame_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                        top_x = fdata.get("top_left_x", -self.width // 2)
                        top_y = fdata.get("top_left_y", -self.height // 2)
                        px = int(top_x + self.width / 2)
                        py = int(top_y + self.height / 2)
                        opacity = float(fdata.get("opacity", 1.0))
                        if opacity < 1.0:
                            r, g, b, a = frame_img.split()
                            a = a.point(lambda p: int(p * opacity))
                            frame_img.putalpha(a)
                        canvas.paste(frame_img, (px, py), frame_img)
                    except Exception:
                        pass
        return canvas

    def export_sequence(self, output_dir: str, start_frame: Optional[int] = None,
                        end_frame: Optional[int] = None, prefix: str = "frame_") -> List[str]:
        """Export composited animation frames as PNG sequence into output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        max_f = max([max(l["frames"].keys()) for l in self.layers if l.get("frames")] or [1])
        s_frame = max(1, start_frame or self.mark_in)
        e_frame = max(s_frame, end_frame or max(max_f, self.mark_out))
        paths = []
        for f_idx in range(s_frame, e_frame + 1):
            img = self.render_frame(f_idx)
            out_p = os.path.join(output_dir, f"{prefix}{f_idx:04d}.png")
            img.save(out_p, format="PNG")
            paths.append(out_p)
        return paths

    def export_gif(self, output_path: str, start_frame: Optional[int] = None,
                    end_frame: Optional[int] = None, fps: Optional[int] = None,
                    loop: int = 0) -> bool:
        """Pure-Python fallback to render and export animation as animated GIF."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        max_f = max([max(l["frames"].keys()) for l in self.layers if l.get("frames")] or [1])
        s_frame = max(1, start_frame or self.mark_in)
        e_frame = max(s_frame, end_frame or max(max_f, self.mark_out))
        use_fps = fps or self.fps or 12
        duration_ms = max(20, int(1000 / use_fps))

        frames = []
        for f_idx in range(s_frame, e_frame + 1):
            img = self.render_frame(f_idx)
            frames.append(img)

        if not frames:
            return False

        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=loop,
            disposal=2
        )
        return True

    def generate_preview_strip(self, frames: Optional[List[int]] = None,
                               frame_count: int = 6, thumb_width: int = 240,
                               onion_skin: bool = False,
                               output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        """Generate a visual verification filmstrip (contact sheet) of key animation frames."""
        max_f = max([max(l["frames"].keys()) for l in self.layers if l.get("frames")] or [1])
        start_f = max(1, self.mark_in)
        end_f = max(start_f, max(max_f, self.mark_out))

        if frames:
            sample_frames = sorted(list(set(frames)))
        else:
            fc = max(2, min(frame_count, end_f - start_f + 1))
            if end_f == start_f:
                sample_frames = [start_f]
            else:
                step = (end_f - start_f) / float(fc - 1)
                sample_frames = sorted(list(set([round(start_f + i * step) for i in range(fc)])))

        # Determine thumbnail dimensions
        aspect = self.height / float(max(1, self.width))
        tw = thumb_width
        th = int(tw * aspect)
        header_h = 24
        pad = 12

        total_w = pad + len(sample_frames) * (tw + pad)
        total_h = pad * 2 + th + header_h

        strip = Image.new("RGBA", (total_w, total_h), (24, 24, 30, 255))
        draw = ImageDraw.Draw(strip)

        for idx, f_num in enumerate(sample_frames):
            x = pad + idx * (tw + pad)
            y = pad

            # Frame card background
            draw.rectangle([x, y, x + tw, y + th + header_h], fill=(36, 36, 46, 255), outline=(55, 55, 70, 255))

            # Header badge with frame index
            draw.rectangle([x, y, x + tw, y + header_h], fill=(48, 48, 62, 255))
            label = f"Frame {f_num}"
            draw.text((x + 8, y + 4), label, fill=(225, 225, 235, 255))

            # Render frame
            curr_frame = self.render_frame(f_num)

            # Optional onion skinning (blend previous frame at 30% opacity in cool tint)
            if onion_skin and f_num > start_f:
                prev_frame = self.render_frame(f_num - 1)
                onion = prev_frame.convert("RGBA")
                r, g, b, a = onion.split()
                a = a.point(lambda p: int(p * 0.35))
                onion.putalpha(a)
                curr_frame = Image.alpha_composite(curr_frame, onion)

            # Resize to thumbnail
            thumb = curr_frame.resize((tw, th), Image.Resampling.LANCZOS)
            strip.paste(thumb, (x, y + header_h), thumb)

        if not output_path:
            import tempfile
            fd, output_path = tempfile.mkstemp(prefix="pencil2d_strip_", suffix=".png")
            os.close(fd)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        strip.save(output_path, format="PNG")
        return strip, output_path


def export_project(project_path: str, output_path: str,
                   width: Optional[int] = None, height: Optional[int] = None,
                   fps: Optional[int] = None,
                   start_frame: Optional[int] = None, end_frame: Optional[int] = None,
                   camera: Optional[str] = None, transparency: bool = False,
                   timeout: int = 180, force_pure_python: bool = False,
                   appimage_path: Optional[str] = None) -> Tuple[bool, str]:
    """Render a Pencil2D project using AppImage CLI, with automatic headless support and pure-Python fallback."""
    app_bin = appimage_path or get_appimage_path()
    ext = os.path.splitext(output_path)[1].lower()

    # If pure-Python fallback requested or AppImage not present:
    if force_pure_python or not app_bin or not os.path.exists(app_bin):
        try:
            proj = Pencil2DProject.load(project_path)
            if ext == ".gif":
                ok = proj.export_gif(output_path, start_frame=start_frame, end_frame=end_frame, fps=fps)
                if ok:
                    return True, f"Export completed via pure-Python compositor to {output_path}."
                return False, "Failed to generate GIF frames."
            elif ext == ".png":
                target_frame = start_frame or proj.current_frame or 1
                img = proj.render_frame(target_frame)
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                img.save(output_path, format="PNG")
                return True, f"Exported frame {target_frame} via pure-Python compositor to {output_path}."
            elif ext == ".mp4":
                if shutil.which("ffmpeg"):
                    import tempfile
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        proj.export_sequence(tmp_dir, start_frame=start_frame, end_frame=end_frame)
                        use_fps = fps or proj.fps or 12
                        ffmpeg_cmd = [
                            "ffmpeg", "-y", "-framerate", str(use_fps),
                            "-i", os.path.join(tmp_dir, "frame_%04d.png"),
                            "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            os.path.abspath(output_path)
                        ]
                        res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
                        if res.returncode == 0 and os.path.exists(output_path):
                            return True, f"Rendered MP4 via FFmpeg fallback to {output_path}."
                        return False, f"FFmpeg error: {res.stderr}"
                return False, "Pencil2D executable not found and FFmpeg is not installed for MP4 export."
            else:
                return False, f"Unsupported format for pure-Python fallback: {ext}"
        except Exception as e:
            if not app_bin or not os.path.exists(app_bin):
                return False, f"Pencil2D executable not found and fallback failed: {str(e)}"

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
    has_display = bool(env.get("DISPLAY"))
    # Headless auto-detection: wrap with xvfb-run if available
    if not has_display and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a"] + cmd
    elif not has_display:
        env["DISPLAY"] = ":0.0"

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=timeout)
        output = (proc.stdout + "\n" + proc.stderr).strip()
        if proc.returncode == 0:
            return True, f"Export completed successfully to {output_path}.\n{output}"
        else:
            # Fallback to pure-Python GIF export if CLI fails
            if ext == ".gif":
                try:
                    proj = Pencil2DProject.load(project_path)
                    if proj.export_gif(output_path, start_frame=start_frame, end_frame=end_frame, fps=fps):
                        return True, f"Pencil2D CLI returned {proc.returncode}; successfully exported via pure-Python fallback: {output_path}"
                except Exception:
                    pass
            return False, f"Export failed with code {proc.returncode}:\n{output}"
    except subprocess.TimeoutExpired:
        if ext == ".gif":
            try:
                proj = Pencil2DProject.load(project_path)
                if proj.export_gif(output_path, start_frame=start_frame, end_frame=end_frame, fps=fps):
                    return True, f"Pencil2D CLI timed out; exported via pure-Python fallback: {output_path}"
            except Exception:
                pass
        return False, f"Export execution timed out after {timeout} seconds."
    except Exception as e:
        return False, f"Export execution error: {str(e)}"

def launch_gui(project_path: Optional[str] = None, appimage_path: Optional[str] = None) -> Tuple[bool, str]:
    """Launch Pencil2D in visual GUI mode as a detached background process."""
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
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True, f"Launched Pencil2D GUI (PID {proc.pid}) with project: {project_path or 'New Workspace'}"
    except Exception as e:
        return False, f"Failed to launch GUI: {str(e)}"

# Convenient API aliases
render_animation = export_project
