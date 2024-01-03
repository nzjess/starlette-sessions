import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any, Callable, MutableMapping, Optional, cast

from starlette_sessions import constants
from starlette_sessions.backend import BackendSession
from starlette_sessions.cookie.base import (
    BaseCookieSessionBackend,
    StandardCookieBackendSession,
)


def json_dump_bytes(content: MutableMapping[str, Any]) -> bytes:
    return json.dumps(content).encode("utf-8")


def json_load_bytes(content: bytes) -> MutableMapping[str, Any]:
    return cast(MutableMapping[str, Any], json.loads(content.decode("utf-8")))


class CookieSessionBackend(BaseCookieSessionBackend):
    """
    Stores the contents of a session in the session cookie itself, in plain text.

    +----------------------------------------------------------------------------------------------+
    | WARNING                                                                                      |
    +----------------------------------------------------------------------------------------------+
    | Any client can inspect and/or modify the contents of the session, therefore this backend     |
    | may not be suitable for all use-cases.                                                       |
    +----------------------------------------------------------------------------------------------+

    The `max_age` init parameter can be used to set the cookie headers so that clients should expire
    the cookie after certain amount of time.  Any access to the session during a server side request
    will cause the max age to be reset.

    Tne `serializer` and `deserializer` parameters can be used to customise the way the session
    contents are converted to bytes prior encoding into the cookie.  The standard Python `json`
    module is used by default, but `pickle` would work as well.
    """

    def __init__(
        self,
        max_age: Optional[int] = constants.DEFAULT_MAX_AGE,
        serializer: Callable[[MutableMapping[str, Any]], bytes] = json_dump_bytes,
        deserializer: Callable[[bytes], MutableMapping[str, Any]] = json_load_bytes,
    ) -> None:
        super().__init__(max_age)
        self.__serializer = serializer
        self.__deserializer = deserializer

    def __call__(self, content: Optional[str]) -> BackendSession:
        return StandardCookieBackendSession(self, content)

    def save_content(self, content: MutableMapping[str, Any]) -> str:
        serialized = self.__serializer(content)
        signed = self.sign_content(serialized)
        encoded = urlsafe_b64encode(signed)
        return encoded.decode("utf-8")

    def load_content(self, content: str) -> MutableMapping[str, Any]:
        try:
            decoded = urlsafe_b64decode(content.encode("utf-8"))
            unsigned = self.unsign_content(decoded)
            deserialized = self.__deserializer(unsigned)
        except (UnicodeDecodeError, ValueError):
            return {}
        else:
            return deserialized

    def sign_content(self, content: bytes) -> bytes:
        """
        Sign the serialized bytes representing the contents of a session.

        This implementation returns the bytes unchanged.  Subclass this class to customize this behaviour.
        """
        return content

    def unsign_content(self, content: bytes) -> bytes:
        """
        Unsign the serialized bytes representing the contents of a session.

        This implementation returns the bytes unchanged.  Subclass this class to customize this behaviour.
        """
        return content
