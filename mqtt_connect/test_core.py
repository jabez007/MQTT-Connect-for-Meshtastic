import base64
import unittest
from unittest.mock import MagicMock, patch

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2

from .core import MeshQTTHandler


class TestMeshQTTHandler(unittest.TestCase):

    def setUp(self):
        self.mqtt_handler = MeshQTTHandler(
            broker="mqtt.test.broker",
            port=1883,
            username="user",
            password="pass",
            db_file=":memory:",  # Use in-memory database for tests
        )
        self.mqtt_handler.set_key("test_topic", "AQ==")
        self.mqtt_handler.db = MagicMock()

    @patch("mqtt_connect.core._client.mqtt.Client")
    def test_connect(self, mock_mqtt_client):
        mock_client_instance = mock_mqtt_client.return_value
        self.mqtt_handler.client = mock_client_instance
        self.mqtt_handler.connect()
        mock_client_instance.username_pw_set.assert_called_with("user", "pass")
        mock_client_instance.connect.assert_called_with("mqtt.test.broker", 1883, 60)
        mock_client_instance.loop_start.assert_called()

    @patch("mqtt_connect.core._client.mqtt.Client")
    def test_disconnect(self, mock_mqtt_client):
        mock_client_instance = mock_mqtt_client.return_value
        self.mqtt_handler.client = mock_client_instance
        self.mqtt_handler.disconnect()
        mock_client_instance.loop_stop.assert_called_once()
        mock_client_instance.disconnect.assert_called_once()

    def test_set_key(self):
        self.mqtt_handler.set_key("LongFast", "1PG7OiApB1nwvP+rz05pAQ==")
        self.assertEqual(self.mqtt_handler.keys["LongFast"], "1PG7OiApB1nwvP+rz05pAQ==")

    def test_get_key(self):
        self.mqtt_handler.set_key("LongFast", "AQ==")
        self.assertEqual(
            self.mqtt_handler._get_key(
                self.mqtt_handler.root_topic + "/2/e/LongFast/!abcd1234"
            ),
            "AQ==",
        )

    def test_decrypt_message_success(self):
        # Simulate key
        shared_key = "1PG7OiApB1nwvP+rz05pAQ=="  # Base64-encoded key
        key_bytes = base64.b64decode(shared_key.encode("ascii"))

        # Generate nonce
        nonce = (987).to_bytes(8, "little") + (123456).to_bytes(8, "little")

        # Prepare mocks and test data
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        setattr(mock_envelope.packet, "from", 123456)

        # Simulate decrypted message
        decrypted_data = mesh_pb2.Data(
            portnum=portnums_pb2.TEXT_MESSAGE_APP, payload=b"Hello, World!"
        )
        decrypted_bytes = decrypted_data.SerializeToString()

        # Simulate encrypted data
        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(decrypted_bytes) + encryptor.finalize()
        mock_envelope.packet.encrypted = encrypted_data

        # Act
        result = self.mqtt_handler._decrypt_message(mock_envelope.packet, shared_key)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.portnum, portnums_pb2.TEXT_MESSAGE_APP)
        self.assertEqual(result.payload.decode("utf-8"), "Hello, World!")

    def test_decrypt_message_with_invalid_key(self):
        result = self.mqtt_handler._decrypt_message(MagicMock(), "invalid_key")
        self.assertIsNone(result)

    def test_on_message_decrypts_and_processes(self):
        from .core import _receive as mock_receive

        # Prepare mocks and test data
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 12345
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)
        mock_envelope.packet.encrypted = b"encrypted_data"
        #
        mock_payload = mesh_pb2.Data()
        mock_payload.portnum = portnums_pb2.TEXT_MESSAGE_APP
        mock_payload.payload = b"Test Message"
        #
        mock_receive._decrypt_message = MagicMock(return_value=mock_payload)
        mock_receive._process_decrypted_message = MagicMock()
        #
        mock_msg = MagicMock()
        mock_msg.topic = self.mqtt_handler.root_topic + "/2/e/" + "test_topic"
        mock_msg.payload = mock_envelope.SerializeToString()

        # Test _on_message
        mock_receive._on_message(self.mqtt_handler, None, None, mock_msg)
        mock_receive._decrypt_message.assert_called_with(
            self.mqtt_handler, mock_envelope.packet, "AQ=="
        )
        mock_receive._process_decrypted_message.assert_called_with(
            self.mqtt_handler,
            mock_payload,
            mock_envelope,
            "test_topic",
        )

    def test_text_message_callback(self):
        # Prepare mocks and test data
        decoded_message = mesh_pb2.Data(
            portnum=portnums_pb2.TEXT_MESSAGE_APP, payload=b"Hello, World!"
        )
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)

        callback = MagicMock()
        self.mqtt_handler.set_message_callback(callback)
        self.mqtt_handler.db.save_message = MagicMock()

        # Act
        self.mqtt_handler._process_decrypted_message(
            decoded_message, mock_envelope, "test_topic"
        )

        # Assert
        self.mqtt_handler.db.save_message.assert_called_with(
            "test_topic", 987, 1673342400, 123456, "Hello, World!"
        )
        callback.assert_called_once_with(
            "test_topic",  # Channel Name
            123456,  # Sender
            "Hello, World!",  # Message content
            1673342400,  # Timestamp
        )

    def test_nodeinfo_callback(self):
        # Prepare mocks and test data
        node_info = mesh_pb2.User(
            id="node123", short_name="ShortName", long_name="LongName"
        )
        decoded_message = mesh_pb2.Data(
            portnum=portnums_pb2.NODEINFO_APP, payload=node_info.SerializeToString()
        )
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)

        callback = MagicMock()
        self.mqtt_handler.set_nodeinfo_callback(callback)
        self.mqtt_handler.db.save_node_info = MagicMock()

        # Act
        self.mqtt_handler._process_decrypted_message(
            decoded_message, mock_envelope, "test_topic"
        )

        # Assert
        self.mqtt_handler.db.save_node_info.assert_called_with(
            "node123", "ShortName", "LongName"
        )
        callback.assert_called_once_with(
            "node123", "ShortName", "LongName"  # Node ID  # Short name  # Long name
        )

    def test_position_callback(self):
        # Prepare mocks and test data
        position = mesh_pb2.Position(
            latitude_i=int(37.7749 * 1e7),  # Example latitude
            longitude_i=int(-122.4194 * 1e7),  # Example longitude
            altitude=30,  # Example altitude
            time=1673342400,  # Example timestamp
        )
        decoded_message = mesh_pb2.Data(
            portnum=portnums_pb2.POSITION_APP, payload=position.SerializeToString()
        )
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)

        callback = MagicMock()
        self.mqtt_handler.set_position_callback(callback)
        self.mqtt_handler.db.save_position = MagicMock()

        # Act
        self.mqtt_handler._process_decrypted_message(
            decoded_message, mock_envelope, "test_topic"
        )

        # Assert
        self.mqtt_handler.db.save_position.assert_called_with(
            123456, 37.7749, -122.4194, 30, 1673342400
        )
        callback.assert_called_once_with(
            123456,  # Node ID
            37.7749,  # Latitude
            -122.4194,  # Longitude
            30,  # Altitude
        )

    def test_device_telemetry_callback(self):
        # Prepare mocks and test data
        telemetry = telemetry_pb2.Telemetry()
        telemetry.device_metrics.battery_level = 30  # Example battery_level

        decoded_message = mesh_pb2.Data(
            portnum=portnums_pb2.TELEMETRY_APP, payload=telemetry.SerializeToString()
        )
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)

        callback = MagicMock()
        self.mqtt_handler.set_telemetry_callback(callback)
        self.mqtt_handler.db.save_telemetry = MagicMock()

        # Act
        self.mqtt_handler._process_decrypted_message(
            decoded_message, mock_envelope, "test_topic"
        )

        # Assert
        self.mqtt_handler.db.save_telemetry.assert_called_with(
            123456, 30, None, None, None
        )
        callback.assert_called_once_with(
            123456,  # Node ID
            30,  # Battery level
            None,  # Temperature
            None,  # Humidity
            None,  # Pressure
        )

    def test_environment_telemetry_callback(self):
        # Prepare mocks and test data
        telemetry = telemetry_pb2.Telemetry()
        telemetry.environment_metrics.temperature = 22.5  # Example temperature
        telemetry.environment_metrics.relative_humidity = 60.0  # Example humidity
        telemetry.environment_metrics.barometric_pressure = 1013.25  # Example pressure

        decoded_message = mesh_pb2.Data(
            portnum=portnums_pb2.TELEMETRY_APP, payload=telemetry.SerializeToString()
        )
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 987
        mock_envelope.packet.rx_time = 1673342400  # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)

        callback = MagicMock()
        self.mqtt_handler.set_telemetry_callback(callback)
        self.mqtt_handler.db.save_telemetry = MagicMock()

        # Act
        self.mqtt_handler._process_decrypted_message(
            decoded_message, mock_envelope, "test_topic"
        )

        # Assert
        self.mqtt_handler.db.save_telemetry.assert_called_with(
            123456, None, 22.5, 60.0, 1013.25
        )
        callback.assert_called_once_with(
            123456,  # Node ID
            None,  # Battery level
            22.5,  # Temperature
            60.0,  # Humidity
            1013.25,  # Pressure
        )


if __name__ == "__main__":
    unittest.main()
