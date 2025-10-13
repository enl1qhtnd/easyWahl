# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

current_dir = Path(os.getcwd())

block_cipher = None

a = Analysis(
    ['admin_gui.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
        ('database.py', '.'),
        ('api.py', '.'),
        ('models.py', '.'),
        ('websocket_manager.py', '.'),
        ('requirements.txt', '.'),
        # Include static directory if it exists
        ('static', 'static') if (current_dir / 'static').exists() else None,
    ],
    hiddenimports=[
        'database',
        'api', 
        'models',
        'websocket_manager',
        
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'uvicorn',
        'uvicorn.main',
        'uvicorn.server',
        'uvicorn.config',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.validators',
        
        'websockets',
        'websockets.server',
        'websockets.client',
        'websockets.protocol',
        
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.cookies',
        'requests.models',
        'requests.sessions',
        
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        
        'sqlite3',
        'threading',
        'datetime',
        'pathlib',
        'tempfile',
        'os',
        'sys',
        'json',
        'asyncio',
        'typing',
        'webbrowser',
        
        'python_multipart',
        'multipart',
        
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'click',
        'h11',
        'httptools',
        'python_dotenv',
        'pyyaml',
        'watchfiles',
        'websockets',
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

a.datas = [item for item in a.datas if item is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='easyWahl-v1.1.0',
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