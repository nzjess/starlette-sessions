from typing import Any, Callable, MutableMapping, Optional, Union

from itsdangerous import BadSignature, TimestampSigner
from starlette.datastructures import Secret

from starlette_sessions import constants
from starlette_sessions.cookie.backend import (
    CookieSessionBackend,
    json_dump_bytes,
    json_load_bytes,
)


class SignedCookieSessionBackend(CookieSessionBackend):
    """
    Stores the contents of a session in the session cookie itself, signed with a secret key..

    The `max_age` init parameter can be used to set the cookie headers so that clients should expire
    the cookie after certain amount of time.  Any access to the session during a server side request
    will cause the max age to be reset.  The session will also expire even if the client does not
    do it itself.

    Tne `serializer` and `deserializer` parameters can be used to customise the way the session
    contents are converted to bytes prior encoding into the cookie.  The standard Python `json`
    module is used by default, but `pickle` would work as well.
    """

    def __init__(
        self,
        secret_key: Union[str, Secret],
        max_age: Optional[int] = constants.DEFAULT_MAX_AGE,
        serializer: Callable[[MutableMapping[str, Any]], bytes] = json_dump_bytes,
        deserializer: Callable[[bytes], MutableMapping[str, Any]] = json_load_bytes,
    ) -> None:
        super().__init__(
            max_age,
            serializer,
            deserializer,
        )
        self.__timestamper = TimestampSigner(str(secret_key))

    def sign_content(self, content: bytes) -> bytes:
        return self.__timestamper.sign(content)

    def unsign_content(self, content: bytes) -> bytes:
        try:
            return self.__timestamper.unsign(content, max_age=self.get_max_age())
        except BadSignature as e:
            raise ValueError from e
