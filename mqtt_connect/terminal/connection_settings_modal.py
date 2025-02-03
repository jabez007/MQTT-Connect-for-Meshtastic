from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class ConnectionSettingsModal(ModalScreen):
    """A modal for entering details for connecting to MQTT server."""

    class ConnectionSettingsEntered(Message):
        """Message sent when server connection settings are entered."""

        def __init__(
            self,
            hostname: str,
            port: int,
            username: str,
            password: str,
            root_topic: str,
        ):
            super().__init__()
            self.hostname = hostname
            self.port = port
            self.username = username
            self.password = password
            self.root_topic = root_topic

    def compose(self):
        """Define UI elements."""
        with Vertical():
            with Horizontal():
                with Vertical():
                    with Horizontal():
                        yield Label("Hostname")
                        yield Input()
                with Vertical():
                    with Horizontal():
                        yield Label("Port")
                        yield Input()
            with Horizontal():
                with Vertical():
                    with Horizontal():
                        yield Label("Username")
                        yield Input()
                with Vertical():
                    with Horizontal():
                        yield Label("Password")
                        yield Input()
            with Horizontal():
                yield Label("Root topic")
                yield Input()
            yield Horizontal(
                Button("Connect", id="connect"),
                Button("Cancel", id="cancel"),
            )

    def on_key(self, event: Key):
        self.log(f"🔹 DEBUG: Caught key event [{event.name}]")
        if event.name == "escape":
            self.dismiss()
