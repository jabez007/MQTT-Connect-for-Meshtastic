from textual import on
from textual.app import App, Binding, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from ..core import MeshQTTHandler
from .channel_name_modal import ChannelNameModal
from .channel_tabs import ChannelTabs
from .connection_settings_modal import ConnectionSettingsModal
from .node_list import NodeList


class MeshQTTerminal(App):
    CSS_PATH = [
        "MeshQTTerminal.tcss",
        "connection_settings_modal.tcss",
        "channel_name_modal.tcss",
        "channel_tabs.tcss",
    ]

    BINDINGS = [
        Binding("ctrl+s", "connect_server", "Connect to server"),
        Binding("ctrl+n", "new_tab", "Subscribe to channel"),
        Binding("<", "focus_left", "Shift focus left"),
        Binding(">", "focus_right", "Shift focus right"),
    ]

    def __init__(self, mqtt_handler: MeshQTTHandler | None = None):
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.node_list = NodeList()
        self.channel_tabs = ChannelTabs()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield self.node_list
            yield self.channel_tabs
            self.log("🔹 DEBUG: ChannelTabs initialized")
        yield Footer()

    def on_mount(self):
        """Set ChannelTabs as the default focus."""
        self.set_focus(self.channel_tabs)
        # self.log(f"🔹 DEBUG: Current active bindings {self.active_bindings}")

    async def action_connect_server(self):
        """Prompt the user for server connection settings."""
        self.log(f"🔹 DEBUG: Popping server connection modal.")
        await self.push_screen(ConnectionSettingsModal())

    async def action_new_tab(self):
        """Prompt the user for a channel name before creating a new tab."""
        self.log(f"🔹 DEBUG: Popping channel name modal.")
        await self.push_screen(ChannelNameModal())

    @on(ChannelNameModal.ChannelNameEntered)
    def add_new_tab(self, message: ChannelNameModal.ChannelNameEntered):
        """Handle channel name input from the pop-up screen."""
        self.log(f"🔹 DEBUG: Received tab name {message.channel_name}")
        self.channel_tabs.add_tab(message.channel_name)

    def action_focus_right(self):
        """Move focus to the right (Ctrl+L)."""
        self.log(f"🔹 DEBUG: Moving focus to the right")
        if self.focused == self.channel_tabs:
            self.set_focus(self.node_list)  # ✅ Loop back to NodeList
        else:
            self.set_focus(self.channel_tabs)

    def action_focus_left(self):
        """Move focus to the left (Ctrl+H)."""
        self.log(f"🔹 DEBUG: Moving focus to the left")
        if self.focused == self.node_list:
            self.set_focus(self.channel_tabs)  # ✅ Loop forward to ChannelTabs
        else:
            self.set_focus(self.node_list)
