# copilar.spec para APIWEBFASTAPI
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[('data/config.ini', 'data'), ('data/api.log', 'data')],
    hiddenimports = [
        'pyodbc',
        'fastapi', 'uvicorn', 'python_jose', 'databases', 'asyncmy', 'asyncpg', 'pytds', 'passlib.hash', 'PyJWT', 'python_dotenv',
        'apscheduler.schedulers.background', 'starlette', 'h11', 'h2', 'priority', 'wsproto'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name= 'apiwebfastapi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Cambia a False si no quieres una consola
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name= 'webfastapi'
)
