"""Fallback handler for backend vs local analysis.

This module manages the decision logic for when to use the backend API
vs local Gemini analysis. It handles health checks, user preferences,
and graceful degradation when the backend is unavailable.
"""

import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.backend_client import BackendClient, BackendError, RateLimitError, AuthenticationError
from core.analyzer import GeminiAnalyzer


class FallbackMode:
    """Constants for fallback modes."""
    AUTO = "auto"           # Try backend, fall back to local if unavailable
    ALWAYS_BACKEND = "backend"  # Always use backend, fail if unavailable
    ALWAYS_LOCAL = "local"      # Always use local Gemini


class FallbackHandler:
    """Manages analysis routing between backend and local Gemini."""
    
    def __init__(
        self,
        backend_client: Optional[BackendClient],
        local_analyzer: GeminiAnalyzer,
        fallback_mode: str = FallbackMode.AUTO,
        health_check_interval: int = 300  # 5 minutes
    ):
        """Initialize fallback handler.
        
        Args:
            backend_client: Backend client (None to disable backend)
            local_analyzer: Local Gemini analyzer
            fallback_mode: Fallback strategy (auto, backend, local)
            health_check_interval: Seconds between backend health checks
        """
        self.backend_client = backend_client
        self.local_analyzer = local_analyzer
        self.fallback_mode = fallback_mode
        self.health_check_interval = health_check_interval
        
        # Backend health tracking
        self._backend_available = None  # None = unknown, True/False = known
        self._last_health_check = 0
        self._consecutive_failures = 0
        self._max_failures_before_disable = 3
        self._retry_interval = 30  # Retry sooner (30s) if backend is just temporarily down
        
        # Statistics
        self.stats = {
            'backend_requests': 0,
            'backend_successes': 0,
            'backend_failures': 0,
            'local_requests': 0,
            'rate_limit_hits': 0,
            'fallback_count': 0,
        }
        
        # NOTE: We do NOT perform an initial health check here anymore.
        # It blocks the main thread if initialized in the main loop.
        # Instead, we let the first analyze_screenshot() call trigger it
        # (which is usually called in a worker thread).
        if (self.backend_client and 
            self.fallback_mode == FallbackMode.AUTO):
            print("[Fallback Handler] Initialized in AUTO mode (waiting for first request to check health)")

    def analyze_screenshot(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze screenshot with fallback logic.
        
        Args:
            image_path: Path to screenshot
            previous_captures: Previous captures for context
            context_metadata: System-level metadata (active window, activity metrics)
            
        Returns:
            Analysis result dict
        """
        # Determine which analyzer to use
        use_backend = self._should_use_backend()
        
        if use_backend and self.backend_client:
            try:
                # Try backend first
                result = self._analyze_with_backend(image_path, previous_captures, context_metadata)
                self._on_backend_success()
                return result
                
            except RateLimitError as e:
                print(f"\n[WARN] Rate limit exceeded: {e}")
                self.stats['rate_limit_hits'] += 1
                
                if self.fallback_mode == FallbackMode.ALWAYS_BACKEND:
                    raise  # Don't fall back if user wants backend-only
                
                print(f"Falling back to local analysis...")
                return self._analyze_with_local(image_path, previous_captures, context_metadata)
            
            except (BackendError, AuthenticationError) as e:
                print(f"\n[WARN] Backend error: {e}")
                self._on_backend_failure()
                
                if self.fallback_mode == FallbackMode.ALWAYS_BACKEND:
                    raise  # Don't fall back if user wants backend-only
                
                print(f"Falling back to local analysis...")
                self.stats['fallback_count'] += 1
                return self._analyze_with_local(image_path, previous_captures, context_metadata)
        
        # Use local analyzer
        return self._analyze_with_local(image_path, previous_captures, context_metadata)
    
    def _should_use_backend(self) -> bool:
        """Decide whether to try using the backend.
        
        Returns:
            True if should attempt backend, False for local
        """
        # User preference: always local
        if self.fallback_mode == FallbackMode.ALWAYS_LOCAL:
            return False
        
        # User preference: always backend
        if self.fallback_mode == FallbackMode.ALWAYS_BACKEND:
            return True
        
        # No backend client configured
        if not self.backend_client:
            return False
        
        # Auto mode: check backend health
        if self._backend_available is False:
            # Too many consecutive failures, check if it's time to retry
            if self._consecutive_failures >= self._max_failures_before_disable:
                time_since_check = time.time() - self._last_health_check
                if time_since_check < self.health_check_interval:
                    return False  # Don't retry yet (long wait)
            else:
                # Backend failed recently, but not enough to disable. 
                # Retry sooner (short wait)
                time_since_check = time.time() - self._last_health_check
                if time_since_check < self._retry_interval:
                    return False

        # Periodic health check (if we haven't checked recently)
        # Use health_check_interval if healthy, or retry_interval if failing but not disabled
        interval = self.health_check_interval if self._backend_available else self._retry_interval
        
        if time.time() - self._last_health_check > interval:
            self._check_backend_health()
        
        # Use backend if available or if we don't know yet
        return self._backend_available is not False
    
    def _check_backend_health(self) -> None:
        """Check backend health and update status."""
        try:
            health_result = self.backend_client.check_health()
            self._backend_available = True
            self._consecutive_failures = 0
            service = health_result.get('service', 'backend')
            version = health_result.get('version', 'unknown')
            print(f"[OK] Backend health check passed - using backend API at {self.backend_client.backend_url}")
            print(f"     Service: {service} v{version}")
        except BackendError as e:
            self._backend_available = False
            self._consecutive_failures += 1
            print(f"[FAIL] Backend health check failed: {e}")
            if self.fallback_mode == FallbackMode.AUTO:
                print(f"       Falling back to local Gemini analysis")
        except Exception as e:
            # Catch any unexpected exceptions (shouldn't happen, but be safe)
            self._backend_available = False
            self._consecutive_failures += 1
            print(f"[FAIL] Unexpected error during health check: {type(e).__name__}: {e}")
            if self.fallback_mode == FallbackMode.AUTO:
                print(f"       Falling back to local Gemini analysis")
        finally:
            self._last_health_check = time.time()
    
    def _analyze_with_backend(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze using backend API.
        
        Args:
            image_path: Path to screenshot
            previous_captures: Previous captures for context
            context_metadata: System-level metadata (active window, activity metrics)
            
        Returns:
            Analysis result
        """
        self.stats['backend_requests'] += 1
        result = self.backend_client.analyze_screenshot(image_path, previous_captures, context_metadata)
        
        # Add metadata
        result['_source'] = 'backend'
        result['_timestamp'] = time.time()
        
        return result
    
    def _analyze_with_local(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze using local Gemini.
        
        Args:
            image_path: Path to screenshot
            previous_captures: Previous captures for context
            context_metadata: System-level metadata (active window, activity metrics)
            
        Returns:
            Analysis result
        """
        self.stats['local_requests'] += 1
        result = self.local_analyzer.analyze_screenshot_with_context(
            image_path,
            previous_captures,
            context_metadata
        )
        
        if result is None:
            # Use fallback result
            result = self.local_analyzer.analyze_with_fallback(
                image_path,
                previous_captures,
                context_metadata
            )
        
        # Add metadata
        result['_source'] = 'local'
        result['_timestamp'] = time.time()
        
        return result
    
    def _on_backend_success(self) -> None:
        """Called when backend request succeeds."""
        self.stats['backend_successes'] += 1
        self._backend_available = True
        self._consecutive_failures = 0
    
    def _on_backend_failure(self) -> None:
        """Called when backend request fails."""
        self.stats['backend_failures'] += 1
        self._consecutive_failures += 1
        
        if self._consecutive_failures >= self._max_failures_before_disable:
            self._backend_available = False
            print(f"[WARN] Backend disabled after {self._consecutive_failures} consecutive failures")
            print(f"   Will retry in {self.health_check_interval}s")
    
    def force_backend_check(self) -> bool:
        """Force an immediate backend health check.
        
        Returns:
            True if backend is healthy
        """
        self._check_backend_health()
        return self._backend_available is True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current fallback handler status.
        
        Returns:
            Status dict with backend availability and statistics
        """
        return {
            'fallback_mode': self.fallback_mode,
            'backend_available': self._backend_available,
            'backend_enabled': self.backend_client is not None,
            'consecutive_failures': self._consecutive_failures,
            'stats': self.stats.copy(),
        }
    
    def get_stats_summary(self) -> str:
        """Get a human-readable stats summary.
        
        Returns:
            Formatted stats string
        """
        total = self.stats['backend_requests'] + self.stats['local_requests']
        backend_pct = (self.stats['backend_requests'] / total * 100) if total > 0 else 0
        local_pct = (self.stats['local_requests'] / total * 100) if total > 0 else 0
        
        lines = [
            "Analysis Statistics:",
            f"  Total requests: {total}",
            f"  Backend: {self.stats['backend_requests']} ({backend_pct:.1f}%)",
            f"    - Successes: {self.stats['backend_successes']}",
            f"    - Failures: {self.stats['backend_failures']}",
            f"    - Rate limits: {self.stats['rate_limit_hits']}",
            f"  Local: {self.stats['local_requests']} ({local_pct:.1f}%)",
            f"  Fallbacks: {self.stats['fallback_count']}",
        ]
        
        return "\n".join(lines)

