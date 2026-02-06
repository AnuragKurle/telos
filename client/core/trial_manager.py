"""Trial period management.

Handles trial tracking, expiration checks, and upgrade prompts.
Works in conjunction with the config system to track trial status.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import json


class TrialStatus:
    """Trial status constants."""
    ACTIVE = "active" # In trial
    EXPIRED = "expired" # Trial over, not paid
    PRO = "pro" # Paid user
    NOT_STARTED = "not_started"
    LOCAL_FREE = "local_free"  # BYOK mode — free forever


class TrialManager:
    """Manages trial period and upgrade prompts.
    
    Two-tier model:
    - BYOK (local mode): Free forever. User provides their own Gemini API key.
      No trial, no expiration, no upgrade prompts.
    - Cloud mode: 7-day free trial, then $3/month for Pro.
    """
    
    def __init__(self, config_manager, trial_duration_days: int = 7):
        """Initialize trial manager.
        
        Args:
            config_manager: ConfigManager instance
            trial_duration_days: Trial period duration (default: 7 days)
        """
        self.config = config_manager
        self.trial_duration_days = trial_duration_days
        
        # Upgrade prompt thresholds (days remaining)
        self.prompt_thresholds = {
            3: "halfway",
            1: "last_day",
            0: "expired"
        }
    
    def is_byok_mode(self) -> bool:
        """Check if user is in BYOK (Bring Your Own Key) / local mode.
        
        BYOK users have backend.enabled = False and provide their own API key.
        They get free, unlimited access — no trial, no expiration.
        
        Returns:
            True if running in local/BYOK mode
        """
        return not self.config.get('backend', 'enabled', default=False)
    
    def activate_trial(self, email: str, start_date_iso: str, end_date_iso: str) -> None:
        """Activate trial period from server response.
        
        Args:
            email: User email
            start_date_iso: ISO start date string
            end_date_iso: ISO end date string
        """
        trial_config = self.config.config.get('trial', {})
        trial_config['start_date'] = start_date_iso
        trial_config['end_date'] = end_date_iso
        trial_config['duration_days'] = self.trial_duration_days
        
        # Also update account info
        account_config = self.config.config.get('account', {})
        account_config['email'] = email
        account_config['status'] = 'trial'
        
        self.config.config['trial'] = trial_config
        self.config.config['account'] = account_config
        self.config.save(self.config.config)
        
    def start_trial(self) -> None:
        """Start the trial period locally (Legacy fallback)."""
        # Set trial start date in config
        trial_config = self.config.config.get('trial', {})
        trial_config['start_date'] = datetime.now().isoformat()
        
        # Calculate end date
        end_date = datetime.now() + timedelta(days=self.trial_duration_days)
        trial_config['end_date'] = end_date.isoformat()
        
        trial_config['duration_days'] = self.trial_duration_days
        trial_config['upgrade_prompts_shown'] = 0
        
        self.config.config['trial'] = trial_config
        self.config.save(self.config.config)
    
    def get_trial_start_date(self) -> Optional[datetime]:
        """Get trial start date.
        
        Returns:
            Start date or None if not started
        """
        trial_config = self.config.config.get('trial', {})
        start_date_str = trial_config.get('start_date')
        
        if not start_date_str:
            return None
        
        try:
            return datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            return None
    
    def get_trial_expiry_date(self) -> Optional[datetime]:
        """Get trial expiration date.
        
        Returns:
            Expiry date or None if not started
        """
        trial_config = self.config.config.get('trial', {})
        end_date_str = trial_config.get('end_date')
        
        if end_date_str:
            try:
                return datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
                
        # Fallback to calculation from start date
        start_date = self.get_trial_start_date()
        if not start_date:
            return None
        
        return start_date + timedelta(days=self.trial_duration_days)
    
    def get_days_remaining(self) -> int:
        """Get number of days remaining in trial.
        
        Returns:
            Days remaining (0 if expired, -1 if not started)
        """
        expiry_date = self.get_trial_expiry_date()
        if not expiry_date:
            return -1
            
        # Handle timezones loosely by using naive or aware consistently implies complexity
        # simpler to just check diff
        if expiry_date.tzinfo and datetime.now().tzinfo is None:
             now = datetime.now().astimezone()
        else:
             now = datetime.now()
             
        days_left = (expiry_date - now).days
        return max(0, days_left)
    
    def get_trial_status(self) -> str:
        """Get current trial status.
        
        Returns:
            One of: TrialStatus.ACTIVE, EXPIRED, PRO, NOT_STARTED, LOCAL_FREE
        """
        # BYOK users are always free — no trial system applies
        if self.is_byok_mode():
            return TrialStatus.LOCAL_FREE
        
        # Check explicit status first (synced from server)
        account_config = self.config.config.get('account', {})
        explicit_status = account_config.get('status')
        
        if explicit_status == 'pro':
            return TrialStatus.PRO
        
        if explicit_status == 'expired':
            return TrialStatus.EXPIRED
        
        # Check if trial started
        start_date = self.get_trial_start_date()
        if not start_date:
            return TrialStatus.NOT_STARTED
        
        # Check if expired by date calculation
        expiry_date = self.get_trial_expiry_date()
        
        # Handle timezone awareness check
        now = datetime.now()
        if expiry_date.tzinfo:
            now = now.astimezone()
            
        if expiry_date < now:
             return TrialStatus.EXPIRED
        
        return TrialStatus.ACTIVE
    
    def is_trial_active(self) -> bool:
        """Check if trial is currently active.
        
        BYOK users are always considered active (free forever).
        
        Returns:
            True if trial is active or user is in BYOK mode
        """
        status = self.get_trial_status()
        return status in (TrialStatus.ACTIVE, TrialStatus.LOCAL_FREE)
    
    def is_pro(self) -> bool:
        """Check if user has Pro access.
        
        Returns:
             True if Pro
        """
        return self.get_trial_status() == TrialStatus.PRO
        
    def is_trial_expired(self) -> bool:
        """Check if trial has expired.
        
        BYOK users never expire.
        
        Returns:
            True if trial is expired (never true for BYOK)
        """
        return self.get_trial_status() == TrialStatus.EXPIRED
    
    def should_show_upgrade_prompt(self) -> Optional[str]:
        """Check if an upgrade prompt should be shown.
        
        BYOK users never see upgrade prompts.
        
        Returns:
            Prompt type ("halfway", "last_day", "expired") or None
        """
        status = self.get_trial_status()
        
        if status in (TrialStatus.PRO, TrialStatus.LOCAL_FREE):
            return None
            
        if status == TrialStatus.EXPIRED:
             # Repetitively showing expired prompt handled by UI logic typically
             return "expired"
        
        if status == TrialStatus.NOT_STARTED:
            return None
        
        days_remaining = self.get_days_remaining()
        
        # Check thresholds
        for threshold, prompt_type in self.prompt_thresholds.items():
            if days_remaining <= threshold:
                # Check if we've already shown this prompt type today
                if not self._was_prompt_shown_today(prompt_type):
                    return prompt_type
        
        return None
    
    def record_upgrade_prompt_shown(self, prompt_type: str) -> None:
        """Record that an upgrade prompt was shown.
        
        Args:
            prompt_type: Type of prompt shown
        """
        trial_config = self.config.config.get('trial', {})
        
        if 'prompts_shown' not in trial_config:
            trial_config['prompts_shown'] = {}
        
        trial_config['prompts_shown'][prompt_type] = datetime.now().isoformat()
        
        # Increment counter
        trial_config['upgrade_prompts_shown'] = trial_config.get('upgrade_prompts_shown', 0) + 1
        
        self.config.config['trial'] = trial_config
        self.config.save(self.config.config)
    
    def _was_prompt_shown_today(self, prompt_type: str) -> bool:
        """Check if a specific prompt was shown today.
        
        Args:
            prompt_type: Prompt type to check
            
        Returns:
            True if prompt was shown today
        """
        trial_config = self.config.config.get('trial', {})
        prompts_shown = trial_config.get('prompts_shown', {})
        
        last_shown_str = prompts_shown.get(prompt_type)
        if not last_shown_str:
            return False
        
        try:
            last_shown = datetime.fromisoformat(last_shown_str)
            today = datetime.now().date()
            return last_shown.date() == today
        except ValueError:
            return False
    
    def get_trial_info(self) -> Dict[str, Any]:
        """Get comprehensive trial information.
        
        Returns:
            Dict with trial info
        """
        status = self.get_trial_status()
        start_date = self.get_trial_start_date()
        expiry_date = self.get_trial_expiry_date()
        days_remaining = self.get_days_remaining()
        
        return {
            'status': status,
            'is_active': status == TrialStatus.ACTIVE,
            'is_expired': status == TrialStatus.EXPIRED,
            'is_pro': status == TrialStatus.PRO,
            'start_date': start_date.isoformat() if start_date else None,
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'days_remaining': days_remaining,
            'duration_days': self.trial_duration_days,
            'prompt_ready': self.should_show_upgrade_prompt(),
        }
    
    def get_banner_color(self) -> str:
        """Get color for trial banner based on days remaining.
        
        Returns:
            Color string (green, yellow, red)
        """
        status = self.get_trial_status()
        
        if status == TrialStatus.LOCAL_FREE:
            return "green"
        
        if status == TrialStatus.PRO:
            return "blue"
        
        if status == TrialStatus.EXPIRED:
            return "red"
        
        days_remaining = self.get_days_remaining()
        
        if days_remaining >= 4:
            return "green"
        elif days_remaining >= 2:
            return "yellow"
        else:
            return "red"
    
    def get_banner_message(self) -> str:
        """Get message for trial banner.
        
        Returns:
            Banner message string
        """
        status = self.get_trial_status()
        
        if status == TrialStatus.LOCAL_FREE:
            return ""  # No banner needed for BYOK users
        
        if status == TrialStatus.PRO:
            return "Pro Account Active"
        
        if status == TrialStatus.EXPIRED:
            return "Trial Expired - Upgrade to Continue"
        
        if status == TrialStatus.NOT_STARTED:
            return ""
        
        days_remaining = self.get_days_remaining()
        
        if days_remaining == 0:
            return "Last Day of Trial!"
        elif days_remaining == 1:
            return "1 Day Remaining in Trial"
        else:
            return f"{days_remaining} Days Remaining in Trial"
    
    def mark_pro(self, email: str = None) -> None:
        """Mark account as Pro (local override).
        
        Args:
            email: Email address linked to account
        """
        account_config = self.config.config.get('account', {})
        if email:
            account_config['email'] = email
        account_config['status'] = 'pro'
        account_config['upgraded_at'] = datetime.now().isoformat()
        
        self.config.config['account'] = account_config
        self.config.save(self.config.config)

    # ── Contextual nudges ──────────────────────────────────────────────

    def get_contextual_nudge(self, context: str = "general", session_count: int = 0) -> Optional[str]:
        """Get a contextual micro-nudge message if appropriate.
        
        Only returns nudges for active trial users (day 5+). Pro users and
        early trial users (day 1-4) never see nudges.
        
        Args:
            context: Where the nudge would appear ("summary", "dashboard", "milestone")
            session_count: Total sessions tracked so far (for milestone nudges)
            
        Returns:
            Nudge message string or None
        """
        status = self.get_trial_status()
        
        # No nudges for Pro, BYOK, or expired users
        if status not in (TrialStatus.ACTIVE,):
            return None
        
        days_remaining = self.get_days_remaining()
        
        # Day 1-4: Zero nudges. Let the user fall in love with the product.
        if days_remaining > 3:
            return None
        
        # Check if this specific nudge was already shown this session
        nudge_key = f"nudge_{context}_{days_remaining}"
        if self._was_nudge_shown_this_session(nudge_key):
            return None
        
        nudge = None
        
        # Session milestone nudge (50 sessions)
        if context == "milestone" and session_count > 0 and session_count % 50 == 0:
            nudge = f"You've tracked {session_count} sessions! Pro users get unlimited history."
            self._record_nudge_shown(nudge_key)
            return nudge
        
        # Day 5 (2 days left): Subtle informational note
        if days_remaining == 2 and context == "summary":
            nudge = "Your trial has 2 days left. Your tracking data is safe."
            self._record_nudge_shown(nudge_key)
            return nudge
        
        # Day 6 (1 day left): Last day reassurance
        if days_remaining == 1 and context == "dashboard":
            nudge = "Last day of your trial. Your tracking data is preserved."
            self._record_nudge_shown(nudge_key)
            return nudge
        
        # After a good summary: subtle attribution (only day 5-6)
        if context == "summary" and days_remaining <= 2:
            nudge = "Track trends over months with Pro."
            self._record_nudge_shown(nudge_key)
            return nudge
        
        return nudge
    
    def get_post_expiry_nudge(self) -> Optional[str]:
        """Get a post-expiry nudge for returning users.
        
        Shows a non-blocking toast every 3rd app launch after expiry.
        
        Returns:
            Nudge message string or None
        """
        status = self.get_trial_status()
        if status != TrialStatus.EXPIRED:
            return None
        
        # Track app launches since expiry
        trial_config = self.config.config.get('trial', {})
        launches_since_expiry = trial_config.get('launches_since_expiry', 0) + 1
        trial_config['launches_since_expiry'] = launches_since_expiry
        self.config.config['trial'] = trial_config
        self.config.save(self.config.config)
        
        # Show nudge every 3rd launch (not the first -- that gets the full-screen)
        if launches_since_expiry > 1 and launches_since_expiry % 3 == 0:
            return "Miss tracking? Upgrade for $3/mo to pick up where you left off."
        
        return None
    
    def _was_nudge_shown_this_session(self, nudge_key: str) -> bool:
        """Check if a nudge was already shown in this app session (today).
        
        Args:
            nudge_key: Unique key for the nudge
            
        Returns:
            True if nudge was shown today
        """
        trial_config = self.config.config.get('trial', {})
        nudges_shown = trial_config.get('nudges_shown', {})
        
        last_shown_str = nudges_shown.get(nudge_key)
        if not last_shown_str:
            return False
        
        try:
            last_shown = datetime.fromisoformat(last_shown_str)
            return last_shown.date() == datetime.now().date()
        except ValueError:
            return False
    
    def _record_nudge_shown(self, nudge_key: str) -> None:
        """Record that a nudge was shown.
        
        Args:
            nudge_key: Unique key for the nudge
        """
        trial_config = self.config.config.get('trial', {})
        if 'nudges_shown' not in trial_config:
            trial_config['nudges_shown'] = {}
        trial_config['nudges_shown'][nudge_key] = datetime.now().isoformat()
        self.config.config['trial'] = trial_config
        self.config.save(self.config.config)

    def refresh_account_status(self, backend_url: str, firebase_api_key: str) -> bool:
        """Sync account status from backend.
        
        Fetches the latest user status from the server and updates local config.
        
        Args:
            backend_url: Backend API URL
            firebase_api_key: Firebase API key for authentication
            
        Returns:
            True if status was successfully refreshed, False otherwise
        """
        from core.backend_client import BackendClient, BackendError, AuthenticationError
        
        email = self.config.config.get('account', {}).get('email')
        if not email:
            return False
            
        try:
            client = BackendClient(backend_url, firebase_api_key)
            response = client.get_user_status(email)
            
            access_status = response.get('accessStatus', 'trial')
            
            # Update local config based on server status
            if access_status == 'pro':
                self.mark_pro(email)
                return True
            elif access_status == 'expired':
                # Update account status to expired
                account_config = self.config.config.get('account', {})
                account_config['status'] = 'expired'
                self.config.config['account'] = account_config
                self.config.save(self.config.config)
                return True
            elif access_status == 'trial':
                # Update trial dates if provided
                trial_start = response.get('trialStartDate')
                trial_end = response.get('trialEndDate')
                if trial_start and trial_end:
                    self.activate_trial(email, trial_start, trial_end)
                return True
                
            return True
            
        except (BackendError, AuthenticationError) as e:
            print(f"[TRIAL] Failed to refresh account status: {e}")
            return False
        except Exception as e:
            print(f"[TRIAL] Unexpected error refreshing status: {e}")
            return False
