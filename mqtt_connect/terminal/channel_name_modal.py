from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class ChannelNameModal(ModalScreen):
    """A modal for entering a new channel name."""

    CSS = """
    Horizontal {
        width: 100%;
        margin: 3;
        align: center middle;
        content-align: center middle;
    }
    Label {
        width: 20%;
        align: center middle;
        content-align: center middle; 
    }
    Input {
        width: 80%;
        align: center middle;
        content-align: center middle;
    }
    Button {
        margin: 3;
    }
    """

    class ChannelNameEntered(Message):
        """Message sent when a channel name is entered."""

        def __init__(self, channel_name: str):
            super().__init__()
            self.channel_name = channel_name

    def compose(self):
        """Define UI elements."""
        yield Vertical(
            Horizontal(Label("Enter channel name:"), Input(id="channel_name_input")),
            Horizontal(Button("Create", id="create"), Button("Cancel", id="cancel")),
        )

    def on_mount(self):
        """Focus the input box when the screen appears."""
        self.query_one("#channel_name_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        self.log(f"🔹 DEBUG: Caught submit event [{event.value}]")
        channel_name = event.value.strip()
        if channel_name != "":
            self.dismiss()
            self.post_message(self.ChannelNameEntered(channel_name))

    def on_key(self, event: Key):
        self.log(f"🔹 DEBUG: Caught key event [{event.name}]")
        if event.name == "escape":
            self.dismiss()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks."""
        if event.button.id == "create":
            channel_name = self.query_one("#channel_name_input", Input).value.strip()
            if channel_name:
                self.dismiss()
                self.post_message(self.ChannelNameEntered(channel_name))
        elif event.button.id == "cancel":
            self.dismiss()
