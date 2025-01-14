from typing import Optional

from ._client import MeshQTTClient


class MeshQTTHandler(MeshQTTClient):

    def __init__(
        self,
        broker: str,
        port: Optional[int],
        username: Optional[str],
        password: Optional[str],
        root_topic: str = "msh/US",
        db_file: Optional[str] = None,
    ):
        MeshQTTClient.__init__(
            self, broker, port, username, password, root_topic, db_file
        )
        self.client.on_message = self._on_message

    from ._receive import (_decrypt_message, _get_channel, _get_key,
                           _on_message, _process_decrypted_message)


if __name__ == "__main__":
    # Example usage
    mqtt_handler = MeshQTTHandler(
        broker="mqtt.meshtastic.org",
        port=1883,
        username="meshdev",
        password="large4cats",
        root_topic="msh/US",
        db_file="mqtt_data.db",
    )

    def on_message(channel_name, sender, content, timestamp):
        print(
            f"[{timestamp}]Received message on {channel_name} from {sender}: {content}"
        )

    mqtt_handler.set_message_callback(on_message)
    mqtt_handler.connect()
    mqtt_handler.subscribe("LongFast", "AQ==")

    try:
        while True:
            pass  # Keep the script running to process messages
    except KeyboardInterrupt:
        mqtt_handler.disconnect()
