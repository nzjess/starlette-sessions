from abc import abstractmethod
from typing import Any, Callable, MutableMapping, Optional


class BackendSession(MutableMapping[str, Any]):
    """
    Interface for implementing a persistent session backed by some storage scheme.
    """

    @property
    @abstractmethod
    def max_age(self) -> Optional[int]:
        """
        The maximum age of this session, in seconds (optional).  If None, then the session never expires.
        The session cookie middleware uses this to set the 'Max-Age' property on the cookie header.
        """
        ...

    @property
    @abstractmethod
    def content(self) -> Optional[str]:
        """
        The value to use for the content of the cookie (optional).  Most session backends that utilise a backend
        database of any kind would typically just return a unique identifier that points to the session data being
        stored for this session.  If None, then the session no longer exists, and the session cookie middleware will
        remove the cookie, too.
        """
        ...

    @property
    @abstractmethod
    def accessed(self) -> bool:
        """
        Returns True if the session has been accessed at all during the request (False otherwise).  Used by the
        session cookie middleware to negotiate cookie updates and/or remove cookies for sessions that have been
        removed.
        """


#
# Interface for implementing a session backend that manages a set of persistent sessions
# backed by some storage scheme.
#
# Implementations must implement a callable that takes some optional content (provided by the session cookie
# middleware) and returns a BackendSession instance capable of managing the provided content during a given
# request (or creating a new session when needed).
#
SessionBackend = Callable[[Optional[str]], BackendSession]
