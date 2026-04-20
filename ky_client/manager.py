from .client import KYClient


class KYClientManager:
    def __init__(self, username: str, password: str, idp: str) -> None:
        # Initialize client - this will block until login completes
        self._client = KYClient(username, password, idp)
