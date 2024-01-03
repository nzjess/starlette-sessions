import pickle
from typing import Any, MutableMapping, Optional, cast

from redis import Redis

from starlette_sessions import constants
from starlette_sessions.base import BaseSessionBackend


class RedisSessionBackend(BaseSessionBackend):
    """
    Stores session data in Redis, with an optional session expiry TTL.

    A Redis connection may be supplied at init, or if not a default connection will be created.
    """

    def __init__(
        self,
        redis: Optional[Redis] = None,
        ttl: Optional[int] = constants.DEFAULT_MAX_AGE,
    ) -> None:
        self.__redis = redis or Redis()
        self.__ttl = ttl

    def get_max_age(self) -> Optional[int]:
        return self.__ttl

    def load_session(self, sid: str) -> Optional[MutableMapping[str, Any]]:
        session = cast(bytes, self.__redis.get(self.__fmt_sid(sid)))
        if session is not None:
            return cast(MutableMapping[str, Any], pickle.loads(session))  # noqa: S301
        return None

    def save_session(self, sid: str, session: MutableMapping[str, Any]) -> None:
        self.__redis.set(self.__fmt_sid(sid), pickle.dumps(session), ex=self.__ttl)

    def keep_session(self, sid: str) -> None:
        if self.__ttl is not None:
            self.__redis.expire(self.__fmt_sid(sid), self.__ttl)

    @staticmethod
    def __fmt_sid(sid: str) -> str:
        return f"session:{sid}"
