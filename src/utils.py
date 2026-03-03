import os
import sys

VERSION = "v0.4.1"
MAIN_REPO = "MihailRis/voxelcore"
MAX_LOAD = 1000


def resource_path(relative_path):
    try:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    except Exception:
        return relative_path