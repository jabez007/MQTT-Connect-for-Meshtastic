from textual.containers import Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Input, Label


class ChannelNameModal(Screen):
    """A modal for entering a new channel name."""

    class ChannelNameEntered(Message):
        """Message sent when a channel name is entered."""

        def __init__(self, channel_name: str):
            super().__init__()
            self.channel_name = channel_name

    def compose(self):
        """Define UI elements."""
        yield Vertical(
            Label("Enter channel name:"),
            Input(id="channel_name_input"),
            Button("Create", id="create"),
            Button("Cancel", id="cancel"),
        )

    def on_mount(self):
        """Focus the input box when the screen appears."""
        self.query_one("#channel_name_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks."""
        if event.button.id == "create":
            channel_name = self.query_one("#channel_name_input", Input).value.strip()
            if channel_name:
                self.dismiss()
                self.post_message(self.ChannelNameEntered(channel_name))
        elif event.button.id == "cancel":
            self.dismiss()
