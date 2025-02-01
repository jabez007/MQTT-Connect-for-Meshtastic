from textual.app import Binding, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, TabbedContent, TabPane


class ChannelTabs(Vertical):
    """A tabbed view for channels and their messages."""

    BINDINGS = [
        Binding("] b", "next_tab", "Next Tab"),
        Binding("[ b", "prev_tab", "Previous Tab"),
    ]

    def __init__(self, id: str = "channel-tabs", *args, **kwargs):
        super().__init__(id=id, *args, **kwargs)
        self.tabs_data = {}  # Dictionary to store topic messages
        self.tab_index = []  # List of tab IDs in order

    def compose(self) -> ComposeResult:
        self.tab_content = TabbedContent()
        yield self.tab_content
        self.log("🔹 DEBUG: ChannelTabs Content initialized")

    def add_tab(self, channel_name: str):
        """Add a new tab for a channel if it doesn't already exist."""
        self.log(f"🔹 DEBUG: Adding tab for {channel_name}")
        if channel_name not in self.tabs_data:
            new_pane_id = f"pane-{channel_name}"
            new_pane = TabPane(f"{channel_name}", id=new_pane_id)

            self.tab_content.add_pane(new_pane)
            new_pane.mount(Label(f"Messages for {channel_name}"))

            self.tabs_data[channel_name] = []
            self.tab_index.append(new_pane_id)

            # Select the newly added tab
            self.tab_content.active = new_pane_id

    def update_tab(self, channel_name: str, message: str, timestamp: str):
        """Update a tab with a new message."""
        if channel_name in self.tabs_data:
            self.tabs_data[channel_name].append((timestamp, message))
            tab_pane = self.query_one(f"#pane-{channel_name}", TabPane)
            tab_pane.mount(Label(f"[{timestamp}] {message}"))

    async def action_next_tab(self):
        """Switch to the next tab (]b)."""
        self.log(f"🔹 DEBUG: Switching to next tab")

    async def action_prev_tab(self):
        """Switch to the previous tab ([b)."""
        self.log(f"🔹 DEBUG: Switching to previous tab")

    async def key(self, event):
        """Handle <number>gt to switch to a specific tab."""
        self.log(f"🔹 DEBUG: Switching to specific tab")
