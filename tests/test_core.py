"""Unit tests for Pencil2DProject core class."""

import os
import shutil
import tempfile
import unittest
from PIL import Image, ImageDraw

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
        # Create a test image
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

    def test_appimage_detection(self):
        path = get_appimage_path()
        # Even if not present in all test runner environments, function should return str or None
        self.assertTrue(path is None or isinstance(path, str))

if __name__ == "__main__":
    unittest.main()
