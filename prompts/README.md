# Prompts Directory

This folder contains editable prompt templates for AI analysis.

## Files

| File | Purpose | When Used |
|------|---------|-----------|
| `screenshot_analysis.txt` | Analyze each screenshot | Every 30 seconds |
| `session_enrichment.txt` | Summarize grouped sessions | Every 2 hours or after idle |
| `daily_summary.txt` | End-of-day narrative | At email send time or on-demand |
| `ai_chat_system.txt` | AI Chat assistant behavior | Every AI Chat query (press 'A') |

## How to Iterate

1. **Edit the prompt file** directly with any text editor
2. **Changes take effect immediately** - no restart needed
3. **Test with**: `python main.py test` (for screenshot analysis)
4. **View results** in TUI or email reports

## Variables

Prompts use `{variable_name}` placeholders that get replaced at runtime:

### Screenshot Analysis
- `{previous_context}` - Context from previous captures (auto-generated)

### Session Enrichment
- `{duration_minutes}` - Session length
- `{category}` - Primary category (work/learning/etc)
- `{apps_used}` - Comma-separated app names
- `{capture_timeline}` - List of activities with timestamps
- `{goal_context}` - User's analysis goals

### Daily Summary
- `{date}` - Date being summarized
- `{total_minutes}` - Total active time
- `{work_minutes}`, `{learning_minutes}`, etc. - Time per category
- `{context_switches}` - Number of task switches
- `{productivity_score}` - Calculated score (0-100)
- `{session_summaries}` - List of session summaries
- `{goal_context}` - User's analysis goals

### AI Chat System
- No variables - this is a static system prompt
- Defines the AI assistant's personality, capabilities, and response style
- User's activity data is appended separately after this prompt

## Tips for Better Prompts

1. **Be specific** about what you want extracted
2. **Give examples** of ideal outputs
3. **Specify format** clearly (JSON structure)
4. **Keep it concise** - longer prompts cost more API calls
5. **Test incrementally** - change one thing at a time

### Customizing AI Chat (`ai_chat_system.txt`)

This prompt is especially valuable to customize based on your needs:

**Make the assistant more casual:**
- Edit the "General Tone" section to be more conversational
- Adjust example responses to use informal language

**Focus on specific use cases:**
- Add sections for your primary use case (e.g., "Content Creation" or "Project Tracking")
- Include examples of queries you use frequently

**Change response format:**
- Modify the "Formatting" section for your preferred output style
- Add/remove markdown elements

**Adjust personality:**
- Change how the assistant addresses you
- Modify the level of encouragement/critique
- Customize the professional vs. friendly balance

Changes take effect on the next AI Chat query (press 'A' and ask a question).

## JSON Schema

The code enforces JSON schema validation. If you change the output format,
you'll need to update the corresponding schema in the code:

- Screenshot: `core/analyzer.py` (lines 56-77)
- Session: `core/session_builder.py` (lines 241-252)
- Daily: `core/daily_aggregator.py` (lines 200-213)

