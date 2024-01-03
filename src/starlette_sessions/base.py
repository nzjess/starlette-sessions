from abc import ABC, abstractmethod
from typing import Any, Iterator, MutableMapping, Optional, Tuple
from uuid import uuid4

from starlette_sessions.backend import BackendSession


class BaseBackendSession(BackendSession, ABC):
    """
    Abstract base class for implementing persistent sessions backed by a database following a standard pattern.  The
    pattern revolves around defining the content of the cookie managed by the session middle ware as a simple string
    representing the "session identifier", or sid.  This represents the primary key of the session data stored in the
    backing database.

    Concrete subclasses should implement the `_join_session` and `_open_session`, methods, depending on their needs.

    There is a fully concrete `StandardBackendSession` class provided that allows for convenient implementation of this
    pattern together with the abstract `BaseSessionBackend` class.  This allows implementations to provide only a single
    class to integrate the database of their choice as a persistent session store (see the `RedisSessionBackend` class
    as an example).
    """

    def __init__(self, sid: Optional[str]) -> None:
        self._sid = sid
        self._accessed = False
        self._modified = False
        self.__session: Optional[MutableMapping[str, Any]] = None

    @property
    def __sid_exists(self) -> bool:
        return self._sid is not None

    @property
    def __session_exists(self) -> bool:
        if self.__session is not None:
            if not self.__sid_exists:
                msg = "session not created"
                raise RuntimeError(msg)  # shouldn't happen
            return True
        return False

    @property
    def content(self) -> Optional[str]:
        if self.__session_exists:
            self._commit_session(self._sid, self.__session)  # type: ignore[arg-type]
        elif self.__sid_exists:
            self._touch_session(self._sid)  # type: ignore[arg-type]
        return self._sid

    @property
    def accessed(self) -> bool:
        return self._accessed or self._modified

    @property
    def modified(self) -> bool:
        return self._modified

    def __join_or_open_session(self) -> MutableMapping[str, Any]:
        if self.__session is None:
            if self._sid is not None:
                self.__session = self._join_session(self._sid)
            if self.__session is None:
                self._sid, self.__session = self._open_session()
        return self.__session

    @abstractmethod
    def _join_session(self, sid: str) -> Optional[MutableMapping[str, Any]]:
        """
        Joins an existing session, if it exists.  Returns the session, or None if the session did not exist.
        """
        ...

    @abstractmethod
    def _open_session(self) -> Tuple[str, MutableMapping[str, Any]]:
        """
        Opens a new session and assigns it a unique session identifier, returning the newly created session
        together with its id.
        """
        ...

    def _commit_session(self, sid: str, session: MutableMapping[str, Any]) -> None:
        """
        Ensure the session is persisted to the backing database.
        """

    def _touch_session(self, sid: str) -> None:
        """
        Ensure the session is kept alive in the backing database
        """

    def __getitem__(self, key: str) -> Optional[Any]:
        self._accessed = True
        if not self.__sid_exists:
            raise KeyError(key)
        return self.__join_or_open_session()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._accessed = True
        self.__join_or_open_session()[key] = value
        self._modified = True

    def __delitem__(self, key: str) -> None:
        self._accessed = True
        if not self.__sid_exists:
            raise KeyError(key)
        del self.__join_or_open_session()[key]
        self._modified = True

    def __len__(self) -> int:
        self._accessed = True
        if self.__sid_exists:
            len(self.__join_or_open_session())
        return 0

    def __iter__(self) -> Iterator[str]:
        self._accessed = True
        if self.__sid_exists:
            return self.__join_or_open_session().__iter__()
        return iter([])

    def clear(self) -> None:
        if self.__session_exists:
            self.__session.clear()  # type: ignore[union-attr]
            self._modified = True


class BaseSessionBackend(ABC):
    """
    Abstract base class for implementing persistent session backends following a standard pattern.

    Concrete subclasses should implement session life-cycle methods defined depending on their needs.
    """

    def __call__(self, sid: Optional[str]) -> BackendSession:
        return StandardBackendSession(self, sid)

    @abstractmethod
    def get_max_age(self) -> Optional[int]:
        """
        Returns the max age for all sessions managed by this backend, in seconds, or None if sessions
        should never expire.
        """
        ...

    def new_session(self) -> Tuple[str, MutableMapping[str, Any]]:
        """
        Creates a new session and assigns it a unique session identifier, returning the newly created session
        together with its id.

        This method has a default implementation for convenience that may be overridden if desired.
        """
        return self.new_session_id(), {}

    @staticmethod
    def new_session_id() -> str:
        return uuid4().hex

    @abstractmethod
    def load_session(self, sid: str) -> Optional[MutableMapping[str, Any]]:
        """
        Load an existing session from the backing database.  May return None if the
        session does not exist.
        """
        ...

    @abstractmethod
    def save_session(self, sid: str, session: MutableMapping[str, Any]) -> None:
        """
        Save a session to the backing database.
        """
        ...

    def keep_session(self, sid: str) -> None:  # noqa: B027
        """
        Keep the session alive, to avoid it being expired by the backing database.  This method does
        nothing be default.
        """


class StandardBackendSession(BaseBackendSession):
    """
    Convenience concrete backend session implementation that delegates to a given concrete `BaseSessionBackend`
    implementation.  This allows implementations to provide only a single class to integrate the database of their
    choice as a persistent session store (see the `RedisSessionBackend` class as an example).
    """

    def __init__(self, backend: BaseSessionBackend, sid: Optional[str]) -> None:
        super().__init__(sid)
        self.__backend = backend

    @property
    def max_age(self) -> Optional[int]:
        return self.__backend.get_max_age()

    def _open_session(self) -> Tuple[str, MutableMapping[str, Any]]:
        return self.__backend.new_session()

    def _join_session(self, sid: str) -> Optional[MutableMapping[str, Any]]:
        return self.__backend.load_session(sid)

    def _commit_session(self, sid: str, session: MutableMapping[str, Any]) -> None:
        self.__backend.save_session(sid, session)

    def _touch_session(self, sid: str) -> None:
        self.__backend.keep_session(sid)
