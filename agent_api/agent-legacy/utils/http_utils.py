import asyncio
import functools
import random
from typing import Any, Callable, Coroutine, Dict, Optional

import httpx


def retry_with_jitter(
    max_tries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0
):
    """Decorator for retrying an async function with exponential backoff and full jitter."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
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

                    print(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."
                    )
                    await asyncio.sleep(sleep_time)
                except httpx.RequestError as e:
                    last_exception = e

                    if attempt == max_tries - 1:
                        break

                    delay = min(base_delay * (2**attempt), max_delay)
                    sleep_time = random.uniform(0, delay)

                    print(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."
                    )
                    await asyncio.sleep(sleep_time)

            raise last_exception

        return wrapper

    return decorator


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    login_cb: Optional[Callable[[], Coroutine]] = None,
    timeout: int = 15,
    **kwargs,
) -> Dict[str, Any]:
    """Functional helper to make async HTTP requests with retry logic and auto-auth."""

    @retry_with_jitter(max_tries=3)
    async def _do_execute_request():
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
            print(f"Auth error ({e.response.status_code}). Calling login callback...")
            await login_cb()
            # Retry once after login
            response = await _do_execute_request()
        else:
            raise e

    if response.status_code == 204:
        return {}

    return response.json()
