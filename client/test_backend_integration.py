#!/usr/bin/env python3
"""Test script for Phase 2 backend integration.

This script tests the complete flow:
1. Firebase authentication
2. Backend health check
3. Screenshot upload and analysis
4. Fallback mode
"""

import sys
import time
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent))

from core.firebase_auth import FirebaseAuth, FirebaseAuthError
from core.backend_client import BackendClient, BackendError, RateLimitError
from core.fallback_handler import FallbackHandler, FallbackMode
from core.analyzer import GeminiAnalyzer
from utils.config_manager import ConfigManager


def test_firebase_auth(firebase_api_key: str):
    """Test Firebase authentication."""
    print("\n" + "="*60)
    print("TEST 1: Firebase Authentication")
    print("="*60)
    
    try:
        auth = FirebaseAuth(firebase_api_key)
        
        # Get token
        print("Getting Firebase token...")
        token = auth.get_token()
        print(f"[OK] Token obtained: {token[:20]}...")
        
        # Get status
        status = auth.get_auth_status()
        print(f"[OK] Auth status: {status}")
        
        return True
    except FirebaseAuthError as e:
        print(f"[FAIL] Firebase auth failed: {e}")
        return False


def test_backend_health(backend_url: str):
    """Test backend health endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Backend Health Check")
    print("="*60)
    
    try:
        from core.backend_client import test_backend_connection
        
        print(f"Checking backend: {backend_url}")
        is_healthy = test_backend_connection(backend_url)
        
        if is_healthy:
            print("[OK] Backend is healthy and reachable")
            return True
        else:
            print("[FAIL] Backend health check failed")
            return False
    except Exception as e:
        print(f"[FAIL] Backend health check error: {e}")
        return False


def test_backend_client(backend_url: str, firebase_api_key: str, test_image: str):
    """Test backend client screenshot upload."""
    print("\n" + "="*60)
    print("TEST 3: Backend Screenshot Analysis")
    print("="*60)
    
    if not Path(test_image).exists():
        print(f"[FAIL] Test image not found: {test_image}")
        print("  Please provide a screenshot to test with")
        return False
    
    try:
        client = BackendClient(
            backend_url=backend_url,
            firebase_api_key=firebase_api_key,
            timeout=30
        )
        
        print(f"Uploading screenshot: {test_image}")
        result = client.analyze_screenshot(test_image)
        
        print("[OK] Analysis successful!")
        print(f"  Category: {result.get('category')}")
        print(f"  App: {result.get('app')}")
        print(f"  Task: {result.get('task')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Source: {result.get('_source', 'backend')}")
        
        return True
        
    except RateLimitError as e:
        print(f"[WARN] Rate limit hit: {e}")
        print(f"  Retry after: {e.retry_after}s")
        return False
    except BackendError as e:
        print(f"[FAIL] Backend error: {e}")
        return False


def test_fallback_handler(
    backend_url: str,
    firebase_api_key: str,
    gemini_api_key: str,
    test_image: str
):
    """Test fallback handler."""
    print("\n" + "="*60)
    print("TEST 4: Fallback Handler")
    print("="*60)
    
    if not Path(test_image).exists():
        print(f"[FAIL] Test image not found: {test_image}")
        return False
    
    try:
        # Initialize components
        backend_client = BackendClient(
            backend_url=backend_url,
            firebase_api_key=firebase_api_key
        )
        
        local_analyzer = GeminiAnalyzer(gemini_api_key)
        
        fallback_handler = FallbackHandler(
            backend_client=backend_client,
            local_analyzer=local_analyzer,
            fallback_mode=FallbackMode.AUTO
        )
        
        print("Testing AUTO mode (try backend, fall back to local)...")
        result = fallback_handler.analyze_screenshot(test_image)
        
        print("[OK] Analysis successful!")
        print(f"  Category: {result.get('category')}")
        print(f"  App: {result.get('app')}")
        print(f"  Source: {result.get('_source')}")
        
        # Print stats
        print("\n" + fallback_handler.get_stats_summary())
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Fallback handler error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PHASE 2 BACKEND INTEGRATION TEST")
    print("="*60)
    
    # Load config
    try:
        config = ConfigManager('config.yaml')
        config.load()  # Must call load() to read the file
        
        backend_url = config.get('backend', 'url')
        firebase_api_key = config.get('firebase', 'api_key')
        gemini_api_key = config.get('gemini', 'api_key')
        backend_enabled = config.get('backend', 'enabled', default=False)
        
        if not backend_enabled:
            print("\n[WARN] Backend is disabled in config.yaml")
            print("   Set backend.enabled to true to test backend integration")
            return
        
        print(f"\nBackend URL: {backend_url}")
        print(f"Firebase Project: {config.get('firebase', 'project_id')}")
        print(f"Client Version: {config.get('version', default='0.1.0')}")
        
    except Exception as e:
        print(f"\n[FAIL] Failed to load config: {e}")
        return
    
    # Find a test image
    test_image = None
    screenshot_dirs = [
        Path('temp_screenshots'),
        Path.home() / '.telos' / 'screenshots',
    ]
    
    for dir_path in screenshot_dirs:
        if dir_path.exists():
            images = list(dir_path.glob('*.png'))
            if images:
                test_image = str(images[0])
                break
    
    if not test_image:
        print("\n[WARN] No test screenshot found")
        print("   Please capture a screenshot first or provide a test image")
        print("   You can still run tests 1 and 2 (auth and health check)")
    
    # Run tests
    results = []
    
    # Test 1: Firebase Auth
    results.append(("Firebase Auth", test_firebase_auth(firebase_api_key)))
    
    # Test 2: Backend Health
    results.append(("Backend Health", test_backend_health(backend_url)))
    
    # Test 3: Backend Client (if we have a test image)
    if test_image:
        results.append((
            "Backend Analysis",
            test_backend_client(backend_url, firebase_api_key, test_image)
        ))
    
    # Test 4: Fallback Handler (if we have a test image)
    if test_image:
        results.append((
            "Fallback Handler",
            test_fallback_handler(backend_url, firebase_api_key, gemini_api_key, test_image)
        ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:10} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Phase 2 integration is working!")
    else:
        print("\n[WARN] Some tests failed. Check the output above for details.")


if __name__ == '__main__':
    main()

