import unittest
from unittest.mock import MagicMock, patch
from .core import MQTTHandler
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2

class TestMQTTHandler(unittest.TestCase):

    def setUp(self):
        self.mqtt_handler = MQTTHandler(
            broker="mqtt.test.broker",
            port=1883,
            username="user",
            password="pass",
            db_file=":memory:"  # Use in-memory database for tests
        )
        self.mqtt_handler.set_key("test/topic", "AQ==")
        self.mqtt_handler.db = MagicMock()

    @patch("mqtt_connect.core.mqtt.Client")
    def test_connect(self, mock_mqtt_client):
        mock_client_instance = mock_mqtt_client.return_value
        self.mqtt_handler.connect()
        mock_client_instance.username_pw_set.assert_called_with("user", "pass")
        mock_client_instance.connect.assert_called_with("mqtt.test.broker", 1883, 60)
        mock_client_instance.loop_start.assert_called()

    @patch("mqtt_connect.core.mqtt.Client")
    def test_disconnect(self, mock_mqtt_client):
        mock_client_instance = mock_mqtt_client.return_value
        self.mqtt_handler.disconnect()
        mock_client_instance.loop_stop.assert_called()
        mock_client_instance.disconnect.assert_called()

    def test_set_key(self):
        self.mqtt_handler.set_key("test/topic", "1PG7OiApB1nwvP+rz05pAQ==")
        self.assertEqual(self.mqtt_handler.keys["test/topic"], "1PG7OiApB1nwvP+rz05pAQ==")

    @patch("mqtt_connect.core.MQTTHandler._decrypt_message")
    def test_on_message_decrypts_and_processes(self, mock_decrypt_message):
        # Prepare mocks and test data
        mock_envelope = mqtt_pb2.ServiceEnvelope()
        mock_envelope.packet.id = 12345
        mock_envelope.packet.rx_time = 1673342400 # "2025-01-10 10:00:00"
        setattr(mock_envelope.packet, "from", 123456)
        mock_envelope.packet.encrypted = b"encrypted_data"
        #
        mock_payload = mesh_pb2.Data()
        mock_payload.portnum = portnums_pb2.TEXT_MESSAGE_APP
        mock_payload.payload = b"Test Message"
        #
        mock_decrypt_message.return_value = mock_payload
        #
        mock_msg = MagicMock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = mock_envelope.SerializeToString()

        # Test _on_message
        self.mqtt_handler._process_decrypted_message = MagicMock()
        self.mqtt_handler._on_message(None, None, mock_msg)
        self.mqtt_handler._process_decrypted_message.assert_called()

    def test_save_message_to_db(self):
        self.mqtt_handler.db.save_message = MagicMock()
        mock_packet = MagicMock()
        mock_packet.id = 123
        mock_packet.rx_time = "2025-01-10 10:00:00"
        setattr(mock_packet, "from", "test_sender")
        self.mqtt_handler._process_decrypted_message(
            mesh_pb2.Data(
                portnum=portnums_pb2.TEXT_MESSAGE_APP,
                payload=b"Hello, World!"
            ),
            MagicMock(packet=mock_packet)
        )
        self.mqtt_handler.db.save_message.assert_called_with(123, "2025-01-10 10:00:00", "test_sender", "Hello, World!")

    def test_decrypt_message_with_invalid_key(self):
        result = self.mqtt_handler._decrypt_message(MagicMock(), "invalid_key")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()

