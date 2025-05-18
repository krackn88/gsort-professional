# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for gSort Professional.
"""

import os
import sys
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Tree

# Application information
app_name = "gSort Professional"
app_version = "2.0.0"
icon_file = os.path.join("resources", "icons", "app_icon.ico")
company_name = "gSort"

# Platform-specific settings
if sys.platform.startswith('win'):
    # Windows
    exe_name = "gSort-Professional"
    console = False  # Set to True to show console window
elif sys.platform.startswith('darwin'):
    # macOS
    exe_name = "gSort Professional"
    console = False
else:
    # Linux
    exe_name = "gsort-professional"
    console = False

# Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),  # Include resources directory
        ('LICENSE', '.'),            # Include license file
        ('README.md', '.'),          # Include README
    ],
    hiddenimports=[
        'PyQt5',
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'qt_material',
        'openpyxl',
        'weasyprint',
        'pdfkit',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ (ZlibArchive) containing Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if os.path.exists(icon_file) else None,
    version_info={
        'FileVersion': app_version,
        'ProductVersion': app_version,
        'FileDescription': app_name,
        'ProductName': app_name,
        'CompanyName': company_name,
        'LegalCopyright': f'Copyright © 2025 {company_name}',
        'OriginalFilename': f'{exe_name}.exe',
    } if sys.platform.startswith('win') else None,
)

# COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=exe_name,
)

# macOS specific
if sys.platform.startswith('darwin'):
    app = BUNDLE(
        coll,
        name=f'{exe_name}.app',
        icon=icon_file if os.path.exists(icon_file) else None,
        bundle_identifier=f'com.{company_name.lower()}.{exe_name.lower().replace(" ", "-")}',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'NSPrincipalClass': 'NSApplication',
            'CFBundleShortVersionString': app_version,
            'CFBundleVersion': app_version,
            'CFBundleName': app_name,
            'CFBundleDisplayName': app_name,
            'CFBundleGetInfoString': f"{app_name} {app_version}",
            'CFBundleIdentifier': f'com.{company_name.lower()}.{exe_name.lower().replace(" ", "-")}',
            'NSHumanReadableCopyright': f'Copyright © 2025 {company_name}',
        },
    )