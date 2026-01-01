"""Session builder for aggregating captures into sessions."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager


class SessionBuilder:
    """Groups captures into sessions and manages enrichment."""

    def __init__(
        self,
        db: Database,
        analyzer: GeminiAnalyzer,
        goal_manager: AnalysisGoalManager,
        idle_threshold_minutes: int = 5
    ):
        """Initialize session builder.
        
        Args:
            db: Database instance
            analyzer: Gemini analyzer instance
            goal_manager: Analysis goal manager
            idle_threshold_minutes: Minutes of inactivity to trigger new session
        """
        self.db = db
        self.analyzer = analyzer
        self.goal_manager = goal_manager
        self.idle_threshold = timedelta(minutes=idle_threshold_minutes)

    def should_trigger_processing(self) -> bool:
        """Check if session processing should be triggered.
        
        Returns:
            True if enough time has passed or idle detected
        """
        # Simple heuristic: check if we have unprocessed captures
        # In a real daemon, we might check time since last run
        captures = self.db.get_unprocessed_captures(limit=1)
        return len(captures) > 0

    def build_sessions(self) -> List[int]:
        """Process unprocessed captures into sessions.
        
        Returns:
            List of created session IDs
        """
        # Get unprocessed captures
        captures = self.db.get_unprocessed_captures(limit=500)
        if not captures:
            return []

        created_session_ids = []
        current_session_captures = []
        
        # Get the end time of the last session to check for continuity
        last_session_end = self.db.get_last_session_end_time()
        
        # If we have a pending batch, the start time is the first capture's time
        # Check if there's a gap between last session and this batch
        if last_session_end and captures:
            first_capture_time = datetime.fromisoformat(captures[0]['timestamp'])
            if first_capture_time - last_session_end > self.idle_threshold:
                # Gap detected - just start fresh, logic handles this naturally
                pass

        for i, capture in enumerate(captures):
            current_time = datetime.fromisoformat(capture['timestamp'])
            
            # If this is the first capture of a potential session
            if not current_session_captures:
                current_session_captures.append(capture)
                continue

            # Check time gap with previous capture
            prev_capture = current_session_captures[-1]
            prev_time = datetime.fromisoformat(prev_capture['timestamp'])
            
            if current_time - prev_time > self.idle_threshold:
                # Gap detected -> Finalize current session
                session_id = self._create_session(current_session_captures)
                if session_id:
                    created_session_ids.append(session_id)
                current_session_captures = [capture]
            else:
                # Continuous -> Add to current session
                current_session_captures.append(capture)

        # Handle the remaining captures
        if current_session_captures:
            last_capture_time = datetime.fromisoformat(current_session_captures[-1]['timestamp'])
            if datetime.now() - last_capture_time > self.idle_threshold:
                session_id = self._create_session(current_session_captures)
                if session_id:
                    created_session_ids.append(session_id)
            else:
                # Session might still be active. 
                pass

        return created_session_ids

    def _create_session(self, captures: List[Dict]) -> Optional[int]:
        """Create a session record from a list of captures.
        
        Returns:
            Session ID if created, None otherwise
        """
        if not captures:
            return None

        start_time = datetime.fromisoformat(captures[0]['timestamp'])
        end_time = datetime.fromisoformat(captures[-1]['timestamp'])
        duration = int((end_time - start_time).total_seconds())
        
        # Minimum duration filter (e.g. < 1 min might be noise)
        if duration < 60:
            # Mark as processed but don't create session? Or merge?
            # For now, mark as processed to avoid reprocessing
            capture_ids = [c['id'] for c in captures]
            # We assign them to NULL session (processed but no session)
            # Or we can just ignore them. But if we don't process them, they stick around.
            # Let's just create the session for now to be safe and accurate.
            pass

        # Determine dominant category and primary task
        # Simple heuristic: Mode
        categories = {}
        tasks = {}
        apps = set()
        
        for c in captures:
            cat = c['category']
            categories[cat] = categories.get(cat, 0) + 1
            
            task = c['task']
            tasks[task] = tasks.get(task, 0) + 1
            
            apps.add(c['app_name'])

        dominant_category = max(categories.items(), key=lambda x: x[1])[0]
        primary_task = max(tasks.items(), key=lambda x: x[1])[0]
        apps_str = ", ".join(list(apps)[:5]) # Top 5 apps

        # Insert session
        session_id = self.db.insert_session(
            start_time=start_time,
            end_time=end_time,
            category=dominant_category,
            primary_task=primary_task,
            apps_used=apps_str,
            duration_seconds=duration
        )

        # Mark captures
        capture_ids = [c['id'] for c in captures]
        self.db.mark_captures_processed(capture_ids, session_id)
        
        return session_id

    def enrich_session(self, session_id: int) -> bool:
        """Enrich a specific session with AI analysis.
        
        Args:
            session_id: ID of session to enrich
            
        Returns:
            True if successful, False otherwise
        """
        session = self.db.get_session_by_id(session_id)
        if not session:
            return False
            
        # Skip if already enriched (unless we want to force re-enrichment?)
        # For now assume if called, we want to enrich.
        
        try:
            self._enrich_single_session(session)
            return True
        except Exception as e:
            print(f"Failed to enrich session {session_id}: {e}")
            return False

    def enrich_session_with_retry(self, session_id: int, retries: int = 3) -> bool:
        """Enrich a session with retry logic.
        
        Args:
            session_id: Session ID
            retries: Number of retries
            
        Returns:
            True if successful
        """
        # Simple wrapper for now, could add exponential backoff
        for i in range(retries):
            if self.enrich_session(session_id):
                return True
            import time
            time.sleep(1 * (i + 1))
        return False

    def enrich_sessions(self) -> int:
        """Find pending sessions and enrich them with AI analysis.
        
        Returns:
            Number of sessions enriched
        """
        # Get sessions needing enrichment
        sessions = self.db.get_sessions_needing_enrichment(limit=5)
        enriched_count = 0
        
        for session in sessions:
            try:
                self._enrich_single_session(session)
                enriched_count += 1
            except Exception as e:
                print(f"Failed to enrich session {session['id']}: {e}")
                
        return enriched_count

    def _enrich_single_session(self, session: Dict) -> None:
        """Enrich a single session with AI analysis."""
        # Get captures for context
        captures = self.db.get_captures_for_session(session['id'])
        if not captures:
            return

        # Build prompt
        prompt = self._build_enrichment_prompt(session, captures)
        
        # Call AI
        result = self._analyze_session_text(prompt)
        
        # Update DB
        self.db.update_session_enrichment(
            session_id=session['id'],
            detailed_summary=result.get('summary', ''),
            learnings=result.get('learnings', ''),
            focus_score=result.get('focus_score', 0.5)
        )

    def _build_enrichment_prompt(self, session: Dict, captures: List[Dict]) -> str:
        """Build prompt for session analysis."""
        # Summarize captures to avoid token limits
        # Take every Nth capture if too many
        step = max(1, len(captures) // 20)
        selected_captures = captures[::step]
        
        capture_summary = []
        ai_observations_collected = []
        
        for c in selected_captures:
            time_str = datetime.fromisoformat(c['timestamp']).strftime("%H:%M")
            capture_summary.append(f"[{time_str}] {c['app_name']}: {c['task']}")
            
            # Collect AI observations if available (Phase 5)
            if c.get('detailed_context'):
                try:
                    ctx = json.loads(c['detailed_context']) if isinstance(c['detailed_context'], str) else c['detailed_context']
                    if ctx.get('ai_observations'):
                        ai_observations_collected.append(f"- {ctx['ai_observations']}")
                except:
                    pass

        # Get current goal context
        goal_context = ""
        current_goal = self.goal_manager.get_current_goal()
        if current_goal:
            goal_context = f"\nUser's Current Goal/Focus: {current_goal['focus']}"
            
        apps_str = session['apps_used']
        # Truncate apps string if needed
        try:
            # If it looks like a list repr, clean it
            if apps_str.startswith('[') and apps_str.endswith(']'):
                # It might be a list string, but we store comma separated usually.
                # Just robustly handle.
                pass
        except:
            pass
            
        # Clean apps string
        apps_display = apps_str

        # Build AI observations section if any
        ai_obs_section = ""
        if ai_observations_collected:
            # deduplicate
            unique_obs = list(set(ai_observations_collected))
            ai_obs_section = f"AI Observations during session:\n{chr(10).join(unique_obs[:10])}\n"

        prompt = f'''Analyze this work session and provide insights.

Session Details:
- Duration: {session['duration_seconds'] // 60} minutes
- Category: {session['category']}
- Apps Used: {apps_display}
- Activities:
{chr(10).join(capture_summary)}
{ai_obs_section}
{goal_context}

Provide your analysis in JSON format:
{{
  "summary": "Brief 2-3 sentence summary of what was accomplished",
  "learnings": "Key insights, patterns, or learnings (or empty string if none)",
  "focus_score": 0.0-1.0 (based on consistency and minimal switching)
}}
'''
        return prompt

    def _analyze_session_text(self, prompt: str) -> Dict[str, Any]:
        """Analyze session using Gemini text-only API.

        Args:
            prompt: Prompt string

        Returns:
            Dictionary with summary, learnings, focus_score

        Raises:
            Exception: If API call fails
        """
        # Response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "learnings": {"type": "string"},
                "focus_score": {"type": "number"}
            },
            "required": ["summary", "learnings", "focus_score"]
        }
        
        # Create generation config using new SDK
        # Enable dynamic thinking for deeper session analysis
        generation_config = self.analyzer.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            thinking_config=self.analyzer.types.ThinkingConfig(
                thinking_budget=-1  # Dynamic thinking
            )
        )

        # Apply rate limiting
        self.analyzer._apply_rate_limit()

        # Call Gemini API using new SDK pattern
        response = self.analyzer.client.models.generate_content(
            model=self.analyzer.model_name,
            contents=prompt,
            config=generation_config
        )

        if not response.text:
            raise Exception("Empty response from Gemini API")

        return json.loads(response.text)
