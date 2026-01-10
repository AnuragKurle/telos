"""Firebase Authentication via REST API.

This module handles Firebase anonymous authentication without requiring
the firebase-admin SDK on the client side. It uses the Firebase REST API
to sign in anonymously and manage token refresh.

Token storage: ~/.telos/auth.json
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class FirebaseAuthError(Exception):
    """Custom exception for Firebase authentication errors."""
    pass


class FirebaseAuth:
    """Manages Firebase anonymous authentication and token refresh."""
    
    # Firebase REST API endpoints
    SIGNUP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"  # For anonymous sign-up
    SIGNUP_WITH_EMAIL_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"  # Same endpoint, different params
    SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    REFRESH_URL = "https://securetoken.googleapis.com/v1/token"
    
    def __init__(self, api_key: str, storage_dir: str = "~/.telos"):
        """Initialize Firebase Auth client.
        
        Args:
            api_key: Firebase Web API Key
            storage_dir: Directory to store auth tokens (default: ~/.telos)
        """
        self.api_key = api_key
        self.storage_dir = Path(storage_dir).expanduser()
        self.auth_file = self.storage_dir / "auth.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
    def get_token(self, force_refresh: bool = False) -> str:
        """Get a valid Firebase ID token.
        
        This method handles the full authentication flow:
        1. Check in-memory cache
        2. Check disk storage
        3. Refresh if expired
        4. Sign in anonymously if no refresh token
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            
        Returns:
            Valid Firebase ID token
            
        Raises:
            FirebaseAuthError: If authentication fails
        """
        # Check in-memory cache (unless force refresh)
        if not force_refresh and self._is_token_valid():
            return self._cached_token
        
        # Load from disk
        auth_data = self._load_auth_data()
        
        if auth_data:
            # Try to refresh token
            try:
                new_token = self._refresh_token(auth_data['refresh_token'])
                return new_token
            except FirebaseAuthError as e:
                print(f"Token refresh failed: {e}. Signing in again...")
        
        # No valid token, sign in anonymously
        return self._sign_in_anonymous()
    
    def _is_token_valid(self) -> bool:
        """Check if cached token is still valid.
        
        Returns:
            True if token exists and hasn't expired
        """
        if not self._cached_token or not self._token_expiry:
            return False
        
        # Add 5 minute buffer before expiry
        return datetime.now() < (self._token_expiry - timedelta(minutes=5))
    
    def _sign_in_anonymous(self) -> str:
        """Sign in anonymously and get initial tokens.
        
        Returns:
            Firebase ID token
            
        Raises:
            FirebaseAuthError: If sign-in fails
        """
        try:
            response = requests.post(
                f"{self.SIGNUP_URL}?key={self.api_key}",
                json={"returnSecureToken": True},
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                raise FirebaseAuthError(f"Anonymous sign-in failed: {error_msg}")
            
            data = response.json()
            
            # Extract tokens
            id_token = data['idToken']
            refresh_token = data['refreshToken']
            expires_in = int(data['expiresIn'])  # Usually 3600 seconds (1 hour)
            
            # Cache in memory
            self._cached_token = id_token
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Save to disk
            self._save_auth_data({
                'refresh_token': refresh_token,
                'id_token': id_token,
                'expires_at': self._token_expiry.isoformat(),
                'signed_in_at': datetime.now().isoformat(),
            })
            
            print("[OK] Firebase anonymous sign-in successful")
            return id_token
            
        except requests.RequestException as e:
            raise FirebaseAuthError(f"Network error during sign-in: {e}")
    
    def sign_up_with_email(self, email: str, password: str) -> str:
        """Sign up with email and password.
        
        Args:
            email: User email address
            password: User password (minimum 6 characters)
            
        Returns:
            Firebase ID token
            
        Raises:
            FirebaseAuthError: If sign-up fails
        """
        try:
            response = requests.post(
                f"{self.SIGNUP_WITH_EMAIL_URL}?key={self.api_key}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                raise FirebaseAuthError(f"Sign-up failed: {error_msg}")
            
            data = response.json()
            
            # Extract tokens
            id_token = data['idToken']
            refresh_token = data['refreshToken']
            expires_in = int(data['expiresIn'])
            
            # Cache in memory
            self._cached_token = id_token
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Save to disk
            self._save_auth_data({
                'refresh_token': refresh_token,
                'id_token': id_token,
                'expires_at': self._token_expiry.isoformat(),
                'signed_in_at': datetime.now().isoformat(),
                'email': email,  # Store email for reference
            })
            
            print(f"[OK] Firebase sign-up successful: {email}")
            return id_token
            
        except requests.RequestException as e:
            raise FirebaseAuthError(f"Network error during sign-up: {e}")
    
    def sign_in_with_email(self, email: str, password: str) -> str:
        """Sign in with email and password.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Firebase ID token
            
        Raises:
            FirebaseAuthError: If sign-in fails
        """
        try:
            response = requests.post(
                f"{self.SIGNIN_URL}?key={self.api_key}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                raise FirebaseAuthError(f"Sign-in failed: {error_msg}")
            
            data = response.json()
            
            # Extract tokens
            id_token = data['idToken']
            refresh_token = data['refreshToken']
            expires_in = int(data['expiresIn'])
            
            # Cache in memory
            self._cached_token = id_token
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Save to disk
            self._save_auth_data({
                'refresh_token': refresh_token,
                'id_token': id_token,
                'expires_at': self._token_expiry.isoformat(),
                'signed_in_at': datetime.now().isoformat(),
                'email': email,
            })
            
            print(f"[OK] Firebase sign-in successful: {email}")
            return id_token
            
        except requests.RequestException as e:
            raise FirebaseAuthError(f"Network error during sign-in: {e}")
    
    def _refresh_token(self, refresh_token: str) -> str:
        """Refresh the ID token using refresh token.
        
        Args:
            refresh_token: Firebase refresh token
            
        Returns:
            New Firebase ID token
            
        Raises:
            FirebaseAuthError: If refresh fails
        """
        try:
            response = requests.post(
                f"{self.REFRESH_URL}?key={self.api_key}",
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                raise FirebaseAuthError(f"Token refresh failed: {error_msg}")
            
            data = response.json()
            
            # Extract new tokens
            id_token = data['id_token']
            new_refresh_token = data['refresh_token']
            expires_in = int(data['expires_in'])
            
            # Cache in memory
            self._cached_token = id_token
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Update disk storage
            self._save_auth_data({
                'refresh_token': new_refresh_token,
                'id_token': id_token,
                'expires_at': self._token_expiry.isoformat(),
                'refreshed_at': datetime.now().isoformat(),
            })
            
            return id_token
            
        except requests.RequestException as e:
            raise FirebaseAuthError(f"Network error during token refresh: {e}")
    
    def _load_auth_data(self) -> Optional[Dict[str, Any]]:
        """Load authentication data from disk.
        
        Returns:
            Auth data dict if exists, None otherwise
        """
        if not self.auth_file.exists():
            return None
        
        try:
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _save_auth_data(self, data: Dict[str, Any]) -> None:
        """Save authentication data to disk.
        
        Args:
            data: Auth data to save
        """
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save auth data: {e}")
    
    def sign_out(self) -> None:
        """Sign out by clearing all auth data."""
        self._cached_token = None
        self._token_expiry = None
        
        if self.auth_file.exists():
            self.auth_file.unlink()
        
        print("[OK] Signed out successfully")
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status.
        
        Returns:
            Dict with auth status information
        """
        auth_data = self._load_auth_data()
        
        if not auth_data:
            return {
                'authenticated': False,
                'message': 'Not signed in'
            }
        
        is_valid = self._is_token_valid()
        
        return {
            'authenticated': True,
            'token_valid': is_valid,
            'signed_in_at': auth_data.get('signed_in_at', 'unknown'),
            'expires_at': auth_data.get('expires_at', 'unknown'),
            'last_refreshed': auth_data.get('refreshed_at', 'N/A'),
        }


# Convenience function for quick usage
def get_firebase_token(api_key: str) -> str:
    """Get a valid Firebase token (convenience function).
    
    Args:
        api_key: Firebase Web API Key
        
    Returns:
        Valid Firebase ID token
    """
    auth = FirebaseAuth(api_key)
    return auth.get_token()

