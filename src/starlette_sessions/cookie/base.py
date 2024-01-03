from abc import ABC, abstractmethod
from typing import Any, Iterator, MutableMapping, Optional

from starlette_sessions.backend import BackendSession


class StandardCookieBackendSession(BackendSession):
    def __init__(self, backend: "BaseCookieSessionBackend", content: Optional[str]) -> None:
        self.__content = backend.load_content(content) if content is not None else {}
        self.__backend = backend
        self.__accessed = False
        self.__cleared = False

    @property
    def max_age(self) -> Optional[int]:
        return self.__backend.get_max_age()

    @property
    def content(self) -> Optional[str]:
        if self.__cleared:
            return None
        return self.__backend.save_content(dict(self))

    @property
    def accessed(self) -> bool:
        return self.__accessed

    def __getitem__(self, key: str) -> Any:
        self.__accessed = True
        return self.__content.__getitem__(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.__accessed = True
        self.__content.__setitem__(key, value)
        self.__cleared = False

    def __delitem__(self, key: str) -> None:
        self.__accessed = True
        self.__content.__delitem__(key)

    def __len__(self) -> int:
        self.__accessed = True
        return self.__content.__len__()

    def __iter__(self) -> Iterator[str]:
        self.__accessed = True
        return self.__content.__iter__()

    def clear(self) -> None:
        self.__accessed = True
        super().clear()
        self.__cleared = True


class BaseCookieSessionBackend(ABC):
    def __init__(self, max_age: Optional[int]) -> None:
        self.__max_age = max_age

    def get_max_age(self) -> Optional[int]:
        return self.__max_age

    @abstractmethod
    def save_content(self, content: MutableMapping[str, Any]) -> str:
        """
        Convert the contents of a session into a string representation suitable to be stored in a cookie.
        """
        ...

    @abstractmethod
    def load_content(self, content: str) -> MutableMapping[str, Any]:
        """
        Load the contents of a session from a string representation taken from a cookie value.
        """
        ...
