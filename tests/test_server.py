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
        self.assertIn("pencil2d_look", names)
        self.assertIn("pencil2d_generate_animation", names)
        self.assertIn("pencil2d_get_guide", names)

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

    def test_export_tool_pure_python(self):
        handle_call_tool("pencil2d_create", {"project_path": self.project_path, "width": 100, "height": 100})
        out_gif = os.path.join(self.test_dir, "mcp_export.gif")
        res_raw = handle_call_tool("pencil2d_export", {
            "project_path": self.project_path,
            "output_path": out_gif,
            "fps": 12,
            "force_pure_python": True
        })
        res = json.loads(res_raw)
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(out_gif))

    def test_unknown_tool(self):
        res_raw = handle_call_tool("non_existent_tool", {})
        res = json.loads(res_raw)
        self.assertIn("error", res)

    def test_get_guide_tool(self):
        guide_text = handle_call_tool("pencil2d_get_guide", {"topic": "animation"})
        self.assertIn("2D Animation Principles", guide_text)
        self.assertIn("Squash and Stretch", guide_text)

        styles_text = handle_call_tool("pencil2d_get_guide", {"topic": "styles"})
        self.assertIn("Dynamic Stickman", styles_text)
        self.assertIn("Anime & Manga", styles_text)
        self.assertIn("Studio Ghibli", styles_text)

    def test_generate_animation_and_look_tools(self):
        # Generate stylized stickman animation
        gen_res_raw = handle_call_tool("pencil2d_generate_animation", {
            "project_path": self.project_path,
            "style": "stickman",
            "action": "jump",
            "frame_count": 6
        })
        gen_res = json.loads(gen_res_raw)
        self.assertEqual(gen_res["status"], "success")
        self.assertEqual(gen_res["frames_count"], 6)
        self.assertTrue(os.path.exists(self.project_path))

        # Test pencil2d_look in strip mode
        look_res_raw = handle_call_tool("pencil2d_look", {
            "project_path": self.project_path,
            "mode": "strip",
            "frame_count": 4,
            "onion_skin": True
        })
        look_res = json.loads(look_res_raw)
        self.assertEqual(look_res["status"], "success")
        self.assertEqual(look_res["mode"], "strip")
        self.assertTrue(os.path.exists(look_res["preview_strip_path"]))

        # Test pencil2d_look in single frame mode
        frame_res_raw = handle_call_tool("pencil2d_look", {
            "project_path": self.project_path,
            "mode": "frame",
            "frame": 2
        })
        frame_res = json.loads(frame_res_raw)
        self.assertEqual(frame_res["status"], "success")
        self.assertEqual(frame_res["mode"], "frame")
        self.assertTrue(os.path.exists(frame_res["preview_path"]))

    def test_all_art_styles_generation(self):
        for style_name in ["anime", "pencil_sketch", "ghibli", "doodle"]:
            target_proj = os.path.join(self.test_dir, f"test_{style_name}.pclx")
            res_raw = handle_call_tool("pencil2d_generate_animation", {
                "project_path": target_proj,
                "style": style_name,
                "frame_count": 4
            })
            res = json.loads(res_raw)
            self.assertEqual(res["status"], "success")
            self.assertTrue(os.path.exists(target_proj))

if __name__ == "__main__":
    unittest.main()
