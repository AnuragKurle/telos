#!/usr/bin/env python3
"""
Quick fix script for users with broken backend configuration.

This script adds the missing Firebase section to existing config files
that were created without it.

Run this if you're getting "API key not valid" errors after installing via pip.
"""

import yaml
from pathlib import Path


def fix_config():
    """Add missing Firebase configuration to existing config file."""
    
    # Check user data directory first (~/.telos/)
    user_config = Path.home() / ".telos" / "config.yaml"
    
    # Check current directory (development mode)
    local_config = Path("config.yaml")
    
    # Determine which config to fix
    if user_config.exists():
        config_path = user_config
        print(f"Found config at: {config_path}")
    elif local_config.exists():
        config_path = local_config
        print(f"Found config at: {config_path}")
    else:
        print("❌ No config file found!")
        print("\nSearched in:")
        print(f"  - {user_config}")
        print(f"  - {local_config}")
        print("\nPlease run 'telos setup' first.")
        return False
    
    # Load config
    print("\n📖 Reading config...")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check if firebase section exists
    if 'firebase' in config and config['firebase'].get('api_key'):
        print("✅ Firebase section already exists - no fix needed!")
        print(f"   Firebase API key: {config['firebase']['api_key'][:20]}...")
        return True
    
    # Add firebase section
    print("\n🔧 Adding Firebase configuration...")
    config['firebase'] = {
        'api_key': "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8",
        'auth_domain': "gen-lang-client-0772617718.firebaseapp.com",
        'project_id': "gen-lang-client-0772617718"
    }
    
    # Ensure backend is enabled
    if config.get('backend', {}).get('enabled'):
        print("🔧 Backend is enabled - ensuring correct URL...")
        config['backend']['url'] = "https://telos-backend-ae7k4avtpq-el.a.run.app"
    
    # Backup original config
    backup_path = config_path.parent / f"{config_path.name}.backup"
    print(f"\n💾 Creating backup at: {backup_path}")
    with open(backup_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # Save fixed config
    print(f"💾 Saving fixed config to: {config_path}")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("\n✅ Config fixed successfully!")
    print("\nChanges made:")
    print("  ✓ Added Firebase authentication configuration")
    print("  ✓ Backend URL verified")
    print(f"  ✓ Backup saved to: {backup_path}")
    
    print("\n🚀 Next steps:")
    print("  1. Restart Telos: telos")
    print("  2. Backend should now connect properly")
    print("  3. AI Chat should work without errors")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Telos Backend Configuration Fix")
    print("=" * 60)
    print()
    print("This script fixes missing Firebase configuration in your")
    print("config file, which prevents backend connection.")
    print()
    
    try:
        success = fix_config()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf this error persists:")
        print("  1. Try running: telos setup")
        print("  2. Or contact support with this error message")
        exit(1)

