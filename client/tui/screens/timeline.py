"""Timeline screen - full day view showing sessions."""

from datetime import datetime
import json
from typing import Any
from textual.screen import Screen
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container, Horizontal, Vertical
from rich.text import Text

from core.database import Database


class TimelineScreen(Screen):
    """Timeline view showing all today's sessions or individual captures."""

    # View mode: "sessions" or "captures"
    view_mode: reactive[str] = reactive("captures")

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("v", "toggle_view", "Sessions/Captures"),
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
        self.title = "Activity Timeline"
        self._update_subtitle()

        # Setup table
        table = self.query_one(DataTable)
        table.cursor_type = "row"

        # Initial load - scroll to bottom to show most recent
        self._refresh_data(scroll_to_bottom=True)
        
        # Auto-refresh every 30 seconds (preserves cursor position)
        self.set_interval(30.0, self._refresh_data)

    def _update_subtitle(self) -> None:
        """Update the subtitle based on current view mode."""
        if self.view_mode == "sessions":
            self.sub_title = "Today's Activity Sessions"
        else:
            self.sub_title = "Granular Capture History (Every 30s)"

    def action_toggle_view(self) -> None:
        """Toggle between sessions and captures view."""
        self.view_mode = "captures" if self.view_mode == "sessions" else "sessions"
        self._update_subtitle()
        self._refresh_data(scroll_to_bottom=True)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Called when a row is selected in the table."""
        row_key = getattr(event.row_key, "value", None)
        if not row_key:
            return
            
        if self.view_mode == "sessions":
            self.show_session_details(row_key)
        else:
            self.show_capture_details(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Called when a row is highlighted (focused)."""
        row_key = getattr(event.row_key, "value", None)
        if not row_key:
            return
            
        if self.view_mode == "sessions":
            self.show_session_details(row_key)
        else:
            self.show_capture_details(row_key)

    def show_capture_details(self, capture_id: Any) -> None:
        """Fetch and show details for a specific capture."""
        try:
            cid = int(capture_id)
        except (ValueError, TypeError):
            return

        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        
        # We need a get_capture_by_id or similar. 
        # For now, let's use a raw query since it's simple.
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM captures WHERE id = ?", (cid,))
            row = cursor.fetchone()
            if not row:
                return
            capture = dict(row)

        color = self.CATEGORY_COLORS.get(capture['category'].lower(), "cyan")
        
        details = []
        details.append(f"[bold {color}]Individual Capture Details[/bold {color}]")
        details.append(f"[bold {color}]Time:[/bold {color}] {capture['timestamp']}")
        details.append(f"[bold {color}]App:[/bold {color}] {capture['app_name']}")
        details.append(f"[bold {color}]Category:[/bold {color}] {capture['category'].title()}")
        details.append(f"[bold {color}]Task:[/bold {color}] {capture['task']}")
        details.append(f"[bold {color}]AI Confidence:[/bold {color}] {capture['confidence']:.2f}")
        
        if capture.get('detailed_context'):
            try:
                ctx = json.loads(capture['detailed_context']) if isinstance(capture['detailed_context'], str) else capture['detailed_context']
                if ctx.get('full_description'):
                    details.append(f"\n[bold green]Visual Description:[/bold green]\n{ctx['full_description']}")
                if ctx.get('ai_observations'):
                    details.append(f"\n[bold yellow]AI Observations:[/bold yellow]\n{ctx['ai_observations']}")
            except:
                pass
                
        content = "\n".join(details)
        self.query_one("#detail-content").update(content)

    def show_session_details(self, session_id: Any) -> None:
        """Fetch and show details for a specific session.
        
        Args:
            session_id: Session ID (int) or "ongoing"
        """
        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        
        if session_id == "ongoing":
            # Show details from unprocessed captures
            captures = db.get_unprocessed_captures(limit=50)
            if not captures:
                self.query_one("#detail-content").update("No active session data found.")
                return
                
            last_cap = captures[-1]
            color = self.CATEGORY_COLORS.get(last_cap['category'].lower(), "yellow")
            
            details = []
            details.append(f"[bold {color}]Status:[/bold {color}] Ongoing Activity")
            details.append(f"[bold {color}]Category:[/bold {color}] {last_cap['category'].title()}")
            details.append(f"[bold {color}]Latest Task:[/bold {color}] {last_cap['task']}")
            
            start_time = datetime.fromisoformat(captures[0]['timestamp'])
            duration_min = int((datetime.now() - start_time).total_seconds()) // 60
            details.append(f"[bold {color}]Active Since:[/bold {color}] {start_time.strftime('%H:%M:%S')}")
            details.append(f"[bold {color}]Current Duration:[/bold {color}] {duration_min} minutes")
            
            details.append(f"\n[bold yellow]Recent Captures ({len(captures)}):[/bold yellow]")
            for c in captures[-5:]:
                time_str = datetime.fromisoformat(c['timestamp']).strftime("%H:%M:%S")
                emoji = c.get('category_emoji') or "📝"
                details.append(f"• {time_str} {emoji} {c['task']}")
                
            content = "\n".join(details)
            self.query_one("#detail-content").update(content)
            return

        # Regular session handling
        try:
            sid = int(session_id)
        except (ValueError, TypeError):
            return

        session = db.get_session_by_id(sid)
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
        self._refresh_data(scroll_to_bottom=True)

    def _refresh_data(self, scroll_to_bottom: bool = False) -> None:
        """Refresh data from database into the table.
        
        Args:
            scroll_to_bottom: If True, scroll to the most recent entry
        """
        if self.view_mode == "sessions":
            self._load_sessions(scroll_to_bottom)
        else:
            self._load_captures(scroll_to_bottom)

    def _load_captures(self, scroll_to_bottom: bool = False) -> None:
        """Load individual captures from database into the table."""
        table = self.query_one(DataTable)
        current_row = table.cursor_row if table.row_count > 0 else None

        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        captures = db.get_captures_for_date(datetime.now())

        table.clear(columns=True)
        table.add_columns("Time", "App", "Category", "Task", "Conf")

        if not captures:
            table.add_row("--:--:--", "--", "No captures yet", "Activity starts appearing here as it's tracked", "--")
            return

        for cap in captures:
            # Format time with seconds for granular view
            time_str = datetime.fromisoformat(cap['timestamp']).strftime("%H:%M:%S")
            
            # Use simple_category for consistent color mapping
            # Fall back to categorizing if simple_category is missing (legacy)
            raw_cat = cap['category']
            simple_cat = cap.get('simple_category')
            if not simple_cat:
                simple_cat = db._categorize_activity(raw_cat)
            
            color = self.CATEGORY_COLORS.get(simple_cat.lower(), "white")
            
            category = Text(raw_cat.capitalize(), style=color)
            
            task_str = cap['task']
            if len(task_str) > 40:
                task_str = task_str[:37] + "..."
            task_text = Text(task_str, style=color)
            
            # Also color the app name slightly for better row distinction
            app_text = Text(cap['app_name'][:20], style=f"bold {color}")
            time_text = Text(time_str, style="dim")
            conf_text = Text(f"{cap['confidence']:.2f}", style="dim")

            table.add_row(time_text, app_text, category, task_text, conf_text, key=str(cap['id']))

        self._restore_cursor(scroll_to_bottom, current_row, len(captures))

    def _load_sessions(self, scroll_to_bottom: bool = False) -> None:
        """Load sessions from database into the table."""
        table = self.query_one(DataTable)
        current_row = table.cursor_row if table.row_count > 0 else None

        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        sessions = db.get_sessions_for_date(datetime.now())
        unprocessed = db.get_unprocessed_captures(limit=100)

        table.clear(columns=True)
        table.add_columns("Time", "Duration", "Category", "Task", "Focus")

        if not sessions and not unprocessed:
            table.add_row("--:--", "--", "No sessions yet", "Start using the app to see sessions", "--")
            return

        # ... (rest of session loading logic)
        for session in sessions:
            start = datetime.fromisoformat(session['start_time']).strftime("%H:%M")
            duration_min = session['duration_seconds'] // 60
            duration = f"{duration_min}m"
            
            raw_cat = session['category']
            color = self.CATEGORY_COLORS.get(raw_cat.lower(), "white")
            category = Text(raw_cat.capitalize(), style=color)
            
            task_str = session['primary_task']
            if len(task_str) > 40:
                task_str = task_str[:37] + "..."
            task_text = Text(task_str, style=color)
            
            start_text = Text(start, style="dim white")
            duration_text = Text(duration, style="dim white")

            focus_score = session.get('focus_score')
            if focus_score is not None:
                focus_style = "green" if focus_score > 0.7 else ("yellow" if focus_score > 0.4 else "red")
                focus = Text(f"{focus_score:.2f}", style=focus_style)
            else:
                focus = Text("Pending", style="dim")

            table.add_row(start_text, duration_text, category, task_text, focus, key=str(session['id']))
            
        if unprocessed:
            first_cap = unprocessed[0]
            last_cap = unprocessed[-1]
            start_time = datetime.fromisoformat(first_cap['timestamp'])
            duration_sec = int((datetime.now() - start_time).total_seconds())
            duration_min = duration_sec // 60
            
            start_str = start_time.strftime("%H:%M")
            duration_str = f"{duration_min}m+"
            
            cat_name = last_cap['category']
            color = self.CATEGORY_COLORS.get(cat_name.lower(), "yellow")
            category = Text(cat_name.capitalize(), style=color)
            
            task_str = last_cap['task']
            if len(task_str) > 40:
                task_str = task_str[:37] + "..."
            task_text = Text(f"(Active) {task_str}", style=f"italic {color}")
            
            table.add_row(Text(start_str, style="yellow"), Text(duration_str, style="yellow"), 
                          category, task_text, Text("Ongoing", style="dim italic yellow"), key="ongoing")

        total_rows = len(sessions) + (1 if unprocessed else 0)
        self._restore_cursor(scroll_to_bottom, current_row, total_rows)

    def _restore_cursor(self, scroll_to_bottom: bool, current_row: int, total_rows: int) -> None:
        """Restore cursor position after data reload."""
        if total_rows > 0:
            table = self.query_one(DataTable)
            if scroll_to_bottom or current_row is None:
                target_row = total_rows - 1
            elif current_row < total_rows:
                target_row = current_row
            else:
                target_row = total_rows - 1
            
            self.call_after_refresh(lambda r=target_row: table.move_cursor(row=r))
