"""Quick diagnostic script to test backend connection."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config_manager import load_config
from core.backend_client import BackendClient, BackendError
from core.analyzer import GeminiAnalyzer
from core.fallback_handler import FallbackHandler

def main():
    print("=" * 60)
    print("Telos Backend Connection Diagnostic")
    print("=" * 60)
    
    # Load config
    print("\n1. Loading configuration...")
    try:
        config = load_config("config.yaml")
        print("   [OK] Config loaded successfully")
    except Exception as e:
        print(f"   [FAIL] Failed to load config: {e}")
        return
    
    # Check backend settings
    print("\n2. Backend configuration:")
    backend_enabled = config.get('backend', 'enabled', default=False)
    backend_url = config.get('backend', 'url', default="")
    fallback_mode = config.get('backend', 'fallback_mode', default='auto')
    timeout = config.get('backend', 'timeout', default=30)
    
    print(f"   Enabled: {backend_enabled}")
    print(f"   URL: {backend_url}")
    print(f"   Fallback Mode: {fallback_mode}")
    print(f"   Timeout: {timeout}s")
    
    if not backend_enabled:
        print("\n   [WARN] Backend is DISABLED in config!")
        return
    
    if not backend_url:
        print("\n   [WARN] Backend URL is EMPTY!")
        return
    
    # Test health check
    print("\n3. Testing backend health check...")
    print(f"   Connecting to: {backend_url}/health")
    
    firebase_api_key = config.get('firebase', 'api_key')
    
    try:
        backend_client = BackendClient(
            backend_url=backend_url,
            firebase_api_key=firebase_api_key,
            timeout=timeout
        )
        
        print(f"   Timeout set to: {timeout} seconds")
        print("   Checking health (this may take a few seconds)...")
        
        start_time = time.time()
        health = backend_client.check_health()
        elapsed = time.time() - start_time
        
        print(f"   [OK] Backend health check PASSED! ({elapsed:.2f}s)")
        print(f"   Service: {health.get('service')}")
        print(f"   Version: {health.get('version')}")
        print(f"   Timestamp: {health.get('timestamp')}")
        
    except BackendError as e:
        elapsed = time.time() - start_time
        print(f"   [FAIL] Backend health check FAILED! ({elapsed:.2f}s)")
        print(f"   Error: {e}")
        print(f"\n   This is why your app shows 'Local' instead of 'Cloud'")
        return
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   [FAIL] Unexpected error! ({elapsed:.2f}s)")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {e}")
        return
    
    # Test fallback handler
    print("\n4. Testing fallback handler initialization...")
    try:
        gemini_api_key = config.get('gemini', 'api_key')
        local_analyzer = GeminiAnalyzer(gemini_api_key)
        
        fallback_handler = FallbackHandler(
            backend_client=backend_client,
            local_analyzer=local_analyzer,
            fallback_mode=fallback_mode
        )
        
        print("   [OK] Fallback handler initialized")
        print(f"   Mode: {fallback_mode}")
        
    except Exception as e:
        print(f"   [FAIL] Failed to initialize: {e}")
        return
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All checks passed!")
    print("Your backend should work correctly.")
    print("=" * 60)
    print("\nIf your app still shows 'Local', try:")
    print("1. Make sure you're using the latest config.yaml")
    print("2. Restart the Telos.exe completely")
    print("3. Check Windows Firewall isn't blocking the connection")

if __name__ == '__main__':
    main()

