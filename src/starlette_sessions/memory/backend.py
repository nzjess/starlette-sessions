import pickle
from typing import Any, Dict, MutableMapping, Optional, cast

from starlette_sessions.base import BaseSessionBackend


class MemorySessionBackend(BaseSessionBackend):
    """
    Stores session data in memory.  Does not support session expiry.

    +----------------------------------------------------------------------------------------------+
    | WARNING                                                                                      |
    +----------------------------------------------------------------------------------------------+
    | This backend may be OK for local testing, but is probably not suitable for production.       |
    +----------------------------------------------------------------------------------------------+
    """

    def __init__(self) -> None:
        self.__storage: Dict[str, bytes] = {}

    def get_max_age(self) -> Optional[int]:
        return None

    def load_session(self, sid: str) -> Optional[MutableMapping[str, Any]]:
        session = self.__storage.get(sid)
        if session is not None:
            return cast(MutableMapping[str, Any], pickle.loads(session))  # noqa: S301
        return None

    def save_session(self, sid: str, session: MutableMapping[str, Any]) -> None:
        self.__storage[sid] = pickle.dumps(session)
