"""Activity history graph showing the last 60 minutes of activity."""

from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text
from rich.style import Style
from datetime import datetime, timedelta
from core.database import Database
from typing import List, Dict, Tuple
import asyncio
import math

from tui.theme import CATEGORY_COLORS


class ActivityWaveform(Widget):
    """Heatmap/Barcode chart showing activity history over the last 60 minutes.
    
    Visual Style: 'Digital Rain' / Heatmap
    - Full height columns (constrained to align with breakdown line)
    - Header style matches CategoryBreakdown
    """

    captures = reactive([])
    
    # 60 minutes window
    TIME_WINDOW_MINUTES = 60

    def on_mount(self):
        """Initialize when widget is mounted."""
        config = self.app.config
        db_path = config.get('storage', 'database_path')
        self.db = Database(db_path)

        # Data refresh: query database every 5 seconds
        self.set_interval(5.0, self.refresh_activity_data)
        
        # Initial load in a background task
        self.run_worker(self.refresh_activity_data())

    async def refresh_activity_data(self):
        """Query recent captures from database."""
        try:
            # Request 1 hour of history - run in thread to avoid blocking UI
            raw_captures = await asyncio.to_thread(self.db.get_recent_captures, hours=1, limit=1000)
            self.captures = raw_captures
        except Exception:
            self.captures = []
            
    def watch_captures(self, old_captures, new_captures):
        """Refresh when new data arrives."""
        self.refresh()

    def render(self):
        """Render the activity heatmap."""
        width = self.size.width
        height = self.size.height
        
        if width < 10 or height < 3:
            return Text("Waiting for data...", style="dim")
            
        # Layout:
        # Row 0: Title (bold accent)
        # Row 1: Empty padding (to align with breakdown content start)
        # Row 2: Empty padding
        # Rows 3..H-1: Heatmap area
        # Row H: Axis
        
        # Removing the separator line as requested.
        # We still need to maintain the vertical start position of the graph
        # to ensure the BARS align with the content of the breakdown widget.
        
        # Breakdown layout usually:
        # 0: Title
        # 1: Separator
        # 2: Padding/Gap
        # 3: Content starts
        
        # So we keep top_offset = 3 to start graph at row 3.
        
        top_offset = 3 
        side_padding = 2
        graph_width = width - (side_padding * 2)
        
        graph_start_y = top_offset 
        graph_end_y = height - 2 
        graph_height_rows = graph_end_y - graph_start_y + 1
        
        if graph_height_rows < 1:
            return Text("Not enough space")
        
        now = datetime.now()
        start_time = now - timedelta(minutes=self.TIME_WINDOW_MINUTES)
        total_seconds = self.TIME_WINDOW_MINUTES * 60
        seconds_per_col = total_seconds / graph_width 
        
        # Bucket captures
        buckets: List[Dict[str, int]] = [{} for _ in range(graph_width)]
        
        for capture in self.captures:
            ts_val = capture.get('timestamp')
            cat = capture.get('simple_category') or capture.get('category', 'idle')
            if not cat: cat = 'idle'
            cat = cat.lower()
            
            if isinstance(ts_val, str):
                try:
                    ts = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                    if ts.tzinfo: ts = ts.replace(tzinfo=None) 
                except:
                    continue
            else:
                ts = ts_val
                
            delta = (ts - start_time).total_seconds()
            if delta < 0 or delta > total_seconds:
                continue
                
            col_idx = int(delta / seconds_per_col)
            if 0 <= col_idx < graph_width:
                buckets[col_idx][cat] = buckets[col_idx].get(cat, 0) + 1
        
        # Fill gaps: if a bucket is empty but surrounded by activity, interpolate
        # This prevents visual gaps from 30-second capture intervals
        for i in range(1, graph_width - 1):
            if not buckets[i]:  # Empty bucket
                # Check if previous and next buckets have activity
                prev_bucket = buckets[i - 1]
                next_bucket = buckets[i + 1]
                
                if prev_bucket and next_bucket:
                    # Take the dominant category from previous bucket
                    dom_cat = max(prev_bucket.items(), key=lambda x: x[1])[0]
                    # Add reduced count to show it's interpolated
                    buckets[i][dom_cat] = max(1, sum(prev_bucket.values()) // 2)
        
        lines = []
        
        # 1. Title Line (Row 0)
        title_str = "ACTIVITY HEATMAP (LAST 60m)"
        padding_len = (width - len(title_str)) // 2
        title_line = Text(" " * max(0, padding_len))
        title_line.append(title_str, style="bold #00ddff")
        lines.append(title_line)

        # 2. Navigation hint
        nav_hint = "Press V to toggle Day View"
        nav_line = Text(" " * ((width - len(nav_hint)) // 2))
        nav_line.append(nav_hint, style="dim italic")
        lines.append(nav_line)
        
        # 3. Padding - Empty line to maintain alignment
        lines.append(Text(""))

        # 3. Heatmap Rows (with side padding)
        expected_density = max(1.0, seconds_per_col / 5.0)
        CHARS = ["░", "▒", "▓", "█"]
        
        padding_text = Text(" " * side_padding)
        
        for y in range(graph_height_rows):
            row_text = Text()
            row_text.append(padding_text) # Left padding
            
            for x in range(graph_width):
                bucket = buckets[x]
                
                is_major_tick = (x % (graph_width // 4) == 0)
                
                if not bucket:
                    # Idle / Empty
                    if is_major_tick:
                        row_text.append("│", style="dim #444444")
                    else:
                        row_text.append("·", style="dim #222222")
                    continue
                
                total = sum(bucket.values())
                dom_cat = max(bucket.items(), key=lambda item: item[1])[0]
                color = CATEGORY_COLORS.get(dom_cat, '#3d3d4d')
                
                intensity = total / expected_density
                if intensity > 0.8: char_idx = 3 
                elif intensity > 0.5: char_idx = 2
                elif intensity > 0.2: char_idx = 1 
                else: char_idx = 0 
                
                char = CHARS[char_idx]
                row_text.append(char, style=color)
            
            row_text.append(padding_text) # Right padding
            lines.append(row_text)
            
        # 4. Time Axis (with side padding)
        axis_text = Text(style="dim white")
        axis_text.append(padding_text) # Left padding
        
        markers = {
            0: "-60m",
            graph_width // 2: "-30m",
            graph_width - 4: "Now"
        }
        
        current_x = 0
        while current_x < graph_width:
            if current_x in markers:
                label = markers[current_x]
                if current_x + len(label) <= graph_width:
                    axis_text.append(label)
                    current_x += len(label)
                    continue
            
            if current_x % (graph_width // 4) == 0:
                axis_text.append("┴")
            else:
                axis_text.append("─")
            current_x += 1
            
        axis_text.append(padding_text) # Right padding
        lines.append(axis_text)
        
        # Combine
        result = Text()
        for i, line in enumerate(lines):
            result.append(line)
            if i < len(lines) - 1:
                result.append('\n')
                
        return result

