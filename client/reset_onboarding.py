#!/usr/bin/env python3
"""Reset onboarding state to experience the onboarding flow again.

This script removes the onboarding completion flag and state files,
allowing you to go through the onboarding flow as if it's a first run.
"""

from pathlib import Path
import sys


def reset_onboarding():
    """Reset onboarding state."""
    storage_dir = Path.home() / ".telos"
    
    # Files to remove
    files_to_remove = [
        storage_dir / "onboarding_complete",
        storage_dir / "onboarding_state.json",
        storage_dir / ".getting_started_shown",
    ]
    
    removed = []
    not_found = []
    
    for file_path in files_to_remove:
        if file_path.exists():
            file_path.unlink()
            removed.append(str(file_path))
            print(f"✓ Removed: {file_path}")
        else:
            not_found.append(str(file_path))
            print(f"ℹ Not found (already clean): {file_path}")
    
    print("\n" + "="*60)
    if removed:
        print(f"✓ Successfully reset onboarding! Removed {len(removed)} file(s).")
    else:
        print("✓ Onboarding was already reset (no files to remove).")
    
    print("\nYou can now run the client to experience the onboarding flow:")
    print("  cd client")
    print("  python main.py")
    print("\nNote: This will start fresh, so you'll need to:")
    print("  - Go through welcome screens")
    print("  - Set up your account again")
    print("  - Configure your preferences")
    print("="*60)


if __name__ == "__main__":
    try:
        reset_onboarding()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
