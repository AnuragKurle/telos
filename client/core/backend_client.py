"""Backend API client for screenshot analysis.

This module provides a client for interacting with the Telos backend API.
It handles authentication, file uploads, rate limiting, and error handling.
"""

import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
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
                timeout=self.timeout  # Use configured timeout (health checks might be slow on cold start)
            )
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    raise BackendError(f"Invalid JSON response: {e}")
            else:
                raise BackendError(f"Health check failed: {response.status_code}")
                
        except requests.RequestException as e:
            raise BackendError(f"Backend unreachable: {e}")
        except Exception as e:
            # Catch any other unexpected exceptions
            raise BackendError(f"Health check error: {type(e).__name__}: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test backend connection and return detailed status.
        
        Returns:
            Dict with connection status:
                - connected: bool
                - service: str (service name)
                - version: str (service version)
                - error: str (error message if failed)
        """
        try:
            health = self.check_health()
            return {
                'connected': True,
                'service': health.get('service', 'unknown'),
                'version': health.get('version', 'unknown'),
                'timestamp': health.get('timestamp', ''),
                'error': None
            }
        except BackendError as e:
            return {
                'connected': False,
                'service': None,
                'version': None,
                'timestamp': None,
                'error': str(e)
            }
    
    def analyze_screenshot(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """Upload screenshot for analysis.
        
        Args:
            image_path: Path to screenshot image
            previous_captures: List of previous captures for context
            context_metadata: System-level metadata (active window, activity metrics)
            retry_auth: Retry with fresh token if auth fails
            
        Returns:
            Analysis result dict
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
            import json
            with open(image_path, 'rb') as img_file:
                files = {'image': (image_path.name, img_file, 'image/png')}
                data = {}
                if previous_captures:
                    data['previous_context'] = json.dumps(previous_captures)
                if context_metadata:
                    data['context_metadata'] = json.dumps(context_metadata)
                    print(f"[DEBUG] Sending context_metadata to backend: {json.dumps(context_metadata)[:200]}")
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'X-Client-Version': self.CLIENT_VERSION,
                }

                
                response = requests.post(
                    f"{self.backend_url}/v1/analyze/screenshot",
                    files=files,
                    data=data,
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
                    return self.analyze_screenshot(image_path, previous_captures, context_metadata, retry_auth=False)
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
    
    def submit_feedback(
        self,
        feedback_type: str,
        feedback_text: str,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """Submit feedback on AI analysis.
        
        Args:
            feedback_type: Type of feedback ('summary', 'session', 'capture', 'general')
            feedback_text: User's feedback text
            context: Optional context dict (e.g., {'summary_id': 123})
            metadata: Optional metadata dict (e.g., {'screen': 'summary', 'app_version': '0.1.0'})
            retry_auth: Retry with fresh token if auth fails
            
        Returns:
            Response dict with success status and feedback_id
            
        Raises:
            AuthenticationError: If authentication fails
            BackendError: If request fails
        """
        # Apply client-side rate limiting
        self._apply_rate_limit()
        
        # Get Firebase token
        try:
            token = self.firebase_auth.get_token()
        except FirebaseAuthError as e:
            raise AuthenticationError(f"Failed to get Firebase token: {e}")
        
        # Prepare request payload
        payload = {
            'feedback_type': feedback_type,
            'feedback_text': feedback_text,
            'context': context or {},
            'metadata': metadata or {},
        }
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-Client-Version': self.CLIENT_VERSION,
            }
            
            response = requests.post(
                f"{self.backend_url}/v1/feedback",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle response codes
            if response.status_code in (200, 201):
                return response.json()
            
            elif response.status_code == 401:
                # Token expired, retry with fresh token
                if retry_auth:
                    print("Token expired, refreshing...")
                    token = self.firebase_auth.get_token(force_refresh=True)
                    return self.submit_feedback(feedback_type, feedback_text, context, metadata, retry_auth=False)
                else:
                    raise AuthenticationError("Authentication failed after token refresh")
            
            elif response.status_code == 400:
                error_msg = response.json().get('message', 'Bad request')
                raise BackendError(f"Bad request: {error_msg}")
            
            else:
                raise BackendError(f"Unexpected status {response.status_code}: {response.text[:200]}")
        
        except requests.Timeout:
            raise BackendError(f"Request timed out after {self.timeout}s")
        
        except requests.RequestException as e:
            raise BackendError(f"Network error: {e}")

    def verify_access(
        self,
        email: str,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """Verify access for email and start/resume trial.
        
        Args:
            email: User's email address
            retry_auth: Retry on token expiry
            
        Returns:
            Dict with 'access' (bool), 'accessStatus' (str), 'trialStartDate', etc.
            
        Raises:
            AuthenticationError: If auth fails
            BackendError: If request fails or access denied
        """
        self._apply_rate_limit()
        
        try:
            token = self.firebase_auth.get_token()
        except FirebaseAuthError as e:
            raise AuthenticationError(f"Failed to get Firebase token: {e}")
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-Client-Version': self.CLIENT_VERSION,
            }
            
            response = requests.post(
                f"{self.backend_url}/v1/auth/verify-access",
                json={'email': email},
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
                
            elif response.status_code == 401:
                if retry_auth:
                    token = self.firebase_auth.get_token(force_refresh=True)
                    return self.verify_access(email, retry_auth=False)
                else:
                    raise AuthenticationError("Authentication failed")
                    
            elif response.status_code == 403:
                # Access Denied (Not on whitelist or Expired)
                # Parse specific error message
                data = response.json()
                error_msg = data.get('message', 'Access Denied')
                # Return the error payload so we can show specific UI
                return {
                    'access': False,
                    'error': error_msg,
                    'accessStatus': data.get('accessStatus', 'denied')
                }
                
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                error_msg = response.json().get('error', 'Rate limit exceeded')
                raise RateLimitError(error_msg, retry_after)
                
            else:
                raise BackendError(f"Server error: {response.status_code}")
                
        except requests.RequestException as e:
            raise BackendError(f"Connection error: {e}")

    def record_payment_intent(
        self,
        email: str,
        retry_auth: bool = True
    ) -> bool:
        """Record user's intent to upgrade.
        
        Args:
            email: User email
            
        Returns:
            True if successful
        """
        self._apply_rate_limit()
        
        try:
            token = self.firebase_auth.get_token()
        except FirebaseAuthError:
            # Swallow auth error here to not block UI? Or re-raise?
            # Better to re-raise, UI should handle it.
            return False 
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.backend_url}/v1/auth/record-payment-intent",
                json={'email': email},
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401 and retry_auth:
                self.firebase_auth.get_token(force_refresh=True)
                return self.record_payment_intent(email, retry_auth=False)
                
            return False
            
        except Exception as e:
            print(f"Error recording payment intent: {e}")
            return False


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

