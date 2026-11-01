"""Unit tests for Articulated Kinematics, IK, and Locomotion Engine."""

import math
import unittest
from PIL import Image

from pencil2d_mcp.drawing import (
    StickmanPose,
    blend_stickman_poses,
    generate_locomotion_pose,
    render_smooth_stickman,
    solve_2bone_ik,
)


class TestKinematicsEngine(unittest.TestCase):

    def test_solve_2bone_ik_lengths(self):
        root = (100.0, 100.0)
        target = (130.0, 140.0)
        l1, l2 = 30.0, 30.0
        joint = solve_2bone_ik(root, target, l1, l2, bend_positive=True)

        d1 = math.hypot(joint[0] - root[0], joint[1] - root[1])
        d2 = math.hypot(target[0] - joint[0], target[1] - joint[1])

        self.assertAlmostEqual(d1, l1, places=3)
        self.assertAlmostEqual(d2, l2, places=3)

    def test_solve_2bone_ik_reach_clamping(self):
        # Target beyond max reach: should not crash, must clamp smoothly
        root = (0.0, 0.0)
        target = (200.0, 0.0)
        l1, l2 = 40.0, 40.0
        joint = solve_2bone_ik(root, target, l1, l2, bend_positive=True)
        d1 = math.hypot(joint[0] - root[0], joint[1] - root[1])
        self.assertAlmostEqual(d1, l1, places=3)

    def test_blend_stickman_poses_continuity(self):
        pose_a = generate_locomotion_pose(100.0, 300.0, 0.0, facing=1, speed=1.0)
        pose_b = generate_locomotion_pose(200.0, 300.0, 0.5, facing=1, speed=2.0)

        mid_pose = blend_stickman_poses(pose_a, pose_b, 0.5)

        # Check midpoint continuity on pelvis and head
        expected_pelvis_x = (pose_a.pelvis[0] + pose_b.pelvis[0]) * 0.5
        self.assertAlmostEqual(mid_pose.pelvis[0], expected_pelvis_x, places=2)
        expected_head_x = (pose_a.head[0] + pose_b.head[0]) * 0.5
        self.assertAlmostEqual(mid_pose.head[0], expected_head_x, places=2)

    def test_locomotion_gait_ground_contact(self):
        ground_y = 400.0
        # Over a full cycle, both feet should touch or plant on ground_y
        min_foot_l_y = 999.0
        min_foot_r_y = 999.0
        max_foot_l_y = 0.0
        max_foot_r_y = 0.0

        for step in range(20):
            phase = step / 20.0
            pose = generate_locomotion_pose(200.0 + step * 5.0, ground_y, phase, facing=1, speed=1.0)
            min_foot_l_y = min(min_foot_l_y, pose.l_foot[1])
            max_foot_l_y = max(max_foot_l_y, pose.l_foot[1])
            min_foot_r_y = min(min_foot_r_y, pose.r_foot[1])
            max_foot_r_y = max(max_foot_r_y, pose.r_foot[1])

        # Maximum y should be exactly ground_y (stance foot on ground)
        self.assertAlmostEqual(max_foot_l_y, ground_y, places=2)
        self.assertAlmostEqual(max_foot_r_y, ground_y, places=2)
        # Minimum y should be higher (swing foot clears ground)
        self.assertLess(min_foot_l_y, ground_y - 8.0)
        self.assertLess(min_foot_r_y, ground_y - 8.0)

    def test_render_smooth_stickman(self):
        canvas = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        pose = generate_locomotion_pose(200.0, 350.0, 0.25, facing=1, speed=1.5, weapon="katana")
        render_smooth_stickman(canvas, pose, (20, 20, 30, 255), (255, 50, 50, 255), frame_num=10, aura_type="fire")
        # Ensure pixels were actually drawn
        bbox = canvas.getbbox()
        self.assertIsNotNone(bbox)
        self.assertGreater(bbox[2] - bbox[0], 50)
        self.assertGreater(bbox[3] - bbox[1], 80)


if __name__ == "__main__":
    unittest.main()
