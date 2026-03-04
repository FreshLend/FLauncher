# -*- mode: python ; coding: utf-8 -*-

import sys
import platform
import os
import re

spec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
src_path = os.path.join(spec_dir, 'src')

def get_version_from_file():
    utils_path = os.path.join(src_path, 'utils.py')
    try:
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Не удалось прочитать версию из {utils_path}: {e}")
    return "v0.0.0"

VERSION = get_version_from_file()

system = platform.system().lower()
is_macos = system == 'darwin'
print(f"Сборка FLauncher {VERSION} для {platform.system()}")

params = {
    'windows': {
        'separator': ';',
        'icon': os.path.join('src', 'ui', 'icon.ico'),
        'name': f'FLauncher-{VERSION}.exe',
        'console': False
    },
    'linux': {
        'separator': ':',
        'icon': os.path.join('src', 'ui', 'icon.png'),
        'name': f'FLauncher-{VERSION}',
        'console': False
    },
    'darwin': {
        'separator': ':',
        'icon': os.path.join('src', 'ui', 'icon.icns'),
        'name': f'FLauncher-{VERSION}',
        'console': False
    }
}

p = params.get(system, params['linux'])

if is_macos:
    app_name = f'FLauncher-{VERSION}.app'
else:
    app_name = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/ui', 'ui')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=p['name'],
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=p['console'],
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=p['icon']
)

if is_macos:
    app = BUNDLE(
        exe,
        name=app_name,
        icon=p['icon'],
        bundle_identifier='com.flauncher.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': VERSION.replace('v', ''),
            'CFBundleVersion': VERSION.replace('v', ''),
            'CFBundleName': f'FLauncher {VERSION}',
            'CFBundleDisplayName': f'FLauncher {VERSION}',
        }
    )