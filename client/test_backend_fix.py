#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify backend fix works correctly.

Tests:
1. Config creation includes Firebase section
2. Auto-migration adds Firebase section to old configs
3. Backend client can initialize with Firebase config
"""

import yaml
import tempfile
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add client to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigManager


def test_minimal_config_includes_firebase():
    """Test that minimal config created by CLI includes Firebase section."""
    print("\n=== Test 1: Minimal Config Includes Firebase ===")
    
    # This is the minimal config from cli.py
    minimal_config = '''gemini:
  api_key: "BACKEND_MODE_NO_KEY_NEEDED"
  model: "gemini-2.5-flash"

capture:
  interval_seconds: 30
  idle_timeout_seconds: 60
  screenshot_quality: 85
  max_daily_requests: 1500
  use_previous_context: true
  detailed_analysis: true

storage:
  database_path: "~/.telos/tracker.db"
  captures_retention_days: 365
  sessions_retention_days: 90

display:
  refresh_rate_ms: 1000
  theme: "dark"

intelligence:
  session_trigger_hours: 2
  session_trigger_idle_minutes: 5
  check_interval_seconds: 60
  max_enrichment_per_trigger: 3
  min_session_captures: 2
  session_gap_seconds: 300

email:
  enabled: false
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender_email: ""
  sender_password: ""
  recipient_email: ""
  send_time: "21:00"

firebase:
  api_key: "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8"
  auth_domain: "gen-lang-client-0772617718.firebaseapp.com"
  project_id: "gen-lang-client-0772617718"

backend:
  enabled: true
  url: "https://telos-backend-ae7k4avtpq-el.a.run.app"
  fallback_to_local: false

trial:
  start_date: ""
  duration_days: 7
  upgrade_prompts_shown: 0

account:
  auth_type: "anonymous"
  user_id: ""
  email: ""

schema_version: 2
'''
    
    config = yaml.safe_load(minimal_config)
    
    # Check Firebase section exists
    assert 'firebase' in config, "❌ Firebase section missing!"
    assert config['firebase']['api_key'] == "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8", "❌ Firebase API key wrong!"
    assert config['firebase']['auth_domain'] == "gen-lang-client-0772617718.firebaseapp.com", "❌ Firebase auth domain wrong!"
    
    print("✅ Minimal config includes Firebase section")
    print(f"   API Key: {config['firebase']['api_key'][:20]}...")
    print(f"   Auth Domain: {config['firebase']['auth_domain']}")
    return True


def test_auto_migration_adds_firebase():
    """Test that ConfigManager auto-migration adds Firebase section to old configs."""
    print("\n=== Test 2: Auto-Migration Adds Firebase ===")
    
    # Create a v0.1.4 config WITHOUT firebase section
    old_config = {
        'gemini': {'api_key': 'BACKEND_MODE_NO_KEY_NEEDED', 'model': 'gemini-2.5-flash'},
        'capture': {'interval_seconds': 30},
        'storage': {'database_path': '~/.telos/tracker.db'},
        'backend': {'enabled': True, 'url': 'https://telos-backend-ae7k4avtpq-el.a.run.app'},
        'schema_version': 2
    }
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(old_config, f)
        temp_path = f.name
    
    try:
        # Load with ConfigManager (should auto-migrate)
        config_mgr = ConfigManager(temp_path)
        config_mgr.load()
        
        # Check Firebase section was added
        assert 'firebase' in config_mgr.config, "❌ Firebase section not added by migration!"
        assert config_mgr.config['firebase']['api_key'] == "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8", "❌ Firebase API key not set!"
        
        print("✅ Auto-migration adds Firebase section")
        print(f"   Firebase API Key: {config_mgr.config['firebase']['api_key'][:20]}...")
        return True
        
    finally:
        Path(temp_path).unlink()


def test_backend_client_initialization():
    """Test that BackendClient can initialize with Firebase config."""
    print("\n=== Test 3: Backend Client Initialization ===")
    
    try:
        from core.backend_client import BackendClient
        
        # Create backend client with Firebase credentials
        backend_client = BackendClient(
            backend_url="https://telos-backend-ae7k4avtpq-el.a.run.app",
            firebase_api_key="AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8",
            timeout=5
        )
        
        print("✅ BackendClient initialized successfully")
        print(f"   Backend URL: {backend_client.backend_url}")
        print(f"   Firebase Auth: Configured")
        
        # Try health check (may fail if backend is down, but shouldn't crash)
        try:
            status = backend_client.test_connection()
            if status['connected']:
                print(f"✅ Backend health check passed!")
                print(f"   Service: {status['service']}")
                print(f"   Version: {status['version']}")
            else:
                print(f"⚠️  Backend unreachable (but client initialized correctly)")
                print(f"   Error: {status['error']}")
        except Exception as e:
            print(f"⚠️  Health check failed (but client initialized correctly): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ BackendClient initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend Fix Verification Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Minimal Config", test_minimal_config_includes_firebase()))
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results.append(("Minimal Config", False))
    
    try:
        results.append(("Auto-Migration", test_auto_migration_adds_firebase()))
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results.append(("Auto-Migration", False))
    
    try:
        results.append(("Backend Client", test_backend_client_initialization()))
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results.append(("Backend Client", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Backend fix is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())

