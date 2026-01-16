import time
import random
import functools
import requests
from typing import Any, Dict, Optional, Callable

def retry_with_jitter(max_tries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Decorator for retrying a function with exponential backoff and full jitter.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    
                    # Don't retry on certain client errors
                    if e.response is not None and e.response.status_code in [400, 401, 403, 404]:
                        raise e
                    
                    if attempt == max_tries - 1:
                        break
                    
                    # Exponential Backoff + Jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    sleep_time = random.uniform(0, delay)
                    
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
            
            raise last_exception
        return wrapper
    return decorator

def make_request(
    session: requests.Session,
    method: str,
    url: str,
    login_cb: Optional[Callable[[], None]] = None,
    timeout: int = 15,
    **kwargs
) -> Dict[str, Any]:
    """
    Functional helper to make HTTP requests with retry logic and auto-auth.
    """
    
    @retry_with_jitter(max_tries=3)
    def _do_execute_request():
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout
        return session.request(method=method, url=url, **kwargs)

    try:
        response = _do_execute_request()
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Handle Auth error
        if e.response is not None and e.response.status_code in [401, 403] and login_cb:
            print(f"Auth error ({e.response.status_code}). Calling login callback...")
            login_cb()
            # Retry once after login
            response = _do_execute_request()
            response.raise_for_status()
        else:
            raise e

    if response.status_code == 204:
        return {}
        
    return response.json()
