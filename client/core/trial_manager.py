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
    ACTIVE = "active"
    EXPIRED = "expired"
    UPGRADED = "upgraded"
    NOT_STARTED = "not_started"


class TrialManager:
    """Manages trial period and upgrade prompts."""
    
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
        
    def start_trial(self) -> None:
        """Start the trial period."""
        # Set trial start date in config
        trial_config = self.config.config.get('trial', {})
        trial_config['start_date'] = datetime.now().isoformat()
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
            return datetime.fromisoformat(start_date_str)
        except ValueError:
            return None
    
    def get_trial_expiry_date(self) -> Optional[datetime]:
        """Get trial expiration date.
        
        Returns:
            Expiry date or None if not started
        """
        start_date = self.get_trial_start_date()
        if not start_date:
            return None
        
        return start_date + timedelta(days=self.trial_duration_days)
    
    def get_days_remaining(self) -> int:
        """Get number of days remaining in trial.
        
        Returns:
            Days remaining (0 if expired, -1 if not started)
        """
        start_date = self.get_trial_start_date()
        if not start_date:
            return -1
        
        expiry_date = self.get_trial_expiry_date()
        days_left = (expiry_date - datetime.now()).days
        
        return max(0, days_left)
    
    def get_trial_status(self) -> str:
        """Get current trial status.
        
        Returns:
            One of: TrialStatus.ACTIVE, EXPIRED, UPGRADED, NOT_STARTED
        """
        # Check if upgraded
        account_config = self.config.config.get('account', {})
        if account_config.get('auth_type') == 'email':
            return TrialStatus.UPGRADED
        
        # Check if trial started
        start_date = self.get_trial_start_date()
        if not start_date:
            return TrialStatus.NOT_STARTED
        
        # Check if expired
        days_remaining = self.get_days_remaining()
        if days_remaining <= 0:
            return TrialStatus.EXPIRED
        
        return TrialStatus.ACTIVE
    
    def is_trial_active(self) -> bool:
        """Check if trial is currently active.
        
        Returns:
            True if trial is active
        """
        return self.get_trial_status() == TrialStatus.ACTIVE
    
    def is_trial_expired(self) -> bool:
        """Check if trial has expired.
        
        Returns:
            True if trial is expired
        """
        return self.get_trial_status() == TrialStatus.EXPIRED
    
    def should_show_upgrade_prompt(self) -> Optional[str]:
        """Check if an upgrade prompt should be shown.
        
        Returns:
            Prompt type ("halfway", "last_day", "expired") or None
        """
        status = self.get_trial_status()
        
        if status == TrialStatus.UPGRADED:
            return None
        
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
            'is_upgraded': status == TrialStatus.UPGRADED,
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
        
        if status == TrialStatus.UPGRADED:
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
        
        if status == TrialStatus.UPGRADED:
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
    
    def mark_upgraded(self, email: str) -> None:
        """Mark account as upgraded.
        
        Args:
            email: Email address linked to account
        """
        account_config = self.config.config.get('account', {})
        account_config['auth_type'] = 'email'
        account_config['email'] = email
        account_config['upgraded_at'] = datetime.now().isoformat()
        
        self.config.config['account'] = account_config
        self.config.save(self.config.config)

