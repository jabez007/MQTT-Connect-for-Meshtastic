import argparse
import asyncio
from textual.app import App
from textual.widgets import Header, Footer, TextArea, Button, DataTable
from textual.containers import Container, Horizontal
from textual.reactive import reactive

class MqttConnectApp(App):
    """Textual terminal app for MQTT Connect."""
    CSS = """
    Screen {
        align: center middle;
        height: 100%;
        width: 100%;
    }
    """

    message_log = reactive("")

    async def on_load(self):
        await self.bind("q", "quit", "Quit")
        await self.bind("m", "switch_to_message_log", "Message Log")
        await self.bind("n", "switch_to_node_list", "Node List")

    async def on_mount(self):
        # Header and Footer
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Message log screen
        self.message_area = TextArea("Message log will appear here.")
        self.message_screen = Container(
            self.message_area, style="height:100%; width:100%; overflow:scroll"
        )

        # Node info screen
        self.node_list = DataTable()
        self.node_list.add_columns("Node ID", "Short Name", "Long Name")
        self.node_screen = Container(self.node_list, style="height:100%; width:100%;")

        # Initial screen
        await self.view.dock(self.message_screen, edge="main", name="main")
        self.current_screen = "message"

    async def action_switch_to_message_log(self):
        if self.current_screen != "message":
            await self.view.dock(self.message_screen, edge="main", name="main")
            await self.view.remove(self.node_screen)
            self.current_screen = "message"

    async def action_switch_to_node_list(self):
        if self.current_screen != "node":
            await self.view.dock(self.node_screen, edge="main", name="main")
            await self.view.remove(self.message_screen)
            self.current_screen = "node"

    async def append_message(self, message):
        self.message_log += f"\n{message}"
        self.message_area.update(self.message_log)

    async def update_node_list(self, nodes):
        self.node_list.clear()
        for node in nodes:
            self.node_list.add_row(*node)

async def run_terminal_app():
    app = MqttConnectApp()

    async def backend_simulator():
        await asyncio.sleep(2)
        await app.append_message("Connected to MQTT Broker.")
        await asyncio.sleep(2)
        await app.update_node_list([
            ("!abcd1234", "ShortName1", "LongName1"),
            ("!abcd5678", "ShortName2", "LongName2"),
        ])
        await app.append_message("New message received.")

    asyncio.create_task(backend_simulator())
    await app.run_async()

def main():
    parser = argparse.ArgumentParser(description="MQTT Connect Application")
    parser.add_argument(
        "--terminal", action="store_true", help="Run in terminal mode using Textual"
    )
    args = parser.parse_args()

    if args.terminal:
        asyncio.run(run_terminal_app())
    else:
        # Import the existing tkinter GUI logic and start it
        from mqtt_connect_gui import run_gui
        run_gui()

if __name__ == "__main__":
    main()

