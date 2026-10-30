"""Unit tests for Pencil2D MCP Server protocol handler."""

import json
import os
import shutil
import tempfile
import unittest

from pencil2d_mcp.server import TOOLS, handle_call_tool

class TestMCPServer(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.test_dir, "test_mcp.pclx")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tools_list_spec(self):
        self.assertGreaterEqual(len(TOOLS), 14)
        names = [t["name"] for t in TOOLS]
        self.assertIn("pencil2d_inspect", names)
        self.assertIn("pencil2d_create", names)
        self.assertIn("pencil2d_add_frame", names)
        self.assertIn("pencil2d_add_frames_batch", names)
        self.assertIn("pencil2d_add_layer", names)
        self.assertIn("pencil2d_remove_layer", names)
        self.assertIn("pencil2d_add_audio", names)
        self.assertIn("pencil2d_set_camera", names)
        self.assertIn("pencil2d_manage_palette", names)
        self.assertIn("pencil2d_create_spritesheet", names)
        self.assertIn("pencil2d_validate", names)
        self.assertIn("pencil2d_extract_frames", names)
        self.assertIn("pencil2d_export", names)
        self.assertIn("pencil2d_launch_gui", names)

    def test_create_and_inspect_tools(self):
        create_res_raw = handle_call_tool("pencil2d_create", {
            "project_path": self.project_path,
            "width": 640,
            "height": 480,
            "fps": 24,
            "layer_names": ["Inking Layer"]
        })
        create_res = json.loads(create_res_raw)
        self.assertEqual(create_res["status"], "success")
        self.assertTrue(os.path.exists(self.project_path))

        inspect_res_raw = handle_call_tool("pencil2d_inspect", {
            "project_path": self.project_path
        })
        inspect_res = json.loads(inspect_res_raw)
        self.assertEqual(inspect_res["resolution"], "640x480")
        self.assertEqual(inspect_res["fps"], 24)
        layer_names = [l["name"] for l in inspect_res["layers"]]
        self.assertIn("Inking Layer", layer_names)

    def test_validate_and_palette_tools(self):
        handle_call_tool("pencil2d_create", {"project_path": self.project_path})

        val_raw = handle_call_tool("pencil2d_validate", {"project_path": self.project_path})
        val = json.loads(val_raw)
        self.assertTrue(val["is_valid"])

        pal_raw = handle_call_tool("pencil2d_manage_palette", {
            "project_path": self.project_path,
            "color_name": "SkyBlue",
            "red": 100,
            "green": 180,
            "blue": 240
        })
        pal = json.loads(pal_raw)
        self.assertEqual(pal["status"], "success")

    def test_unknown_tool(self):
        res_raw = handle_call_tool("non_existent_tool", {})
        res = json.loads(res_raw)
        self.assertIn("error", res)

if __name__ == "__main__":
    unittest.main()
