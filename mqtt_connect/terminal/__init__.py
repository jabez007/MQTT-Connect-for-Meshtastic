from textual import on
from textual.app import App, Binding, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Tabs

from ..core import MeshQTTHandler
from .channel_name_modal import ChannelNameModal
from .channel_tabs import ChannelTabs
from .node_list import NodeList


class MeshQTTerminal(App):
    CSS = """
    LeftPane {
        width: 30%;
    }
    MainPane {
        width: 70%;
    }
    TextBox {
        height: 3;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_tab", "New Tab"),
    ]

    def __init__(self, mqtt_handler: MeshQTTHandler | None = None):
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.nodes_list = NodeList(classes="LeftPane")
        self.channel_tabs = ChannelTabs(classes="MainPane")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            # yield self.nodes_list
            yield self.channel_tabs
            self.log("🔹 DEBUG: ChannelTabs initialized")
        yield Footer()

    async def action_new_tab(self):
        """Prompt the user for a channel name before creating a new tab."""
        await self.push_screen(ChannelNameModal())

    @on(ChannelNameModal.ChannelNameEntered)
    def add_new_tab(self, message: ChannelNameModal.ChannelNameEntered):
        """Handle channel name input from the pop-up screen."""
        self.log(f"🔹 DEBUG: Received tab name {message.channel_name}")
        self.channel_tabs.add_tab(message.channel_name)
