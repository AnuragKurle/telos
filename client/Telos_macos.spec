# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for macOS build of Telos

This file is used by build_macos.py to create a standalone .app bundle.
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('prompts', 'prompts'),
        ('config.yaml.example', '.'),
        ('docs', 'docs'),
        ('README.md', '.'),
        ('macos/dev.telos.tracker.plist', 'macos'),
    ],
    hiddenimports=[
        'textual',
        'textual.app',
        'textual.widgets',
        'textual.containers',
        'textual.screen',
        'rich',
        'rich.console',
        'rich.table',
        'rich.progress',
        'mss',
        'mss.darwin',
        'PIL',
        'PIL.Image',
        'imagehash',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'yaml',
        'sqlite3',
        'json',
        'datetime',
        'pathlib',
        'requests',
        'urllib3',
        # Add any other imports that PyInstaller might miss
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Windows-specific
        'pywin32',
        'win32api',
        'win32con',
        'win32event',
        'win32service',
        'win32serviceutil',
        
        # Data science (not needed)
        'matplotlib',
        'scipy',
        'pandas',
        'numpy.random._examples',
        
        # Testing (not needed in production)
        'tests',
        'test',
        'unittest',
        'pytest',
        '_pytest',
        
        # GUI frameworks (not needed)
        'tkinter',
        'PyQt5',
        'PySide2',
        'wx',
        
        # Development tools (not needed)
        'IPython',
        'jupyter',
        'notebook',
        'docutils',
        'sphinx',
        
        # Google Cloud SDK (too large, we use REST API)
        'google.cloud',
        'grpc',
        'grpcio',
        
        # Other large libraries
        'cv2',
        'tensorflow',
        'torch',
        'sklearn',
    ],
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
    name='Telos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='Telos.app',
    icon='macos/icon.icns',
    bundle_identifier='dev.telos.tracker',
    version='0.1.0',
    info_plist={
        'CFBundleName': 'Telos',
        'CFBundleDisplayName': 'Telos',
        'CFBundleIdentifier': 'dev.telos.tracker',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'Telos',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,
        
        # Privacy permissions
        'NSCameraUsageDescription': 'Telos does not use the camera.',
        'NSMicrophoneUsageDescription': 'Telos does not use the microphone.',
        'NSScreenCaptureUsageDescription': 'Telos needs to capture screenshots to analyze your activity and provide productivity insights.',
        'NSAccessibilityUsageDescription': 'Telos needs to monitor keyboard and mouse activity to detect when you are active and avoid tracking during idle time.',
        'NSSystemAdministrationUsageDescription': 'Telos needs this permission to run as a background service.',
        
        # App properties
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'LSUIElement': False,  # Set to True to hide from Dock
        'NSSupportsAutomaticGraphicsSwitching': True,
        
        # Document types (none for now)
        'CFBundleDocumentTypes': [],
        
        # URL types (none for now)
        'CFBundleURLTypes': [],
    },
)

