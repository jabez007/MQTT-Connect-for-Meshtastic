from ..core import MeshQTTHandler
from . import MeshQTTerminal

if __name__ == "__main__":
    app = MeshQTTerminal(
        MeshQTTHandler(
            broker="mqtt.meshtastic.org",
            port=1883,
            username="meshdev",
            password="large4cats",
            root_topic="msh/US",
            db_file="mqtt_data.db",
        )
    )
    app.run()
