"""Daily aggregator for generating summaries."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager


class DailyAggregator:
    """Generates daily summaries from sessions."""

    def __init__(
        self,
        db: Database,
        analyzer: GeminiAnalyzer,
        goal_manager: AnalysisGoalManager
    ):
        """Initialize daily aggregator.
        
        Args:
            db: Database instance
            analyzer: Gemini analyzer instance
            goal_manager: Analysis goal manager
        """
        self.db = db
        self.analyzer = analyzer
        self.goal_manager = goal_manager

    def generate_daily_summary(self, date: Optional[datetime] = None, force: bool = False) -> Optional[Dict[str, Any]]:
        """Generate summary for a specific date.
        
        Args:
            date: Date to summarize (default: today)
            force: If True, regenerate even if summary exists
            
        Returns:
            Summary dictionary or None if generation failed/skipped
        """
        if date is None:
            date = datetime.now()
            
        # Check if summary already exists
        existing = self.db.get_daily_summary(date)
        if existing and existing.get('daily_narrative') and not force:
            # Already generated
            return existing

        # If forcing regeneration, delete existing summary first
        if force and existing:
            self.db.delete_daily_summary(date)

        # Get stats for the day
        stats = self.db.get_today_stats() 
        
        # Get sessions
        sessions = self.db.get_sessions_for_date(date)
        
        # If no finalized sessions, we can still generate a summary if we have captures
        if not sessions:
            captures = self.db.get_captures_for_date(date)
            if not captures:
                return None
                
            # Create a simplified "ongoing session" for the AI to analyze
            start_time = captures[0]['timestamp']
            end_time = captures[-1]['timestamp']
            
            # Heuristic for primary task: most common task in captures
            tasks = {}
            for c in captures:
                t = c['task']
                tasks[t] = tasks.get(t, 0) + 1
            primary_task = max(tasks.items(), key=lambda x: x[1])[0] if tasks else "Unknown Activity"
            
            # Heuristic for category
            categories = {}
            for c in captures:
                cat = c['category']
                categories[cat] = categories.get(cat, 0) + 1
            dominant_cat = max(categories.items(), key=lambda x: x[1])[0] if categories else "Browsing"

            sessions = [{
                'id': 0, # Pseudo ID
                'start_time': start_time,
                'end_time': end_time,
                'category': dominant_cat,
                'primary_task': primary_task,
                'detailed_summary': "This session is currently active and has not been finalized into a formal block yet."
            }]
            
        # Generate narrative
        narrative_result = self._generate_narrative(date, sessions, stats)
        
        # Calculate aggregate metrics
        total_focus = 0
        focus_count = 0
        for s in sessions:
            if s.get('focus_score'):
                total_focus += s['focus_score']
                focus_count += 1
        
        # Default to a neutral productivity score if no focus scores available yet
        avg_focus = total_focus / max(1, focus_count) if focus_count > 0 else 0.5
        
        # Insert summary
        summary_id = self.db.insert_daily_summary(
            date=date,
            work_seconds=stats.get('work', 0),
            learning_seconds=stats.get('learning', 0),
            browsing_seconds=stats.get('browsing', 0),
            entertainment_seconds=stats.get('entertainment', 0),
            idle_seconds=stats.get('idle', 0),
            key_learnings_json=narrative_result['key_learnings_json'],
            productivity_score=avg_focus, 
            daily_narrative=narrative_result['daily_narrative'],
            context_switches=max(len(sessions), 1)
        )
        
        return self.db.get_daily_summary(date)

    def _categorize_to_simple(self, detailed_category: str) -> str:
        """
        Helper to map detailed categories to the 5 simple buckets.
        This duplicates logic from Database._categorize_activity but allows standalone use.
        """
        # Reuse DB logic or Analyzer constants
        # For now, just return lower case or 'browsing' default
        if not detailed_category:
            return 'idle'
        cat = detailed_category.lower()
        if cat in ['work', 'learning', 'browsing', 'entertainment', 'idle']:
            return cat
        # Fallback (simplified)
        return 'work' # Optimistic default for now

    def _build_narrative_prompt(self, date: datetime, sessions: List[Dict], stats: Dict) -> str:
        """Build prompt for daily narrative generation."""
        
        date_str = date.strftime("%A, %B %d, %Y")
        
        # Format session timeline
        timeline = []
        for s in sessions:
            start = datetime.fromisoformat(s['start_time']).strftime("%H:%M")
            end = datetime.fromisoformat(s['end_time']).strftime("%H:%M")
            cat = s['category']
            task = s['primary_task']
            summary = s.get('detailed_summary', '')
            timeline.append(f"- {start}-{end} [{cat}]: {task}")
            if summary:
                timeline.append(f"  Summary: {summary}")
                
        # Get goal context
        goal_context = ""
        current_goal = self.goal_manager.get_current_goal()
        if current_goal:
            goal_context = f"\nUser's Target Goal: {current_goal['focus']}"

        prompt = f'''Generate a daily productivity summary for {date_str}.

Daily Stats:
- Work: {stats.get('work', 0)//60} mins
- Learning: {stats.get('learning', 0)//60} mins
- Browsing: {stats.get('browsing', 0)//60} mins
- Entertainment: {stats.get('entertainment', 0)//60} mins

Session Timeline:
{chr(10).join(timeline)}
{goal_context}

Please provide:
1. A "Daily Narrative": A cohesive 1-paragraph story of the day's work, highlighting flow, interruptions, and major accomplishments. Write in the third person (e.g. "The user started the day...").
2. "Key Learnings": A list of bullet points (max 5) identifying habits, patterns, or specific knowledge gained.

Output in JSON format:
{{
  "daily_narrative": "...",
  "key_learnings": ["...", "..."]
}}
'''
        return prompt

    def _generate_narrative(
        self,
        date: datetime,
        sessions: List[Dict],
        stats: Dict
    ) -> Dict[str, Any]:
        """Generate narrative summary using Gemini.
        
        Args:
            date: Date of summary
            sessions: List of session dictionaries
            stats: Daily statistics dictionary
            
        Returns:
            Dictionary with daily_narrative and key_learnings_json
        """
        prompt = self._build_narrative_prompt(date, sessions, stats)
        
        try:
            # Response schema for structured output
            response_schema = {
                "type": "object",
                "properties": {
                    "daily_narrative": {"type": "string"},
                    "key_learnings": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["daily_narrative", "key_learnings"]
            }
            
            # Create generation config using new SDK
            # Enable dynamic thinking for comprehensive daily synthesis
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

            result = json.loads(response.text)

            return {
                'daily_narrative': result['daily_narrative'],
                'key_learnings_json': json.dumps(result['key_learnings'])
            }

        except Exception as e:
            print(f"Narrative generation failed: {e}")
            return {
                'daily_narrative': "Summary generation failed. Please try regenerating.",
                'key_learnings_json': json.dumps([])
            }
