"""Pencil2D MCP Server & Automation Library.

Author: chriz-3656
License: MIT
"""

__version__ = "0.4.0"
__author__ = "chriz-3656"

from .core import Pencil2DProject, export_project, render_animation, launch_gui, get_appimage_path
from .server import run_server, TOOLS

__all__ = [
    "Pencil2DProject",
    "export_project",
    "render_animation",
    "launch_gui",
    "get_appimage_path",
    "run_server",
    "TOOLS",
    "__version__",
    "__author__",
]
