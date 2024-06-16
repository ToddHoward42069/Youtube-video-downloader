# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL._imaging', 'pydub', 'PIL', 'pytube', 'requests', 'certifi', 'mutagen', 'pydantic', 'ffmpeg', 'ffmpeg_python', 'PIL._tkinter_finder'],
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
    name='Youtube-Video-Downloader',
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
)
