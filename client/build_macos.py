"""
Telos macOS Build Script - Creates standalone .app bundle

This script builds a standalone .app bundle using PyInstaller that includes:
- All Python dependencies
- Config files and prompts
- Documentation
- No Python installation required to run

Usage:
    python build_macos.py

Output:
    dist/Telos.app - Standalone macOS application bundle
    dist/Telos-v0.1.0-beta.dmg - Installable disk image
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Build configuration
APP_NAME = "Telos"
VERSION = "0.1.0-beta"
AUTHOR = "Telos Team"
BUNDLE_IDENTIFIER = "dev.telos.tracker"

# Paths
CLIENT_DIR = Path(__file__).parent
DIST_DIR = CLIENT_DIR / "dist"
BUILD_DIR = CLIENT_DIR / "build"
SPEC_FILE = CLIENT_DIR / f"{APP_NAME}_macos.spec"
MACOS_DIR = CLIENT_DIR / "macos"

# Files to include
DATA_FILES = [
    ('prompts', 'prompts'),          # Include all prompts
    ('config.yaml.example', '.'),    # Include example config
    ('docs', 'docs'),                # Include documentation
    ('README.md', '.'),              # Include README
]

# Hidden imports (packages that PyInstaller might miss)
HIDDEN_IMPORTS = [
    'textual',
    'rich',
    'mss',
    'PIL',
    'imagehash',
    'pynput',
    'yaml',
    # Note: NO pywin32 for macOS
]

# Packages to exclude (reduce size dramatically)
EXCLUDED_MODULES = [
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
]

def print_header(message):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {message}")
    print("="*60 + "\n")

def check_dependencies():
    """Check if required build tools are installed."""
    print_header("Checking Build Dependencies")
    
    # Check if running on macOS
    if sys.platform != 'darwin':
        print("❌ This script must be run on macOS")
        print(f"   Current platform: {sys.platform}")
        sys.exit(1)
    
    print("✅ Running on macOS")
    
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found")
        print("\nInstalling PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Check if all app dependencies are installed
    print("\nChecking app dependencies...")
    requirements_file = CLIENT_DIR / "requirements.txt"
    if requirements_file.exists():
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ All dependencies installed")

def clean_build():
    """Clean previous build artifacts."""
    print_header("Cleaning Previous Builds")
    
    for directory in [DIST_DIR, BUILD_DIR]:
        if directory.exists():
            print(f"Removing {directory}...")
            shutil.rmtree(directory)
    
    if SPEC_FILE.exists():
        print(f"Removing {SPEC_FILE}...")
        SPEC_FILE.unlink()
    
    print("✅ Cleanup complete")

def build_app_bundle():
    """Build the .app bundle using PyInstaller."""
    print_header(f"Building {APP_NAME}.app Bundle")
    
    # Check if icon exists
    icon_path = MACOS_DIR / "icon.icns"
    
    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",                    # Single file executable
        "--windowed",                   # No console window
        "--clean",                      # Clean cache
        "--strip",                      # Strip debug symbols
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={CLIENT_DIR}",
        "--osx-bundle-identifier", BUNDLE_IDENTIFIER,
    ]
    
    # Add icon if available
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"  Using icon: {icon_path}")
    else:
        print(f"  ℹ️  No icon found at {icon_path}")
        print(f"     App will use default icon")
    
    # Exclude unnecessary modules to reduce size
    for module in EXCLUDED_MODULES:
        cmd.extend(["--exclude-module", module])
    
    # Add data files (only essential ones)
    for src, dest in DATA_FILES:
        src_path = CLIENT_DIR / src
        if src_path.exists():
            cmd.extend(["--add-data", f"{src}:{dest}"])
            print(f"  Including: {src}")
    
    # Add hidden imports
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    
    # Main entry point
    cmd.append("main.py")
    
    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd, cwd=CLIENT_DIR)
        print("\n✅ Build successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)

def create_readme():
    """Create a README for the distribution."""
    print_header("Creating Distribution README")
    
    readme_content = f"""
# {APP_NAME} v{VERSION}

## Quick Start

1. **Installation**
   - Open the DMG file
   - Drag {APP_NAME}.app to Applications folder
   - Eject the DMG

2. **First Launch**
   - Right-click {APP_NAME}.app in Applications
   - Select "Open" (required for first launch on unsigned apps)
   - Click "Open" in the security dialog
   - Follow the onboarding wizard

