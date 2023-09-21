# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = ['../LipidIMEA']
hiddenimports += collect_submodules('../LipidIMEA')


block_cipher = None


a = Analysis(
    ['src/experiment/experiment.py'],
    pathex=['../LipidIMEA'],
    binaries=[],
    datas=[
        ('../LipidIMEA/_include/*', 'LipidIMEA/_include/'),
        ('../LipidIMEA/_include/rt_ranges/*', 'LipidIMEA/_include/rt_ranges/'),
        ('../LipidIMEA/_include/rules/*', 'LipidIMEA/_include/rules/'),
        ('../LipidIMEA/_include/scdb_params/*', 'LipidIMEA/_include/scdb_params/'),
    ] + collect_data_files('hdf5plugin'),
    hiddenimports=hiddenimports,
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
    name='experiment',
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
)
