import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, cast

import httpx

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def retry_with_jitter(
    max_tries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for retrying an async function with exponential backoff and full jitter."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: httpx.HTTPStatusError | httpx.RequestError | None = None
            for attempt in range(max_tries):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e

                    # Don't retry on certain client errors
                    if e.response.status_code in [400, 401, 403, 404]:
                        raise e

                    if attempt == max_tries - 1:
                        break

                    # Exponential Backoff + Jitter
                    delay = min(base_delay * (2**attempt), max_delay)
                    sleep_time = random.uniform(0, delay)

                    logger.debug(
                        "Attempt %d failed: %s. Retrying in %.2fs...",
                        attempt + 1,
                        e,
                        sleep_time,
                    )
                    await asyncio.sleep(sleep_time)
                except httpx.RequestError as e:
                    last_exception = e

                    if attempt == max_tries - 1:
                        break

                    delay = min(base_delay * (2**attempt), max_delay)
                    sleep_time = random.uniform(0, delay)

                    logger.debug(
                        "Attempt %d failed: %s. Retrying in %.2fs...",
                        attempt + 1,
                        e,
                        sleep_time,
                    )
                    await asyncio.sleep(sleep_time)
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    login_cb: Callable[[], Awaitable[dict[str, str]]] | None = None,
    timeout: int = 15,
    **kwargs: Any,
) -> dict[str, Any]:
    """Functional helper to make async HTTP requests with retry logic and auto-auth."""

    @retry_with_jitter(max_tries=3)
    async def _do_execute_request() -> httpx.Response:
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout
        response = await client.request(method=method, url=url, **kwargs)
        response.raise_for_status()
        return response

    try:
        response = await _do_execute_request()
    except httpx.HTTPStatusError as e:
        # Handle Auth error
        if e.response.status_code in [401, 403] and login_cb:
            logger.debug(
                "Auth error (%d). Calling login callback...", e.response.status_code
            )

            # An auth callback return new headers
            new_headers = await login_cb()
            if new_headers:
                kwargs.setdefault("headers", {}).update(new_headers)

            # Retry once after login
            response = await _do_execute_request()
        else:
            raise e

    if response.status_code == 204:
        return {}

    return cast(dict[str, Any], response.json())
