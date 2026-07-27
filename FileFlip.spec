# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

project_root = Path.cwd()
tesseract_root = Path(r"C:\Program Files\Tesseract-OCR")
if not tesseract_root.exists():
    raise FileNotFoundError(
        "Tesseract was not found at C:\\Program Files\\Tesseract-OCR. "
        "Install it or update tesseract_root in FileFlip.spec before packaging."
    )

datas = [
    (str(project_root / 'assets'), 'assets'),
    (str(tesseract_root), 'tesseract'),
]
binaries = []
hiddenimports = [
    'docx',
    'fitz',
    'PIL',
    'pytesseract',
    'pythoncom',
    'pywintypes',
    'win32com',
    'win32com.client',
    'win32timezone',
]
tmp_ret = collect_all('fitz')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # FileFlip uses PyQt6 exclusively. A globally installed PyQt5 can be
    # discovered through optional third-party dependencies and makes
    # PyInstaller abort when both Qt bindings are collected.
    excludes=['PyQt5', 'PySide2', 'PySide6'],
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
    name='FileFlip',
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
    icon=str(project_root / 'assets' / 'fileflip.ico'),
)
