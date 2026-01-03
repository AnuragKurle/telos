"""
Prompt Loader Utility

Loads prompts from prompts/ folder with fallback to hardcoded defaults.
Supports variable substitution for dynamic prompts.
"""

from pathlib import Path
from typing import Dict, Optional


class PromptLoader:
    """Load prompts from prompts/ folder with fallback to defaults."""

    # Default prompts if files are missing
    DEFAULT_PROMPTS = {
        'screenshot_analysis': """Analyze this screenshot and categorize the user's activity.

## Previous Context
{previous_context}

## Output Fields

### category (string)
Common categories: work, learning, browsing, entertainment, idle
You can also use: debugging, meeting, research, communication, creative, planning, break, etc.

### app (string, max 50 chars)
Application name. Include filename if relevant: "VSCode - email_reporter.py"

### task (string, max 80 chars)
Short, human-readable description. Keep it CONCISE.

### confidence (number 0.0-1.0)

### detailed_context (object, optional)
Include if visible:
- file_name: Current file
- cursor_position: Line number
- browser_url: Website URL
- full_description: Detailed task description (max 200 chars)
- progress_from_last: What changed since last capture
- ai_observations: Your insights about patterns
- suggested_category: If a different category fits better

Return valid JSON only.""",

        'session_enrichment': """Analyze this work session and provide insights.

## Session Details
- Duration: {duration_minutes} minutes
- Category: {category}
- Apps Used: {apps_used}
- Activities:
{capture_timeline}

{goal_context}

Provide analysis in JSON format:
{
  "summary": "2-3 sentence summary of accomplishments",
  "learnings": "Key insights or learnings (or empty string)",
  "focus_score": 0.0-1.0
}""",

        'daily_summary': """Generate a daily summary for {date}.

## Daily Statistics
- Total active time: {total_minutes} minutes
- Work: {work_minutes}m
- Learning: {learning_minutes}m
- Browsing: {browsing_minutes}m
- Entertainment: {entertainment_minutes}m
- Context switches: {context_switches}
- Productivity score: {productivity_score}/100

## Session Timeline
{session_summaries}

{goal_context}

Provide analysis in JSON format:
{
  "daily_narrative": "3-4 sentence narrative of the day",
  "key_learnings": ["Learning 1", "Learning 2", ...]
}""",

        'ai_chat_system': """You are an AI assistant that helps users understand and analyze their computer activity data.

You have access to:
- Individual captures (screenshots analyzed every 30 seconds with detailed context)
- Sessions (grouped activities with AI summaries)
- Daily summaries (productivity scores, learnings, focus blocks)

Your job is to:
1. Answer questions about what the user worked on
2. Generate content (LinkedIn posts, tweets, marketing material) based on their work
3. Extract insights and patterns from their activity
4. Help them recall specific projects or learnings

Guidelines:
- Be concise and helpful
- When generating content (posts, tweets), make it engaging and professional
- Use specific details from the data (file names, apps, timestamps)
- For creative requests (LinkedIn posts, marketing), be creative but accurate
- If data is insufficient, say so clearly
- Format your responses with markdown for readability

Important:
- The user's data is private and local - treat it with respect
- Focus on being helpful and insightful
- If asked to generate content, make it polished and ready to use"""
    }

    def __init__(self, prompts_dir: str = None):
        """Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt files. If None, searches
                        standard locations (./prompts, ~/.telos/prompts)
        """
        if prompts_dir is not None:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = self._find_prompts_dir()
    
    def _find_prompts_dir(self) -> Path:
        """Find prompts directory in standard locations."""
        # Check current directory first (development mode)
        cwd_prompts = Path("prompts")
        if cwd_prompts.exists():
            return cwd_prompts
        
        # Check user data directory (pip install mode)
        user_prompts = Path.home() / ".telos" / "prompts"
        if user_prompts.exists():
            return user_prompts
        
        # Default to current directory (will use hardcoded defaults)
        return cwd_prompts

    def load_prompt(self, prompt_name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """Load prompt from file and optionally substitute variables.

        Args:
            prompt_name: Name of prompt (without .txt extension)
            variables: Dictionary of variables to substitute

        Returns:
            Prompt string with variables substituted
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"

        if prompt_path.exists():
            try:
                prompt = prompt_path.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Error reading prompt file {prompt_path}: {e}")
                prompt = self._get_default_prompt(prompt_name)
        else:
            prompt = self._get_default_prompt(prompt_name)

        # Substitute variables if provided
        if variables:
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def _get_default_prompt(self, prompt_name: str) -> str:
        """Get default prompt if file is missing.

        Args:
            prompt_name: Name of prompt

        Returns:
            Default prompt string
        """
        if prompt_name in self.DEFAULT_PROMPTS:
            return self.DEFAULT_PROMPTS[prompt_name]

        # Generic fallback
        return f"Analyze the input and provide a response for: {prompt_name}"

    def prompt_exists(self, prompt_name: str) -> bool:
        """Check if a prompt file exists.

        Args:
            prompt_name: Name of prompt

        Returns:
            True if file exists
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        return prompt_path.exists()

    def list_prompts(self) -> list:
        """List all available prompt files.

        Returns:
            List of prompt names (without .txt extension)
        """
        if not self.prompts_dir.exists():
            return list(self.DEFAULT_PROMPTS.keys())

        prompts = []
        for file in self.prompts_dir.glob("*.txt"):
            if file.name != "README.md":
                prompts.append(file.stem)

        # Add defaults that don't have files
        for default in self.DEFAULT_PROMPTS:
            if default not in prompts:
                prompts.append(default)

        return sorted(prompts)