3. **Permissions**
   - {APP_NAME} will request Screen Recording permission
   - {APP_NAME} will request Accessibility permission
   - These are required for the app to track your activity

4. **Daily Use**
   - The app runs in the background
   - Access via menu bar or system tray
   - View your productivity dashboard anytime

5. **Troubleshooting**
   - Logs: ~/Library/Logs/Telos/
   - Config: ~/Library/Application Support/Telos/config.yaml
   - Delete config to reset settings

## Features

- 🎯 Automatic activity tracking
- 📊 AI-powered productivity insights
- 📧 Daily email reports
- 🔒 Privacy-focused (local processing)
- ⚡ Lightweight background service

## Support

- Email: support@telos.dev
- Docs: https://docs.telos.dev
- Issues: https://github.com/AnuragKurle/telos/issues

## Privacy

Telos processes your data locally and only sends anonymized analytics to our backend.
No screenshots or personal data leave your device without explicit consent.

Read full privacy policy: https://telos.dev/privacy

---

Built with ❤️ by {AUTHOR}
Version: {VERSION}
"""
    
    dist_readme = DIST_DIR / "README.txt"
    dist_readme.write_text(readme_content.strip(), encoding='utf-8')
    print(f"✅ Created {dist_readme}")

def create_dmg():
    """Create a DMG disk image for easy distribution."""
    print_header("Creating DMG Installer")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    dmg_path = DIST_DIR / f"{APP_NAME}-v{VERSION}-macOS.dmg"
    
    if not app_path.exists():
        print(f"❌ App bundle not found: {app_path}")
        return False
    
    # Remove existing DMG if present
    if dmg_path.exists():
        dmg_path.unlink()
    
    print(f"Creating DMG from {app_path}...")
    
    try:
        # Create DMG using hdiutil
        cmd = [
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", str(app_path),
            "-ov",
            "-format", "UDZO",
            str(dmg_path)
        ]
        
        subprocess.check_call(cmd)
        
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ DMG created successfully!")
        print(f"   File: {dmg_path}")
        print(f"   Size: {size_mb:.2f} MB")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG creation failed: {e}")
        print("\nYou can still use the .app bundle directly from the dist folder")
        return False

def get_app_size():
    """Get the size of the built app bundle."""
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if app_path.exists():
        # Calculate total size of .app bundle
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(app_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        size_mb = total_size / (1024 * 1024)
        return size_mb
    return 0

def print_summary():
    """Print build summary."""
    print_header("Build Summary")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    dmg_path = DIST_DIR / f"{APP_NAME}-v{VERSION}-macOS.dmg"
    
    if dmg_path.exists():
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        print(f"✅ macOS Installer created successfully!")
        print(f"\n📦 DMG Installer:")
        print(f"   File: {dmg_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"\n🧪 Testing:")
        print(f"   1. Double-click the DMG file")
        print(f"   2. Drag Telos.app to Applications folder")
        print(f"   3. Right-click → Open (first time)")
        print(f"   4. Test the installed app")
        print(f"\n📤 Distribution:")
        print(f"   1. Upload {APP_NAME}-v{VERSION}-macOS.dmg to cloud storage")
        print(f"   2. Share link with your users")
        print(f"   3. They just open the DMG and drag to Applications!")
        print(f"\n✨ User Experience:")
        print(f"   • Download {APP_NAME}-v{VERSION}-macOS.dmg")
        print(f"   • Open DMG → Drag to Applications")
        print(f"   • Right-click → Open (first time only)")
        print(f"   • Grant Screen Recording permission")
        print(f"   • Start tracking!")
    elif app_path.exists():
        size_mb = get_app_size()
        print(f"✅ App bundle created")
        print(f"\n📦 Output:")
        print(f"   Location: {app_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"\n💡 To create DMG:")
        print(f"   The DMG creation requires hdiutil (should be available on macOS)")
    else:
        print("❌ Build failed - no output found")

def main():
    """Main build process."""
    print(f"\n🚀 Building {APP_NAME} v{VERSION} for macOS")
    
    try:
        # Step 1: Check dependencies
        check_dependencies()
        
        # Step 2: Clean previous builds
        clean_build()
        
        # Step 3: Build app bundle
        build_app_bundle()
        
        # Step 4: Create distribution files
        create_readme()
        
        # Step 5: Create DMG installer
        create_dmg()
        
        # Step 6: Print summary
        print_summary()
        
        print("\n" + "="*60)
        print("  🎉 Build Complete!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

