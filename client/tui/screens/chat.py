"""Chat screen - AI-powered query interface for activity data."""

import asyncio
from datetime import datetime
from typing import Optional
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Input, Markdown
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.message import Message

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.query_engine import QueryEngine
from core.backend_client import BackendClient, BackendError, AuthenticationError
from utils.prompt_loader import PromptLoader
from tui.feedback_mixin import FeedbackMixin


class ChatMessage(Vertical):
    """A single chat message widget with proper markdown rendering."""

    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        height: auto;
        padding: 0 0 1 0;
    }

    ChatMessage .message-header {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    ChatMessage .message-content {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self, role: str, content: str, timestamp: str = None):
        """Initialize chat message.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Optional timestamp string
        """
        super().__init__()
        self.role = role
        self.msg_content = content
        self.timestamp = timestamp or datetime.now().strftime('%H:%M:%S')

    def compose(self) -> ComposeResult:
        """Compose the message widget."""
        # Create header based on role
        if self.role == 'user':
            header_text = f"[bold cyan]You[/bold cyan] [dim]({self.timestamp})[/dim]"
        elif self.role == 'assistant':
            header_text = f"[bold green]AI Assistant[/bold green] [dim]({self.timestamp})[/dim]"
        elif self.role == 'system':
            header_text = f"[dim italic]System[/dim italic] [dim]({self.timestamp})[/dim]"
        else:
            header_text = f"[dim]({self.timestamp})[/dim]"

        yield Static(header_text, markup=True, classes="message-header")

        # For assistant messages, use Markdown widget to properly render markdown
        if self.role == 'assistant':
            yield Markdown(self.msg_content, classes="message-content")
        else:
            # For user/system messages, use Static with markup
            if self.role == 'system':
                yield Static(f"[dim italic]{self.msg_content}[/dim italic]", markup=True, classes="message-content")
            else:
                yield Static(self.msg_content, markup=True, classes="message-content")


class ChatScreen(FeedbackMixin, Screen):
    """Chat interface for querying activity data with AI."""

    CSS = """
    ChatScreen {
        layout: vertical;
    }

    #chat-container {
        height: 1fr;
        border: solid $accent;
        padding: 1 2;
        margin: 1 2;
    }

    #chat-messages {
        height: 100%;
        overflow-y: scroll;
    }

    .chat-message {
        margin-bottom: 2;
        padding: 1 2;
        background: $panel;
        border-left: thick $accent;
        width: 100%;
    }

    .chat-message-user {
        border-left: thick cyan;
        background: #0a2a3a;
    }

    .chat-message-assistant {
        border-left: thick green;
        background: #0a2a1a;
    }

    .chat-message-system {
        border-left: thick grey;
        background: transparent;
        padding: 0 2;
    }

    #input-container {
        height: auto;
        dock: bottom;
        padding: 0 2 1 2;
    }

    #chat-input {
        width: 100%;
        border: solid $accent;
    }

    #help-text {
        color: $text-muted;
        text-style: italic;
        margin: 0 2;
        height: auto;
    }
    """

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self):
        """Initialize chat screen."""
        super().__init__()
        self.messages = []
        self.is_processing = False
        self.prompt_loader = PromptLoader()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        yield Static(
            "💬 Ask questions about your activity data. Examples: "
            "'What did I work on yesterday?' • 'Generate a LinkedIn post about building this app' • "
            "'What have I learned this week?'",
            id="help-text"
        )
        with Vertical(id="chat-container"):
            with ScrollableContainer(id="chat-messages"):
                pass  # Messages will be added dynamically
        with Horizontal(id="input-container"):
            yield Input(placeholder="Ask a question about your activity...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.title = "AI Chat"
        self.sub_title = "Query Your Activity Data"

        # Add welcome message
        self.add_message('system',
            "Ask me anything about your activity. Try: \"What did I do yesterday?\""
        )

        # Focus the input
        self.query_one("#chat-input").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission.

        Args:
            event: Input submitted event
        """
        user_query = event.value.strip()

        if not user_query:
            return

        # Check trial status before processing
        from core.trial_manager import TrialManager
        trial_manager = TrialManager(self.app.config)
        if trial_manager.is_trial_expired() and not trial_manager.is_pro():
            self.add_message("system", "❌ Trial expired. AI Chat is unavailable. Please upgrade to continue.")
            from tui.screens.upgrade import UpgradeScreen
            self.app.push_screen(UpgradeScreen(trial_manager))
            event.input.value = ""
            return

        if self.is_processing:
            self.add_message('system', "⏳ Please wait for the current query to complete...")
            return

        # Clear input
        self.query_one("#chat-input").value = ""

        # Add user message
        self.add_message('user', user_query)

        # Process query asynchronously
        self.run_worker(self.process_query(user_query))

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat.

        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = ChatMessage(role, content, timestamp)

        # Add CSS class based on role
        if role == 'user':
            message.add_class('chat-message-user')
        elif role == 'assistant':
            message.add_class('chat-message-assistant')
        elif role == 'system':
            message.add_class('chat-message-system')

        message.add_class('chat-message')

        # Add to messages container
        messages_container = self.query_one("#chat-messages")
        messages_container.mount(message)

        # Scroll to bottom
        messages_container.scroll_end(animate=False)

        # Store in history
        self.messages.append({'role': role, 'content': content, 'timestamp': timestamp})

    async def process_query(self, query: str) -> None:
        """Process user query and generate response.

        Args:
            query: User's question
        """
        self.is_processing = True

        try:
            # Show processing indicator
            self.add_message('system', "⏳ Analyzing your activity data...")

            # Get config and database
            config = self.app.config
            db = Database(config.get('storage', 'database_path'))

            # Initialize query engine
            query_engine = QueryEngine(db)

            # Determine days to search based on query
            days_back = self._estimate_days_from_query(query)

            # Get context
            context = await asyncio.to_thread(
                query_engine.get_context_for_query,
                query,
                days_back
            )

            # Format context for LLM
            context_text = await asyncio.to_thread(
                query_engine.format_context_for_llm,
                context
            )

            # Build prompt for Gemini
            system_prompt = self._build_system_prompt()
            full_prompt = f"{system_prompt}\n\n{context_text}\n\n# User Query\n{query}"

            # Call Gemini API
            api_key = config.get('gemini', 'api_key')
            model_name = config.get('gemini', 'model', default='gemini-2.5-flash')

            response_text = await asyncio.to_thread(
                self._call_gemini_api,
                api_key,
                model_name,
                full_prompt
            )

            # Increment API usage
            await asyncio.to_thread(db.increment_api_usage)

            # Remove processing message (get last system message)
            messages_container = self.query_one("#chat-messages")
            last_widget = list(messages_container.children)[-1]
            if isinstance(last_widget, ChatMessage) and last_widget.role == 'system':
                last_widget.remove()

            # Add assistant response
            self.add_message('assistant', response_text)

            # Add suggested follow-up questions
            suggestions = self._get_follow_up_suggestions(query)
            if suggestions:
                suggestion_text = "  ".join(f"[dim italic]\"{s}\"[/dim italic]" for s in suggestions)
                self.add_message('system', f"Try asking: {suggestion_text}")

        except Exception as e:
            # Remove processing message
            messages_container = self.query_one("#chat-messages")
            last_widget = list(messages_container.children)[-1]
            if isinstance(last_widget, ChatMessage) and last_widget.role == 'system':
                last_widget.remove()

            self.add_message('system', f"❌ Error: {str(e)}")

        finally:
            self.is_processing = False
            self.query_one("#chat-input").focus()

    def _get_follow_up_suggestions(self, query: str) -> list:
        """Generate contextual follow-up suggestions based on the user's query.

        Args:
            query: The user's original query

        Returns:
            List of 2-3 suggested follow-up questions
        """
        query_lower = query.lower()

        if any(w in query_lower for w in ['yesterday', 'today', 'this morning', 'this afternoon']):
            return [
                "Compare this to last week",
                "What should I focus on tomorrow?",
            ]
        elif any(w in query_lower for w in ['week', 'weekly']):
            return [
                "Which day was most productive?",
                "Break this down by app",
            ]
        elif any(w in query_lower for w in ['focus', 'productive', 'deep work']):
            return [
                "When are my peak focus hours?",
                "How can I reduce distractions?",
            ]
        elif any(w in query_lower for w in ['app', 'time spent', 'how much']):
            return [
                "Show me trends over the past week",
                "What takes up most of my time?",
            ]
        else:
            return [
                "What did I do yesterday?",
                "What are my most productive hours?",
            ]

    def _estimate_days_from_query(self, query: str) -> int:
        """Estimate how many days back to search based on query keywords.

        Args:
            query: User's query

        Returns:
            Number of days to search
        """
        query_lower = query.lower()

        if 'yesterday' in query_lower:
            return 1
        elif 'today' in query_lower:
            return 1
        elif 'this week' in query_lower or 'last week' in query_lower:
            return 14
        elif 'this month' in query_lower or 'last month' in query_lower:
            return 60
        elif 'all' in query_lower or 'everything' in query_lower:
            return 365
        else:
            return 7  # Default: last 7 days

    def _build_system_prompt(self) -> str:
        """Build system prompt for the AI assistant.

        Returns:
            System prompt string loaded from prompts/ai_chat_system.txt
        """
        return self.prompt_loader.load_prompt('ai_chat_system')

    def _call_gemini_api(self, api_key: str, model_name: str, prompt: str) -> str:
        """Call Gemini API to get response using new google-genai SDK.

        Args:
            api_key: Gemini API key
            model_name: Model to use
            prompt: Full prompt with context

        Returns:
            AI response text
        """
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        # Enable dynamic thinking for better data analysis
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1
            )
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        if response.text:
            return response.text.strip()
        else:
            raise Exception("Empty response from Gemini API")

    def get_feedback_context(self) -> dict:
        """Provide chat-specific feedback context with recent messages."""
        recent_messages = self.messages[-3:] if len(self.messages) > 0 else []
        return {
            'type': 'chat',
            'screen': 'chat',
            'recent_messages': [{'role': m['role'], 'content': m['content'][:200]} for m in recent_messages],
        }
