from . import MeshQTTHandler

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

    def on_connect(broker):
        print(f"IN CALLBACK - Connected to {broker}")
        mqtt_handler.subscribe("LongFast", "AQ==")

    def on_message(channel_name, sender, content, timestamp):
        print(
            f"IN CALLBACK - [{timestamp}]Received message on {channel_name} from {sender}: {content}"
        )

    mqtt_handler.set_connect_callback(on_connect)
    mqtt_handler.set_message_callback(on_message)
    mqtt_handler.connect()

    try:
        while True:
            pass  # Keep the script running to process messages
    except KeyboardInterrupt:
        mqtt_handler.disconnect()
