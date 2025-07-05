import logging
from functools import wraps
from typing import Any, Callable, Literal, Optional, Tuple, TypeAlias

LOG_LEVEL: TypeAlias = Literal['CRITICAL','ERROR','WARNING','INFO','DEBUG','NOTSET','DEFAULT']

def logwrap(
        before: Optional[Tuple[LOG_LEVEL, str]] | str = None,
        after: Optional[Tuple[LOG_LEVEL, str]] | str = None,
        show_args: Optional[LOG_LEVEL] = None
        ) -> Callable:
    """
    Simple dynamic decorator to log function calls. Uses the logging module with your current project configurations.
    Use LOG_LEVEL literal for using standard log levels. 
    **Warning**: Providing wrong log level won't raise any exception but will default to specified defaults with DEFAULT level.

    Args:
        before: Tuple of log level and message to log before function call or string with default of `DEBUG` level.
        after: Tuple of log level and message to log after function call or string with default of `INFO` level.
        show_args: Log level to use for logging function parameters before a call (eg. Args and kwargs) defaults to `DEBUG` level.

    Examples:
        >>> # Example with Custom Levels
        >>> @logwrap(before=('INFO', 'Function starting'), after=('INFO', 'Function ended'), show_args='DEBUG')
        >>> def my_func(my_arg, my_kwarg=None):
        >>>     ...
        >>> my_func('hello', my_kwarg=123) # calling the function
        Info - My Function is Starting
        Debug - Arguments: args=('hello',), kwargs={'my_kwarg': 123}
        Info - Function Ended
        >>> # Example with defaults.
        >>> @logwrap(before='Starting', after='Ended')
        >>> def my_new_func():
        >>>     ...
        >>> my_new_func()
        Debug - Starting
        Info - Ended
    """
    if isinstance(before, str):
        before = ('DEFAULT', before)

    if isinstance(after, str):
        after = ('DEFAULT', after)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            # Log before
            if before:
                level, message = before
                logger.log(getattr(logging, level, logging.DEBUG), message)

            # Log method parameters if requested
            if show_args:
                level = getattr(logging, show_args, logging.DEBUG)
                logger.log(level, f"Arguments: args={args}, kwargs={kwargs}")

            result = func(*args, **kwargs)

            # Log after
            if after:
                level, message = after
                logger.log(getattr(logging, level, logging.INFO), message)

            return result
        return wrapper
    return decorator

def return_exception_on_error(func: Callable) -> Callable:
    """Decorator to return an exception on error instead of raising it."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any|Exception:
        try: result = func(*args, **kwargs)
        except Exception as e: return e
        return result
    return wrapper

def return_true_on_error(func: Callable) -> Callable:
    """Decorator used to return True when an error occurs."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any|Literal[True]:
        try: result = func(*args, **kwargs)
        except: return True
        return result
    return wrapper

def return_false_on_error(func: Callable) -> Callable:
    """Decorator used to return False when an error occurs."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any|Literal[False]:
        try: result = func(*args, **kwargs)
        except: return False
        return result
    return wrapper