from functools import wraps
import inspect

def handle_tool_error(func):
    """Decorator to catch exceptions in tools and return a formatted error message to the LLM."""
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return f"Error executing tool {func.__name__}: {str(e)}\n\nIMPORTANT: Do not blindly retry the tool with the same input. If the error persists, ask the user for clarification."
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return f"Error executing tool {func.__name__}: {str(e)}\n\nIMPORTANT: Do not blindly retry the tool with the same input. If the error persists, ask the user for clarification."
        return sync_wrapper
