# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('zorvan.Nodes')


a = Analysis(
    ['run_new_ui.py'],
    pathex=[],
    binaries=[],
    datas=[('gui_framework\\legacy\\styles_template.qss', 'gui_framework\\legacy'), ('gui_framework\\legacy\\styles.qss', 'gui_framework\\legacy'), ('custom_nodes.json', '.'), ('assets\\\\zorvan.ico', 'assets')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZorvanNewUI',
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
    icon=['C:\\My Stuff\\Uni & Research\\Zorvan Public Repo\\Zorvan\\assets\\zorvan.ico'],
)
