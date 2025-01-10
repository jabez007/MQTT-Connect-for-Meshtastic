import tkinter as tk
from tkinter import scrolledtext, messagebox
from .core import MQTTHandler
from .interfaces import UIInterface


class GUI(UIInterface):
    """Tkinter-based GUI for MQTT Connect."""

    def __init__(self):
        # Initialize MQTT handler
        self.mqtt = MQTTHandler(
            broker="mqtt.meshtastic.org",
            port=1883,
            username="user",
            password="pass",
            db_file="mqtt_data.db"
        )
        self.mqtt.set_message_callback(self.on_message_received)
        self.mqtt.set_connect_callback(self.on_connect)

        # Initialize the Tkinter GUI
        self.root = tk.Tk()
        self.root.title("MQTT Connect GUI")
        self._setup_widgets()

    def _setup_widgets(self):
        """Setup GUI components."""
        # Message Log
        self.message_log = scrolledtext.ScrolledText(self.root, state='disabled', wrap=tk.WORD, height=15)
        self.message_log.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=tk.EW)

        # Node List
        self.node_list = tk.Listbox(self.root, height=10)
        self.node_list.grid(row=1, column=0, padx=10, pady=10, sticky=tk.NSEW)

        # Entry for messages
        self.message_entry = tk.Entry(self.root)
        self.message_entry.grid(row=2, column=0, padx=10, pady=5, sticky=tk.EW)

        # Buttons
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(row=2, column=1, padx=10, pady=5, sticky=tk.EW)

        self.connect_button = tk.Button(self.root, text="Connect", command=self.connect)
        self.connect_button.grid(row=3, column=0, padx=10, pady=5, sticky=tk.EW)

        self.disconnect_button = tk.Button(self.root, text="Disconnect", command=self.disconnect)
        self.disconnect_button.grid(row=3, column=1, padx=10, pady=5, sticky=tk.EW)

        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.mqtt.connect()
            self.add_log("Connecting to MQTT broker...")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.mqtt.disconnect()
        self.add_log("Disconnected from MQTT broker.")

    def send_message(self):
        """Send a message to the default topic."""
        message = self.message_entry.get()
        if message:
            self.mqtt.publish("test/topic", message)
            self.add_log(f"Sent: {message}")
            self.message_entry.delete(0, tk.END)

    def on_message_received(self, topic, message):
        """Callback for handling received MQTT messages."""
        self.add_log(f"Received on {topic}: {message}")

    def on_connect(self, broker):
        """Callback for handling successful connection."""
        self.add_log(f"Connected to broker: {broker}")
        self.update_node_list(self.mqtt.get_node_list())

    def add_log(self, message):
        """Add a message to the message log."""
        self.message_log.config(state='normal')
        self.message_log.insert(tk.END, f"{message}\n")
        self.message_log.config(state='disabled')
        self.message_log.see(tk.END)

    def update_node_list(self, nodes):
        """Update the node list display."""
        self.node_list.delete(0, tk.END)
        for node in nodes:
            self.node_list.insert(tk.END, f"{node[0]} - {node[1]} ({node[2]})")

    def run(self):
        """Start the Tkinter main loop."""
        self.mqtt.initialize_database()
        self.root.mainloop()


if __name__ == "__main__":
    gui = GUI()
    gui.run()

