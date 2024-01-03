from typing import Literal

from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starlette_sessions.backend import BackendSession, SessionBackend


class SessionMiddleware:
    """
    Middleware implementation that mediates between a provided session backend implementation and the cookie value.
    """

    def __init__(
        self,
        app: ASGIApp,
        backend: SessionBackend,
        cookie_name: str = "session",
        path: str = "/",
        same_site: Literal["lax", "strict", "none"] = "lax",
        https_only: bool = False,
    ) -> None:
        self.app = app
        self.backend = backend
        self.cookie_name = cookie_name
        self.path = path
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        cookie_value = connection.cookies.get(self.cookie_name)
        scope["session"] = self.backend(cookie_value)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                session: BackendSession = scope["session"]
                if session.accessed:
                    cookie_content = session.content
                    max_age = session.max_age if cookie_content is not None else 0
                    headers = MutableHeaders(scope=message)
                    cookie = "{cookie_name}={cookie_content}; path={path}; {max_age}{security_flags}".format(
                        cookie_name=self.cookie_name,
                        cookie_content=cookie_content,
                        path=self.path,
                        max_age=f"Max-Age={max_age}; " if max_age is not None else "",
                        security_flags=self.security_flags,
                    )
                    headers.append("Set-Cookie", cookie)
            await send(message)

        await self.app(scope, receive, send_wrapper)
