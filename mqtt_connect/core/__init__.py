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
