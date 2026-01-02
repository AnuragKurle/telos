"""Timeline screen - full day view showing sessions."""

from datetime import datetime
import json
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container, Horizontal, Vertical
from rich.text import Text

from core.database import Database


class TimelineScreen(Screen):
    """Timeline view showing all today's sessions."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]
    
    # Category color palette matching the activity graph
    CATEGORY_COLORS = {
        'work': '#5eb5e0',        # Soft cyan-blue
        'learning': '#b388eb',    # Soft purple
        'browsing': '#7cd992',    # Soft green
        'entertainment': '#f4a460', # Sandy orange
        'idle': '#3d3d4d',        # Muted dark
    }

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        with Horizontal():
            yield DataTable(id="session-table")
            with Vertical(id="detail-panel"):
                yield Static("SESSION DETAILS", id="detail-title")
                yield Static("Select a session to see rich AI analysis and detailed context.", id="detail-content")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.title = "Session Timeline"
        self.sub_title = "Today's Activity Sessions"

        # Setup table
        table = self.query_one(DataTable)
        table.cursor_type = "row"

        # Initial load - scroll to bottom to show most recent
        self._load_sessions(scroll_to_bottom=True)
        
        # Auto-refresh every 30 seconds (preserves cursor position)
        self.set_interval(30.0, self._load_sessions)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Called when a row is selected in the table."""
        row_index = event.cursor_row
        session_id = getattr(event.row_key, "value", None)
        
        if session_id:
            self.show_session_details(session_id)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Called when a row is highlighted (focused)."""
        session_id = getattr(event.row_key, "value", None)
        if session_id:
            self.show_session_details(session_id)

    def show_session_details(self, session_id: int) -> None:
        """Fetch and show details for a specific session."""
        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        
        session = db.get_session_by_id(session_id)
        if not session:
            return

        # Get category color
        cat_key = session['category'].lower()
        color = self.CATEGORY_COLORS.get(cat_key, "cyan")

        # Build detail text
        details = []
        details.append(f"[bold {color}]Category:[/bold {color}] {session['category'].title()}")
        details.append(f"[bold {color}]Task:[/bold {color}] {session['primary_task']}")
        details.append(f"[bold {color}]Duration:[/bold {color}] {session['duration_seconds'] // 60} minutes")
        
        if session.get('detailed_summary'):
            details.append(f"\n[bold green]AI Summary:[/bold green]\n{session['detailed_summary']}")
        
        if session.get('learnings'):
            details.append(f"\n[bold green]Key Learnings:[/bold green]\n{session['learnings']}")

        # Fetch captures for this session to show granular context
        captures = db.get_captures_for_session(session_id)
        if captures:
            details.append(f"\n[bold yellow]Granular Capture History ({len(captures)} captures):[/bold yellow]")
            for c in captures[-5:]:  # Show last 5 captures in the session
                time_str = datetime.fromisoformat(c['timestamp']).strftime("%H:%M:%S")
                task = c['task']
                emoji = c.get('category_emoji') or "📝"
                details.append(f"• {time_str} {emoji} {task}")
                
                # Show rich context if available
                rich_context = c.get('detailed_context')
                if rich_context:
                    try:
                        ctx = json.loads(rich_context) if isinstance(rich_context, str) else rich_context
                        if ctx.get('full_description'):
                            details.append(f"  [dim]Detail: {ctx['full_description']}[/dim]")
                        if ctx.get('ai_observations'):
                            details.append(f"  [dim]Insight: {ctx['ai_observations']}[/dim]")
                    except:
                        pass

        content = "\n".join(details)
        self.query_one("#detail-content").update(content)

    def action_refresh(self) -> None:
        """Refresh session timeline from database (called by 'r' key)."""
        self._load_sessions(scroll_to_bottom=True)

    def _load_sessions(self, scroll_to_bottom: bool = False) -> None:
        """Load sessions from database into the table.
        
        Args:
            scroll_to_bottom: If True, scroll to the most recent session
        """
        table = self.query_one(DataTable)
        
        # Remember current cursor position
        current_row = table.cursor_row if table.row_count > 0 else None

        # Get today's sessions from database
        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        sessions = db.get_sessions_for_date(datetime.now())

        # Clear existing data
        table.clear(columns=True)
        table.add_columns("Time", "Duration", "Category", "Task", "Focus")

        if not sessions:
            table.add_row("--:--", "--", "No sessions yet", "Start using the app to see sessions", "--")
            return

        # Populate table with sessions
        for session in sessions:
            start = datetime.fromisoformat(session['start_time']).strftime("%H:%M")
            duration_min = session['duration_seconds'] // 60
            duration = f"{duration_min}m"
            
            # Color code category
            raw_cat = session['category']
            cat_key = raw_cat.lower()
            color = self.CATEGORY_COLORS.get(cat_key, "white")
            
            category = Text(raw_cat.capitalize(), style=color)
            task_text = Text(session['primary_task'], style=color)
            
            # Use colored Text objects for other columns too if desired for consistent row look
            # Or keep them plain. Let's color the whole row effectively by coloring each cell text.
            start_text = Text(start, style="dim white")
            duration_text = Text(duration, style="dim white")
            
            # Truncate long tasks for table view
            task_str = session['primary_task']
            if len(task_str) > 40:
                task_str = task_str[:37] + "..."
                task_text = Text(task_str, style=color)

            # Format focus score
            focus_score = session.get('focus_score')
            if focus_score is not None:
                # Color code focus
                focus_style = "green" if focus_score > 0.7 else ("yellow" if focus_score > 0.4 else "red")
                focus = Text(f"{focus_score:.2f}", style=focus_style)
            else:
                focus = Text("Pending", style="dim")

            # Use session ID as row key
            table.add_row(start_text, duration_text, category, task_text, focus, key=str(session['id']))
        
        # Restore cursor position or scroll to bottom
        if sessions:
            num_sessions = len(sessions)
            if scroll_to_bottom or current_row is None:
                # Scroll to the bottom (most recent)
                target_row = num_sessions - 1
            elif current_row < num_sessions:
                # Restore previous position
                target_row = current_row
            else:
                # If cursor was beyond new session count, go to bottom
                target_row = num_sessions - 1
            
            # Use default argument to capture value immediately
            self.call_after_refresh(lambda r=target_row: table.move_cursor(row=r))
