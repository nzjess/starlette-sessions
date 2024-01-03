# starlette-sessions

Adds server-side session support to your Starlette application

## License

[MIT License](LICENSE)

## Contributors

- Jesse McLaughlin <nzjess@gmail.com>

## Installing

```shell
# with redis support, for example

# from source
poetry install --extras redis
```

## Quick Start

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

from starlette_sessions.middleware import SessionMiddleware
from starlette_sessions.cookie.backend import CookieSessionBackend
from starlette_sessions.signedcookie.backend import SignedCookieSessionBackend
from starlette_sessions.memory.backend import MemorySessionBackend
from starlette_sessions.redis.backend import RedisSessionBackend


async def homepage(request: Request):
    return JSONResponse({"hello": "world"})


async def session_set(request: Request):
    counter = request.session.get("counter")
    response = JSONResponse({"counter": counter})
    request.session["counter"] = (counter or 0) + 1
    return response


async def session_read(request: Request):
    return JSONResponse(
        {k: v for k, v in request.session.items()}
    )


async def session_clear(request: Request):
    counter = request.session.get("counter")
    response = JSONResponse({"counter": counter})
    request.session.clear()
    return response


async def session_unsafe(request: Request):
    try:
        counter = request.session["counter"]
    except KeyError:
        counter = None
    return JSONResponse({"counter": counter})


#
# try out these backends:
#
session_backend = CookieSessionBackend()
# session_backend = SignedCookieSessionBackend(secret_key="s3cr3t", max_age=30)
# session_backend = MemorySessionBackend()
# session_backend = RedisSessionBackend(ttl=30)


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/set", session_set),
        Route("/read", session_read),
        Route("/clear", session_clear),
        Route("/unsafe", session_unsafe),
    ],
    middleware=[
        Middleware(SessionMiddleware, backend=session_backend),
    ]
)

uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Development
```shell
# setup
poetry install --with dev --all-extras

# linting
poetry run ruff src tests

# formatting
poetry run black src tests
poetry run isort src tests

# type checking
poetry run mypy src tests

# testing
poetry run pytest -s tests/unit
```
