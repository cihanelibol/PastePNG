# PyInstaller spec. Builds a single, windowless exe.
#   pyinstaller pastepng.spec
#   -> dist/PastePNG.exe
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pastepng.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.png', 'assets'), ('assets/icon.ico', 'assets')],
    hiddenimports=['win32timezone'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PastePNG',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    icon='assets/icon.ico',
)
