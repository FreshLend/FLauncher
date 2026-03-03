# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],  # Указываем путь к main.py внутри src
    pathex=['src'],    # Добавляем src в путь поиска
    binaries=[],
    datas=[
        ('src/ui', 'ui'),  # Копируем ui из src в корень сборки
    ],
    hiddenimports=[
        'pypresence',
        'markdown',
        'requests',
        'PyQt5',
    ],
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
    name='FLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/ui/icon.ico'  # Указываем путь к иконке внутри src
)