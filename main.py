#!/usr/bin/env python3
import argparse
from mqtt_connect import GUI
from mqtt_connect_terminal import TerminalApp
from mqtt_connect_textual import MqttConnectApp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--terminal", action="store_true", help="Run in terminal mode")
    args = parser.parse_args()

    if args.terminal:
        textual_app = MqttConnectApp()
        terminal_ui = TerminalApp(textual_app)
        textual_app.on_mount = lambda: asyncio.create_task(terminal_ui.start())
        asyncio.run(textual_app.run_async())
    else:
        gui = GUI()
        gui.run()

if __name__ == "__main__":
    main()

