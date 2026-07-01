# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['test_back_forth_postal.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pywinauto',
        'pywinauto.application',
        'pywinauto.mouse',
        'pywinauto.backend',
        'pywinauto.backends',
        'pywinauto.backends.uia',
        'pywinauto.backends.win32',
        'pywinauto.controls',
        'pywinauto.controls.uiawrapper',
        'pywinauto.controls.win32_controls',
        'pywinauto.keyboard',
        'comtypes',
        'comtypes.client',
        'win32api',
        'win32con',
        'win32gui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    [],
    name='test_back_forth_postal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
