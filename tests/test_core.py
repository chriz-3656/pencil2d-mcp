"""Unit tests for Pencil2DProject core class."""

import os
import shutil
import tempfile
import unittest
from PIL import Image

from pencil2d_mcp.core import Pencil2DProject, get_appimage_path

class TestPencil2DProject(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.test_dir, "test.pclx")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_and_save_project(self):
        proj = Pencil2DProject(width=1280, height=720, fps=24)
        self.assertEqual(proj.width, 1280)
        self.assertEqual(proj.height, 720)
        self.assertEqual(proj.fps, 24)

        proj.save(self.project_path)
        self.assertTrue(os.path.exists(self.project_path))
        self.assertGreater(os.path.getsize(self.project_path), 0)

    def test_roundtrip_load(self):
        proj = Pencil2DProject(width=1000, height=800, fps=15)
        img = Image.new("RGBA", (1000, 800), (255, 0, 0, 255))
        proj.add_frame_image("Bitmap Layer", 1, img)
        proj.save(self.project_path)

        loaded = Pencil2DProject.load(self.project_path)
        self.assertEqual(loaded.width, 1000)
        self.assertEqual(loaded.height, 800)
        self.assertEqual(loaded.fps, 15)

        summary = loaded.inspect_summary()
        self.assertEqual(summary["resolution"], "1000x800")
        self.assertEqual(summary["fps"], 15)
        self.assertEqual(summary["total_layers"], 2)

        bitmap_layer = [l for l in loaded.layers if l["type"] == 1][0]
        self.assertIn(1, bitmap_layer["frames"])
        self.assertGreater(len(bitmap_layer["frames"][1]["bytes"]), 0)

    def test_layer_management(self):
        proj = Pencil2DProject()
        lid = proj.add_layer("Ink Layer", layer_type="bitmap")
        self.assertTrue(any(l["id"] == lid for l in proj.layers))

        removed = proj.remove_layer("Ink Layer")
        self.assertTrue(removed)
        self.assertFalse(any(l["name"] == "Ink Layer" for l in proj.layers))

    def test_camera_and_palette(self):
        proj = Pencil2DProject()
        proj.set_camera_keyframe(frame_num=5, dx=50.0, dy=-20.0, scale=1.2, rotation=5.0)
        cam_layer = [l for l in proj.layers if l["type"] == 5][0]
        self.assertIn(5, cam_layer["frames"])
        self.assertEqual(cam_layer["frames"][5]["s"], 1.2)

        proj.add_palette_color("SkinTone", 240, 200, 180)
        self.assertTrue(any(c["name"] == "SkinTone" for c in proj.palette))

    def test_spritesheet_generation(self):
        proj = Pencil2DProject(width=100, height=100)
        img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        img2 = Image.new("RGBA", (100, 100), (0, 255, 0, 255))
        proj.add_frame_image("Bitmap Layer", 1, img1)
        proj.add_frame_image("Bitmap Layer", 2, img2)

        sheet_out = os.path.join(self.test_dir, "sheet.png")
        res = proj.generate_spritesheet(sheet_out, columns=2)
        self.assertTrue(os.path.exists(sheet_out))
        self.assertEqual(res["total_frames"], 2)
        self.assertEqual(res["columns"], 2)

    def test_validation(self):
        proj = Pencil2DProject()
        val = proj.validate_integrity()
        self.assertTrue(val["is_valid"])
        # Test validate() alias
        val_alias = proj.validate()
        self.assertEqual(val["is_valid"], val_alias["is_valid"])

    def test_create_factory_method(self):
        proj = Pencil2DProject.create(
            file_path=self.project_path,
            width=640,
            height=480,
            fps=20,
            layer_names=["Background", "Character", "Foreground"]
        )
        self.assertEqual(proj.width, 640)
        self.assertEqual(proj.height, 480)
        self.assertEqual(proj.fps, 20)
        self.assertTrue(os.path.exists(self.project_path))
        # Check layer order preserves input order
        bitmap_layer_names = [l["name"] for l in proj.layers if l["type"] == 1]
        self.assertEqual(bitmap_layer_names, ["Background", "Character", "Foreground"])

    def test_auto_create_layer(self):
        proj = Pencil2DProject()
        img = Image.new("RGBA", (100, 100), (0, 0, 255, 255))
        # Target layer "Hair Layer" does not exist yet; auto_create_layer should create it
        proj.add_frame_image("Hair Layer", 1, img, auto_create_layer=True)
        self.assertTrue(any(l["name"] == "Hair Layer" for l in proj.layers))

    def test_pure_python_rendering_and_gif(self):
        proj = Pencil2DProject(width=200, height=200, fps=10)
        img1 = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
        img2 = Image.new("RGBA", (200, 200), (0, 255, 0, 255))
        proj.add_frame_image("Bitmap Layer", 1, img1)
        proj.add_frame_image("Bitmap Layer", 2, img2)

        # Test single frame compositing
        frame_1 = proj.render_frame(1)
        self.assertEqual(frame_1.size, (200, 200))

        # Test GIF export
        gif_out = os.path.join(self.test_dir, "test_render.gif")
        ok = proj.export_gif(gif_out, start_frame=1, end_frame=2)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(gif_out))
        self.assertGreater(os.path.getsize(gif_out), 0)

    def test_appimage_detection(self):
        path = get_appimage_path()
        self.assertTrue(path is None or isinstance(path, str))

if __name__ == "__main__":
    unittest.main()
