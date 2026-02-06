"""Day activity heatmap showing full 24-hour breakdown."""

import asyncio
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text
from datetime import datetime, timedelta
from core.database import Database
from typing import List, Dict

from tui.theme import CATEGORY_COLORS, INTENSITY_CHARS


class DayHeatmap(Widget):
    """Heatmap showing full day (24 hours) in 30-minute blocks.
    
    Visual Layout:
    - 24 columns (one per hour: 00, 01, 02, ... 23)
    - 2 rows per display line (first 30 min, second 30 min)
    - Expandable: Press SPACE to toggle between compact (2 rows) and expanded (detailed) view
    """

    # Reactive state
    expanded = reactive(False)
    selected_date = reactive(datetime.now().date())
    blocks = reactive([])

    def on_mount(self):
        """Initialize when widget is mounted."""
        config = self.app.config
        db_path = config.get('storage', 'database_path')
        self.db = Database(db_path)
        
        # Refresh every 30 seconds (more frequent for today's data)
        self.set_interval(30.0, self.refresh_data)
        
        # Initial load in a background task
        self.run_worker(self.refresh_data())

    async def refresh_data(self):
        """Load day blocks from database."""
        try:
            date = datetime.combine(self.selected_date, datetime.min.time())
            # Run in thread to avoid blocking UI
            self.blocks = await asyncio.to_thread(self.db.get_day_blocks, date, block_minutes=30)
        except Exception as e:
            self.blocks = []
    
    def watch_selected_date(self, old_date, new_date):
        """Refresh when date changes."""
        self.run_worker(self.refresh_data())
        
    def watch_blocks(self, old_blocks, new_blocks):
        """Refresh display when data changes."""
        self.refresh()
    
    def toggle_expanded(self):
        """Toggle between compact and expanded view (called by parent screen)."""
        self.expanded = not self.expanded
        
    def previous_day(self):
        """Go to previous day (called by parent screen).
        
        Expired trial users are limited to 7 days of history.
        """
        from core.trial_manager import TrialManager
        trial_manager = TrialManager(self.app.config)
        
        new_date = self.selected_date - timedelta(days=1)
        
        if trial_manager.is_trial_expired() and not trial_manager.is_pro():
            # Limit to 7 days back from today
            cutoff = datetime.now().date() - timedelta(days=7)
            if new_date < cutoff:
                self.app.notify(
                    "History beyond 7 days is available with Pro. Your data is preserved.",
                    severity="warning",
                    timeout=5
                )
                return
        
        self.selected_date = new_date
        
    def next_day(self):
        """Go to next day (called by parent screen)."""
        self.selected_date = self.selected_date + timedelta(days=1)

    def render(self):
        """Render the day heatmap."""
        width = self.size.width
        height = self.size.height
        
        if width < 50:
            return Text("Window too narrow for heatmap", style="dim")
        
        lines = []
        
        # Title with date
        date_str = self.selected_date.strftime("%A, %B %d, %Y")
        mode = "EXPANDED" if self.expanded else "COMPACT"
        
        # Add indicator if viewing past/future
        today = datetime.now().date()
        if self.selected_date < today:
            date_indicator = " (PAST)"
            indicator_style = "#ffaa00"
        elif self.selected_date > today:
            date_indicator = " (FUTURE)"
            indicator_style = "#00ddff"
        else:
            date_indicator = " (TODAY)"
            indicator_style = "#00ff00"
        
        title = f"DAY HEATMAP - {date_str} [{mode}]"
        title_line = Text(" " * ((width - len(title) - len(date_indicator)) // 2))
        title_line.append(title, style="bold #00ddff")
        title_line.append(date_indicator, style=f"bold {indicator_style}")
        lines.append(title_line)
        lines.append(Text())  # Empty line
        
        # Navigation hint with mode toggle
        nav_hint = "V Toggle Mode  |  ← → Change Day  |  T Jump to Today  |  SPACE Expand/Collapse"
        nav_line = Text(" " * ((width - len(nav_hint)) // 2))
        nav_line.append(nav_hint, style="dim italic")
        lines.append(nav_line)
        lines.append(Text())  # Empty line
        
        if not self.blocks:
            lines.append(Text("No activity data for this day yet.", style="dim"))
            lines.append(Text("Your heatmap fills in as Telos captures your work.", style="dim italic"))
            return self._combine_lines(lines)
        
        # Render grid
        if self.expanded:
            grid_lines = self._render_expanded()
        else:
            grid_lines = self._render_compact()
        
        lines.extend(grid_lines)
        
        # Add legend
        lines.append(Text())
        legend = self._render_legend()
        lines.append(legend)
        
        return self._combine_lines(lines)
    
    def _render_compact(self) -> List[Text]:
        """Render compact 2-row view."""
        lines = []
        
        # Hour labels (00 01 02 ... 23)
        hour_line = Text("    ")  # 4-space indent
        for hour in range(24):
            hour_line.append(f"{hour:02d} ", style="dim white")
        lines.append(hour_line)
        
        # Separator
        sep_line = Text("    " + "─" * (24 * 3), style="dim")
        lines.append(sep_line)
        
        # Row 1: First 30-min block (00-29)
        row1 = Text(":00 ")
        for hour in range(24):
            block = self._get_block(hour, 0)
            char, color = self._get_block_style(block)
            row1.append(char * 2 + " ", style=color)
        lines.append(row1)
        
        # Row 2: Second 30-min block (30-59)
        row2 = Text(":30 ")
        for hour in range(24):
            block = self._get_block(hour, 1)
            char, color = self._get_block_style(block)
            row2.append(char * 2 + " ", style=color)
        lines.append(row2)
        
        return lines
    
    def _render_expanded(self) -> List[Text]:
        """Render expanded view with more detail."""
        lines = []
        
        # Hour labels - each hour gets 3 chars (2 for number, 1 space)
        hour_line = Text("      ")  # Left padding
        for hour in range(24):
            hour_line.append(f"{hour:02d}", style="dim white")
            hour_line.append(" ", style="dim")
        lines.append(hour_line)
        
        # Top border - each hour gets 3 chars to match labels
        border = Text("      ")  # Left padding
        for _ in range(24):
            border.append("┬──", style="dim")
        lines.append(border)
        
        # Each hour gets a vertical cell with both blocks shown
        for block_idx in range(2):
            time_label = ":00" if block_idx == 0 else ":30"
            row = Text(f" {time_label}  ")
            
            for hour in range(24):
                block = self._get_block(hour, block_idx)
                char, color = self._get_block_style(block)
                
                # Show with border - 3 chars per hour (│ + char + space)
                row.append("│", style="#555555")
                row.append(char, style=color)
                row.append(" ", style="dim")
                
            lines.append(row)
            
            # Add separator between blocks
            if block_idx == 0:
                sep = Text("      ")
                for _ in range(24):
                    sep.append("├──", style="#333333")
                lines.append(sep)
        
        # Bottom border
        bottom = Text("      ")
        for _ in range(24):
            bottom.append("┴──", style="dim")
        lines.append(bottom)
        
        # Add hourly stats
        lines.append(Text())
        stats_line = Text("Peak hours: ", style="bold")
        # Calculate top 3 most active hours
        hourly_activity = {}
        for hour in range(24):
            total = sum(self._get_block(hour, b)['total_captures'] for b in range(2))
            hourly_activity[hour] = total
        
        top_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (hour, count) in enumerate(top_hours):
            if count > 0:
                stats_line.append(f"{hour:02d}:00 ({count} captures)", style="cyan")
                if i < 2:
                    stats_line.append(", ")
        
        lines.append(stats_line)
        
        return lines
    
    def _get_block(self, hour: int, block_idx: int) -> Dict:
        """Get block data for specific hour and 30-min block."""
        # Find block in self.blocks list
        for block in self.blocks:
            if block['hour'] == hour and block['block'] == block_idx:
                return block
        
        # Return empty block if not found
        return {
            'hour': hour,
            'block': block_idx,
            'dominant_category': 'idle',
            'total_captures': 0,
            'activity_level': 0.0,
            'category_counts': {}
        }
    
    def _get_block_style(self, block: Dict) -> tuple:
        """Get character and color for a block.
        
        Returns:
            (character, color_code)
        """
        category = block['dominant_category'] or 'idle'
        activity = block['activity_level']
        
        # Choose character based on activity level
        char_idx = int(activity * (len(INTENSITY_CHARS) - 1))
        char = INTENSITY_CHARS[char_idx]
        
        # Get color for category
        color = CATEGORY_COLORS.get(category, '#3d3d4d')
        
        return char, color
    
    def _render_legend(self) -> Text:
        """Render color legend."""
        legend = Text("  Legend: ", style="dim")
        
        for cat, color in CATEGORY_COLORS.items():
            if cat != 'idle':  # Skip idle in legend
                legend.append("█ ", style=color)
                legend.append(f"{cat.title()}  ", style="dim")
        
        return legend
    
    def _combine_lines(self, lines: List[Text]) -> Text:
        """Combine text lines with newlines."""
        result = Text()
        for i, line in enumerate(lines):
            result.append(line)
            if i < len(lines) - 1:
                result.append('\n')
        return result

