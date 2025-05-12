import logging
from functools import wraps
from typing import Callable, Literal, Optional, Tuple, TypeAlias

LOG_LEVEL: TypeAlias = Literal['CRITICAL','ERROR','WARNING','INFO','DEBUG','NOTSET']

def logwrap(
        before: Optional[Tuple[LOG_LEVEL, str]] = None,
        after: Optional[Tuple[LOG_LEVEL, str]] = None,
        log_parms: Optional[LOG_LEVEL] = None
        ) -> Callable:
    """
    Decorator to log function calls and returns.

    Args:
        before: Tuple of log level and message to log before function call.
        after: Tuple of log level and message to log after function call.
        log_parms: Log level to use for logging function parameters.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            # Log before
            if before:
                level, message = before
                logger.log(getattr(logging, level.upper(), logging.DEBUG), message)

            # Log method parameters if requested
            if log_parms:
                level = getattr(logging, log_parms.upper(), logging.DEBUG)
                logger.log(level, f"Arguments: args={args}, kwargs={kwargs}")

            result = func(*args, **kwargs)

            # Log after
            if after:
                level, message = after
                logger.log(getattr(logging, level.upper(), logging.INFO), message)

            return result
        return wrapper
    return decorator
