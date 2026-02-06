"""Gemini Vision API integration for screenshot analysis.

PORTKEY INTEGRATION: All LLM calls are logged to Portkey for observability.
See https://app.portkey.ai for logs.
"""

import json
import time
import base64
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.prompt_loader import PromptLoader

# Portkey configuration for LLM logging
PORTKEY_API_KEY = os.getenv('PORTKEY_API_KEY', 'AapMbWHuS0fvPfOSF9z4iOBuEYTm')
PORTKEY_VIRTUAL_KEY = os.getenv('PORTKEY_VIRTUAL_KEY', 'google-virtual-881dd3')


def _log_to_portkey(prompt: str, response_text: str, model: str, call_type: str = "unknown", latency_ms: float = 0, user_id: str = None, user_mode: str = "unknown"):
    """Log LLM call to Portkey for observability.
    
    Uses Portkey's SDK to make a small "ping" call that logs the metadata.
    This is a fire-and-forget operation.
    """
    try:
        from portkey_ai import Portkey
        import threading
        
        def _send_log():
            try:
                # Create Portkey client with metadata
                portkey = Portkey(
                    api_key=PORTKEY_API_KEY,
                    virtual_key=PORTKEY_VIRTUAL_KEY,
                    user=user_id or "telos-client",  # Top-level user parameter for Portkey logs
                    metadata={
                        "call_type": call_type,
                        "source": "telos-client",
                        "model": model,
                        "latency_ms": str(latency_ms),
                        "user_mode": user_mode,
                    },
                    trace_id=f"client-{call_type}-{int(latency_ms)}",
                )
                
                # Use a minimal call to log our data through Portkey
                # This creates a log entry with our metadata
                portkey.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"[TELOS LOG] call_type={call_type}"},
                        {"role": "user", "content": prompt[:2000] if prompt else "N/A"},
                        {"role": "assistant", "content": response_text[:2000] if response_text else "N/A"}
                    ],
                    max_tokens=1,  # Minimal tokens to avoid cost
                    stream=False,
                )
            except Exception as e:
                print(f"[Portkey] Background log failed: {e}")
        
        # Run in background thread to not block
        thread = threading.Thread(target=_send_log, daemon=True)
        thread.start()
        
    except Exception as e:
        # Silent fail - don't interrupt the flow for logging failures
        print(f"[Portkey] Logging setup failed (non-critical): {e}")


