"""
Telos Build Script - Creates standalone executable for Windows

This script builds a standalone .exe using PyInstaller that includes:
- All Python dependencies
- Config files and prompts
- Documentation
- No Python installation required to run

Usage:
    python build_installer.py

Output:
    dist/Telos.exe - Standalone executable
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
ICON = None  # Add path to .ico file if you have one

# Paths
CLIENT_DIR = Path(__file__).parent
DIST_DIR = CLIENT_DIR / "dist"
BUILD_DIR = CLIENT_DIR / "build"
SPEC_FILE = CLIENT_DIR / f"{APP_NAME}.spec"

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
    'win32api',
    'win32con',
    'win32event',
    'win32service',
    'win32serviceutil',
    'google.genai',
]

def print_header(message):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {message}")
    print("="*60 + "\n")

def check_dependencies():
    """Check if required build tools are installed."""
    print_header("Checking Build Dependencies")
    
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

def build_executable():
    """Build the standalone executable using PyInstaller."""
    print_header(f"Building {APP_NAME} Executable")
    
    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",                    # Single file executable
        "--windowed",                   # No console window (comment out for debugging)
        "--clean",                      # Clean cache
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={CLIENT_DIR}",
    ]
    
    # Add icon if available
    if ICON and Path(ICON).exists():
        cmd.extend(["--icon", ICON])
    
    # Add data files
    for src, dest in DATA_FILES:
        src_path = CLIENT_DIR / src
        if src_path.exists():
            cmd.extend(["--add-data", f"{src};{dest}"])
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

1. **First Time Setup**
   - Double-click `{APP_NAME}.exe` to launch
   - If Windows shows a security warning:
     * Click "More info"
     * Click "Run anyway"
   - Follow the onboarding wizard

2. **Daily Use**
   - The app runs in the background
   - Access via system tray icon
   - View your productivity dashboard anytime

3. **Troubleshooting**
   - Logs are stored in: `%APPDATA%\\Telos\\logs\\`
   - Config is stored in: `%APPDATA%\\Telos\\config.yaml`
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
    dist_readme.write_text(readme_content.strip())
    print(f"✅ Created {dist_readme}")

def get_exe_size():
    """Get the size of the built executable."""
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        return size_mb
    return 0

def print_summary():
    """Print build summary."""
    print_header("Build Summary")
    
    installer_path = DIST_DIR / f"TelosSetup-v{VERSION}.exe"
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    zip_path = CLIENT_DIR / f"{APP_NAME}-v{VERSION}-Windows.zip"
    
    if installer_path.exists():
        size_mb = installer_path.stat().st_size / (1024 * 1024)
        print(f"✅ Windows Installer created successfully!")
        print(f"\n📦 Installer:")
        print(f"   File: {installer_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"\n🧪 Testing:")
        print(f"   1. Run the installer on your machine")
        print(f"   2. Follow the installation wizard")
        print(f"   3. Test the installed app")
        print(f"\n📤 Distribution:")
        print(f"   1. Upload TelosSetup-v{VERSION}.exe to Google Drive/Dropbox")
        print(f"   2. Share link with your friend")
        print(f"   3. They just run it and follow the wizard!")
        print(f"\n✨ User Experience:")
        print(f"   • Download TelosSetup.exe")
        print(f"   • Run it → Installation wizard appears")
        print(f"   • Installs to Program Files")
        print(f"   • Creates desktop/start menu shortcuts")
        print(f"   • Optionally starts with Windows")
    elif zip_path.exists():
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"✅ Distribution package created (no Inno Setup)")
        print(f"\n📦 Package:")
        print(f"   File: {zip_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"\n💡 To create a proper installer:")
        print(f"   1. Install Inno Setup: https://jrsoftware.org/isdl.php")
        print(f"   2. Run this script again")
    elif exe_path.exists():
        size_mb = get_exe_size()
        print(f"✅ Executable created")
        print(f"\n📦 Output:")
        print(f"   Location: {exe_path}")
        print(f"   Size: {size_mb:.2f} MB")
    else:
        print("❌ Build failed - no output found")

def create_installer():
    """Create Windows installer using Inno Setup."""
    print_header("Creating Windows Installer")
    
    # Check if Inno Setup is installed
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    inno_compiler = None
    for path in inno_paths:
        if Path(path).exists():
            inno_compiler = path
            break
    
    if not inno_compiler:
        print("⚠️  Inno Setup not found - skipping installer creation")
        print("\n💡 To create a proper installer:")
        print("   1. Download Inno Setup: https://jrsoftware.org/isdl.php")
        print("   2. Install it (default location)")
        print("   3. Run this script again")
        print("\n📦 For now, creating .zip package instead...")
        create_distribution_zip()
        return
    
    print(f"✅ Found Inno Setup: {inno_compiler}")
    
    # Check if ISS file exists
    iss_file = CLIENT_DIR / "installer_config.iss"
    if not iss_file.exists():
        print(f"❌ Installer config not found: {iss_file}")
        return
    
    # Run Inno Setup compiler
    print("\nCompiling installer...")
    try:
        subprocess.check_call([inno_compiler, str(iss_file)], cwd=CLIENT_DIR)
        print("✅ Installer created successfully!")
        
        # Find the installer
        installer_name = f"TelosSetup-v{VERSION}.exe"
        installer_path = DIST_DIR / installer_name
        
        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            print(f"\n📦 Installer Details:")
            print(f"   File: {installer_path}")
            print(f"   Size: {size_mb:.2f} MB")
            return installer_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installer creation failed: {e}")
        print("\n📦 Creating .zip package as fallback...")
        create_distribution_zip()

def create_distribution_zip():
    """Create a .zip file for easy distribution (fallback if no Inno Setup)."""
    print_header("Creating Distribution Package")
    
    import zipfile
    
    zip_path = CLIENT_DIR / f"{APP_NAME}-v{VERSION}-Windows.zip"
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    readme_path = DIST_DIR / "README.txt"
    
    if not exe_path.exists():
        print("❌ Executable not found, cannot create zip")
        return
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(exe_path, f"{APP_NAME}.exe")
        if readme_path.exists():
            zipf.write(readme_path, "README.txt")
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✅ Created distribution package:")
    print(f"   Location: {zip_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"\n📤 Ready to share with beta testers!")

def main():
    """Main build process."""
    print(f"\n🚀 Building {APP_NAME} v{VERSION}")
    
    try:
        # Step 1: Check dependencies
        check_dependencies()
        
        # Step 2: Clean previous builds
        clean_build()
        
        # Step 3: Build executable
        build_executable()
        
        # Step 4: Create distribution files
        create_readme()
        
        # Step 5: Create installer (or zip if Inno Setup not available)
        create_installer()
        
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

