import sys


def get_platform_asset_pattern():
    system = sys.platform
    if system == 'win32':
        return 'win64.zip'
    elif system == 'darwin':
        return '.dmg'
    else:
        return '.AppImage'


def get_executable_pattern():
    system = sys.platform
    if system == 'win32':
        return '.exe'
    elif system == 'darwin':
        return '.app'
    else:
        return '.AppImage'


def get_platform_name():
    if sys.platform == 'win32':
        return "Windows"
    if sys.platform == 'darwin':
        return "macOS"

    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAME="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        return value
    except Exception:
        pass

    return "Linux"