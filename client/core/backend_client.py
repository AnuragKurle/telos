"""Backend API client for screenshot analysis.

This module provides a client for interacting with the Telos backend API.
It handles authentication, file uploads, rate limiting, and error handling.
"""

import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.firebase_auth import FirebaseAuth, FirebaseAuthError


class BackendError(Exception):
    """Base exception for backend errors."""
    pass


class RateLimitError(BackendError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(BackendError):
    """Raised when authentication fails."""
    pass


class BackendClient:
    """Client for Telos backend API."""
    
    # API version
    CLIENT_VERSION = "0.1.0"
    
    def __init__(
        self,
        backend_url: str,
        firebase_api_key: str,
        timeout: int = 30,
        storage_dir: str = "~/.telos"
    ):
        """Initialize backend client.
        
        Args:
            backend_url: Backend API URL (e.g., https://telos-backend-xxx.run.app)
            firebase_api_key: Firebase Web API Key for authentication
            timeout: Request timeout in seconds
            storage_dir: Directory for auth storage
        """
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.firebase_auth = FirebaseAuth(firebase_api_key, storage_dir)
        
        # Track last request for client-side rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests
    
    def check_health(self) -> Dict[str, Any]:
        """Check backend health status.
        
        Returns:
            Health status dict
            
        Raises:
            BackendError: If health check fails
        """
        try:
            response = requests.get(
                f"{self.backend_url}/health",
                timeout=5  # Quick timeout for health check
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise BackendError(f"Health check failed: {response.status_code}")
                
        except requests.RequestException as e:
            raise BackendError(f"Backend unreachable: {e}")
    
    def analyze_screenshot(
        self,
        image_path: str,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """Upload screenshot for analysis.
        
        Args:
            image_path: Path to screenshot image
            retry_auth: Retry with fresh token if auth fails
            
        Returns:
            Analysis result dict with keys:
                - category: Activity category
                - app: Application name
                - task: Task description
                - confidence: Confidence score
                - detailed_context: Additional context (optional)
            
        Raises:
            BackendError: If upload fails
            RateLimitError: If rate limit exceeded
            AuthenticationError: If authentication fails
        """
        # Apply client-side rate limiting
        self._apply_rate_limit()
        
        # Get Firebase token
        try:
            token = self.firebase_auth.get_token()
        except FirebaseAuthError as e:
            raise AuthenticationError(f"Failed to get Firebase token: {e}")
        
        # Prepare file
        image_path = Path(image_path)
        if not image_path.exists():
            raise BackendError(f"Image file not found: {image_path}")
        
        # Upload request
        try:
            with open(image_path, 'rb') as img_file:
                files = {'image': (image_path.name, img_file, 'image/png')}
                headers = {
                    'Authorization': f'Bearer {token}',
                    'X-Client-Version': self.CLIENT_VERSION,
                }
                
                response = requests.post(
                    f"{self.backend_url}/v1/analyze/screenshot",
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
            
            # Handle response codes
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 401:
                # Token expired, retry with fresh token
                if retry_auth:
                    print("Token expired, refreshing...")
                    token = self.firebase_auth.get_token(force_refresh=True)
                    return self.analyze_screenshot(image_path, retry_auth=False)
                else:
                    raise AuthenticationError("Authentication failed after token refresh")
            
            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                error_msg = response.json().get('error', 'Rate limit exceeded')
                raise RateLimitError(error_msg, retry_after)
            
            elif response.status_code == 400:
                error_msg = response.json().get('error', 'Bad request')
                raise BackendError(f"Bad request: {error_msg}")
            
            elif response.status_code == 426:
                # Client version too old
                error_msg = response.json().get('error', 'Client version outdated')
                raise BackendError(f"Client upgrade required: {error_msg}")
            
            else:
                raise BackendError(f"Unexpected status {response.status_code}: {response.text[:200]}")
        
        except requests.Timeout:
            raise BackendError(f"Request timed out after {self.timeout}s")
        
        except requests.RequestException as e:
            raise BackendError(f"Network error: {e}")
    
    def _apply_rate_limit(self) -> None:
        """Apply client-side rate limiting to avoid overwhelming backend."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def is_backend_available(self) -> bool:
        """Check if backend is available.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            self.check_health()
            return True
        except BackendError:
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication status.
        
        Returns:
            Dict with auth status
        """
        return self.firebase_auth.get_auth_status()
    
    def sign_out(self) -> None:
        """Sign out and clear credentials."""
        self.firebase_auth.sign_out()


# Convenience function for testing
def test_backend_connection(backend_url: str) -> bool:
    """Test backend connection (no auth required).
    
    Args:
        backend_url: Backend URL
        
    Returns:
        True if backend is reachable and healthy
    """
    try:
        response = requests.get(f"{backend_url.rstrip('/')}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Backend healthy: {data.get('service')} v{data.get('version')}")
            return True
        else:
            print(f"[FAIL] Backend returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"[FAIL] Backend unreachable: {e}")
        return False

