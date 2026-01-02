#!/usr/bin/env python3
"""
Simple helper script to create icon.icns from a PNG image.

Usage:
    python create_icns.py input.png
    
This will create icon.icns in the same directory.

Requirements:
    - PIL (Pillow): pip install Pillow
    - macOS iconutil command (built-in on macOS)
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed")
    print("Install it with: pip install Pillow")
    sys.exit(1)


def create_icns(input_path):
    """Create .icns file from input image."""
    
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return False
    
    print(f"Creating icon.icns from {input_path}...")
    
    # Create iconset directory
    iconset_dir = Path("icon.iconset")
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir()
    
    # Load source image
    try:
        img = Image.open(input_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
    except Exception as e:
        print(f"Error loading image: {e}")
        return False
    
    # Generate all required sizes
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    
    print("Generating icon sizes...")
    for size, filename in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        output_path = iconset_dir / filename
        resized.save(output_path, 'PNG')
        print(f"  ✓ {filename} ({size}x{size})")
    
    # Use iconutil to create .icns
    print("\nCreating .icns file...")
    try:
        subprocess.run([
            'iconutil', '-c', 'icns', str(iconset_dir)
        ], check=True)
        print("✓ icon.icns created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running iconutil: {e}")
        print("\nMake sure you're running this on macOS")
        return False
    except FileNotFoundError:
        print("Error: iconutil command not found")
        print("This tool is only available on macOS")
        return False
    
    # Clean up
    shutil.rmtree(iconset_dir)
    
    # Move to current directory
    icon_path = Path("icon.icns")
    if icon_path.exists():
        print(f"\n✅ Success! Created: {icon_path.absolute()}")
        print(f"   Size: {icon_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print("\n❌ Failed to create icon.icns")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_icns.py input.png")
        print("\nExample:")
        print("  python create_icns.py telos-icon.png")
        print("\nThis will create icon.icns from your PNG image.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    success = create_icns(input_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