class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class GeminiAnalyzer:
    """Analyzes screenshots using Gemini Vision API with the new google-genai SDK.
    
    All LLM calls are logged to Portkey for observability.
    """

    # Common categories (AI can suggest others)
    COMMON_CATEGORIES = ['work', 'learning', 'browsing', 'entertainment', 'idle',
                         'debugging', 'meeting', 'research', 'communication', 'creative', 'planning', 'break']

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", user_email: str = None, user_mode: str = "unknown"):
        """Initialize Gemini analyzer.

        Args:
            api_key: Google Gemini API key
            model: Model name to use
            user_email: User email for logging
            user_mode: User mode ('cloud' or 'byok') for Portkey analytics
        """
        from google import genai
        from google.genai import types
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self.user_email = user_email
        self.user_mode = user_mode
        self.types = types
        self.max_retries = 3
        self.retry_delay = 2
        self.last_request_time = 0
        self.min_request_interval = 4.0  # Minimum 4 seconds between requests (15 RPM = 4s)
        self.prompt_loader = PromptLoader()
        
        # Log initialization
        print(f"[GeminiAnalyzer] Initialized with Portkey logging (User: {user_email}, Mode: {user_mode})")

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting before making API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _build_previous_context(self, previous_captures: List[Dict]) -> str:
        """Build context string from previous captures.

        Args:
            previous_captures: List of previous capture dictionaries

        Returns:
            Context string for the prompt
        """
        if not previous_captures:
            return "No previous context available. This is the first capture."

        context_parts = []
        for i, capture in enumerate(previous_captures, 1):
            time_str = capture.get('timestamp', 'unknown')
            task = capture.get('task', 'unknown')
            app = capture.get('app_name', 'unknown')
            category = capture.get('category', 'unknown')

            # Include detailed_context if available
            detailed = capture.get('detailed_context')
            extra_info = ""
            if detailed:
                try:
                    details = json.loads(detailed) if isinstance(detailed, str) else detailed
                    file_name = details.get('file_name', '')
                    progress = details.get('progress_from_last', '')
                    cursor = details.get('cursor_position', '')

                    if file_name:
                        extra_info += f" [File: {file_name}"
                        if cursor:
                            extra_info += f" @ {cursor}"
                        extra_info += "]"
                    if progress:
                        extra_info += f" Progress: {progress}"
                except (json.JSONDecodeError, TypeError):
                    pass

            context_parts.append(
                f"{i} capture(s) ago: [{category}] {app} - {task}{extra_info}"
            )

        return "\n".join(context_parts)

    def _get_generation_config(self):
        """Get generation config with thinking enabled and JSON schema.

        Returns:
            GenerateContentConfig object
        """
        # Response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                # REQUIRED: Simple category for dashboard statistics (constrained enum)
                "simple_category": {
                    "type": "string",
                    "enum": ["work", "learning", "browsing", "entertainment", "idle"]
                },
                # Core fields (required) - CONCISE for display
                "category": {"type": "string"},  # Detailed category for display
                "category_emoji": {"type": "string"},  # AI chooses emoji
                "category_color": {"type": "string"},  # AI chooses color
                "app": {"type": "string"},       # max 50 chars
                "task": {"type": "string"},      # max 80 chars - CONCISE
                "confidence": {"type": "number"},
                
                # Rich context (optional) - for internal use
                "detailed_context": {
                    "type": "object",
                    "properties": {
                        # Specifics
                        "file_name": {"type": "string"},
                        "cursor_position": {"type": "string"},
                        "browser_url": {"type": "string"},
                        
                        # Rich description (for search/analysis)
                        "full_description": {"type": "string"},
                        "progress_from_last": {"type": "string"},
                        
                        # AI AUTONOMY FIELDS
                        "ai_observations": {"type": "string"},
                        "suggested_category": {"type": "string"},
                        "confidence_notes": {"type": "string"}
                    }
                }
            },
            "required": ["simple_category", "category", "category_emoji", "category_color", "app", "task", "confidence"]
        }
        
        # Create config with dynamic thinking enabled (-1 = model decides)
        return self.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            thinking_config=self.types.ThinkingConfig(
                thinking_budget=-1  # Dynamic thinking - model decides based on complexity
            )
        )

    def _normalize_emoji(self, emoji_str: str) -> str:
        """Normalize emoji string (handle hex codes if AI sends them)."""
        if not emoji_str:
            return "📝"
        
        # If it's already an emoji (non-ascii character), return it
        if any(ord(c) > 127 for c in emoji_str):
            return emoji_str[0]  # Take first char if multiple
            
        # Try to parse hex codes like u1f4f1, U+1F4F1, etc.
        try:
            clean_hex = emoji_str.lower().replace('u+', '').replace('u', '').strip()
            if len(clean_hex) >= 4:
                return chr(int(clean_hex, 16))
        except:
            pass
            
        return "📝"

    def _load_image_as_part(self, image_path: str):
        """Load image file and create a Part object for the API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Part object with image data
        """
        from PIL import Image
        import io
        
        # Read image and convert to bytes
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (handle RGBA, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Save to bytes buffer as JPEG
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            image_bytes = buffer.getvalue()
        
        # Create Part with inline data
        return self.types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        )

    def analyze_screenshot_with_context(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Analyze screenshot with context from previous captures.

        Args:
            image_path: Path to screenshot image
            previous_captures: List of previous captures for context
            context_metadata: System-level metadata (active window, activity metrics)


        Returns:
            Dictionary with category, app, task, confidence, and detailed_context
            Returns None if analysis fails
        """
        # Build context from previous captures
        context_str = self._build_previous_context(previous_captures or [])
        
        # Build system context string
        system_context_str = "No system context available."
        if context_metadata:
            metrics = []
            if context_metadata.get('keystrokes', 0) > 10:
                metrics.append("High Typing")
            elif context_metadata.get('keystrokes', 0) > 0:
                metrics.append("Low Typing")
                
            if context_metadata.get('mouse_clicks', 0) > 2:
                metrics.append("High Clicks")
            
            if context_metadata.get('mouse_distance', 0) > 500:
                metrics.append("High Mouse Movement")
                
            input_desc = ", ".join(metrics) if metrics else "No Input"
            
            system_context_str = (
                f"Active Window: {context_metadata.get('window_title', 'Unknown')}\n"
                f"App Name: {context_metadata.get('app_name', 'Unknown')}\n"
                f"Input Activity (Last 30s): {input_desc}\n"
                f"(Raw: {context_metadata.get('keystrokes')} keys, {context_metadata.get('mouse_clicks')} clicks)"
            )

        # Load prompt and inject context
        prompt = self.prompt_loader.load_prompt(
            'screenshot_analysis',
            variables={
                'previous_context': context_str,
                'system_context': system_context_str
            }
        )

        generation_config = self._get_generation_config()

        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting before request
                self._apply_rate_limit()

                # Load image as Part
                image_part = self._load_image_as_part(image_path)
                
                # Create content with text and image
                contents = [
                    self.types.Content(
                        role="user",
                        parts=[
                            self.types.Part.from_text(text=prompt),
                            image_part
                        ]
                    )
                ]

                # Call API with new SDK
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generation_config
                )
                latency_ms = (time.time() - start_time) * 1000

                # Check if response has text
                if not response.text:
                    print(f"Empty response from API (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                result_text = response.text.strip()

                # Log to Portkey for observability (all inputs/outputs)
                _log_to_portkey(
                    prompt=prompt,
                    response_text=result_text,
                    model=self.model_name,
                    call_type="screenshot_analysis",
                    latency_ms=latency_ms,
                    user_id=self.user_email,
                    user_mode=self.user_mode,
                )

                # Extract JSON from response
                result_text = self._extract_json(result_text)

                # Parse JSON
                result = json.loads(result_text)

                if not self._validate_result_with_context(result):
                    print(f"Invalid result format: {result}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                # Normalize emoji (Phase 5 fix)
                result['category_emoji'] = self._normalize_emoji(result.get('category_emoji', '📝'))

                # Enforce size limits
                result = self._enforce_size_limits(result)

                return result

            except json.JSONDecodeError as e:
                print(f"JSON decode error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if 'result_text' in locals() and result_text:
                    print(f"Raw response (first 200 chars): {result_text[:200]}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    print(f"\n⚠️  RATE LIMIT HIT (attempt {attempt + 1}/{self.max_retries})")
                    print(f"Error: {error_str[:200]}...")

                    retry_wait = 60
                    if "retry in" in error_str.lower():
                        try:
                            import re
                            match = re.search(r'retry in (\d+\.?\d*)', error_str.lower())
                            if match:
                                retry_wait = int(float(match.group(1))) + 5
                        except:
                            pass

                    if attempt < self.max_retries - 1:
                        print(f"Waiting {retry_wait} seconds before retry...")
                        time.sleep(retry_wait)
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded: {error_str[:100]}", retry_wait)

                print(f"Error analyzing screenshot (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                return None

        return None

    def _validate_result_with_context(self, result: Dict[str, Any]) -> bool:
        """Validate analysis result format with AI autonomy (flexible categories).

        Args:
            result: Analysis result dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['category', 'app', 'task', 'confidence']

        if not all(field in result for field in required_fields):
            return False

        # AI autonomy: Accept any category string (not just the 5 defaults)
        if not isinstance(result['category'], str) or not result['category']:
            return False

        if not isinstance(result['confidence'], (int, float)):
            return False

        if not 0.0 <= result['confidence'] <= 1.0:
            return False

        return True

    def _enforce_size_limits(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce size limits on result fields.

        Args:
            result: Analysis result dictionary

        Returns:
            Result with size limits enforced
        """
        # Core fields
        if result.get('task'):
            result['task'] = result['task'][:80]
        if result.get('app'):
            result['app'] = result['app'][:50]

        # Detailed context fields
        if result.get('detailed_context'):
            dc = result['detailed_context']
            if dc.get('file_name'):
                dc['file_name'] = dc['file_name'][:100]
            if dc.get('cursor_position'):
                dc['cursor_position'] = dc['cursor_position'][:20]
            if dc.get('browser_url'):
                dc['browser_url'] = dc['browser_url'][:150]
            if dc.get('full_description'):
                dc['full_description'] = dc['full_description'][:200]
            if dc.get('progress_from_last'):
                dc['progress_from_last'] = dc['progress_from_last'][:150]
            if dc.get('ai_observations'):
                dc['ai_observations'] = dc['ai_observations'][:200]
            if dc.get('confidence_notes'):
                dc['confidence_notes'] = dc['confidence_notes'][:100]

        return result

    # ---- Legacy methods for backward compatibility ----

    def analyze_screenshot(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Analyze screenshot and categorize activity (legacy method).

        Args:
            image_path: Path to screenshot image

        Returns:
            Dictionary with category, app, task, and confidence
            Returns None if analysis fails
        """
        # Use new method with empty context for backward compatibility
        return self.analyze_screenshot_with_context(image_path, previous_captures=None)

    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text that might have preamble.

        Args:
            text: Text that may contain JSON with preamble

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        text = text.replace('```json', '').replace('```', '').strip()

        # Find the first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]

        return text

    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate analysis result format (legacy - strict categories).

        Args:
            result: Analysis result dictionary

        Returns:
            True if valid, False otherwise
        """
        return self._validate_result_with_context(result)

    def analyze_with_fallback(
        self,
        image_path: str,
        previous_captures: Optional[List[Dict]] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze screenshot with fallback to default values.

        Args:
            image_path: Path to screenshot image
            previous_captures: Previous captures for context (optional)
            context_metadata: System-level metadata (active window, activity metrics)

        Returns:
            Analysis result or default fallback
        """
        result = self.analyze_screenshot_with_context(image_path, previous_captures, context_metadata)

        if result is None:
            return {
                'simple_category': 'idle',  # For dashboard statistics
                'category': 'idle',
                'category_emoji': '💤',
                'category_color': '#95a5a6',
                'app': 'Unknown',
                'task': 'Unable to analyze',
                'confidence': 0.0,
                'detailed_context': {}
            }

        return result
