import logging
from functools import wraps
from typing import Any, Callable, Literal, Optional, ParamSpec, Tuple, Type, TypeAlias, TypeVar, Union, overload

LOG_LEVEL: TypeAlias = Literal['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET', 'DEFAULT']

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

def logwrap(
        before: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
        on_exception: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
        after: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Simple dynamic decorator to log function calls. Uses the logging module with your current project configurations.
    Use LOG_LEVEL literal for using standard log levels.
    The messages will get formated in proccess so you can use templating for better logging.

    (`func`: Function Name, `args`: Arguments Tuple, `kwargs`: Keyword Arguments Dict, `e`: The Exception if Exists)

    Passing bool will use default levels and messages.(
    Before: 'DEBUG - Calling {func} - args:{args}, kwargs:{kwargs}'
    After: 'INFO - Function {func} ended'
    On Exception: 'ERROR - Error on {func}: {e}')

    **Warning**: If options are negative, it will not log the option.
    **Warning**: Providing wrong log level won't raise any exception but will default to specified defaults with DEFAULT level.

    Args:
        before: Tuple of log level and message to log before function call or string with default of `DEBUG` level.
        on_exception: Tuple of log level and message to log exception of function call or string with default of `ERROR` level.
        after: Tuple of log level and message to log after function call or string with default of `INFO` level.

    Examples:
    >>> @logwrap(before=('INFO', '{func} starting, args={args} kwargs={kwargs}'), after=('INFO', '{func} ended'))
    ... def my_func(my_arg, my_kwarg=None):
    ...     ...
    ... my_func('hello', my_kwarg=123)
    Info - my_func Starting, args=('hello',), kwargs={'my_kwarg': 123}
    Info - my_func Ended

    >>> @logwrap(before=True, after=True)
    ... def my_new_func():
    ...     ...
    ... my_new_func()
    Debug - Calling my_new_func - args:(), kwargs:{}
    Info - Function my_new_func ended

    >>> @logwrap(on_exception=True)
    ... def error_func():
    ...     raise Exception('My exception msg')
    ... error_func()
    Error - Error on error_func: My exception msg
    """
    def normalize(
            default_level: LOG_LEVEL,
            default_msg: str,
            option: Optional[Tuple[LOG_LEVEL, str]] | str | bool | None,
        ) -> Tuple[LOG_LEVEL, str] | None:
        """
        Normalize the options to specified args and make the input to `Tuple[LOG_LEVEL, str] | None`.
        Returns None on negative inputs.

        Args:
            default_level(LOG_LEVEL): default level on str, bool inputs
            default_msg(str): default msg on bool inputs
            option(Optional[Tuple[LOG_LEVEL, str]] | str | bool | None): The option to normalize
        
        Returns:
            (Tuple[LOG_LEVEL, str] | None): Normalized output for logging wraper
        """
        if isinstance(option, bool) and option is True:
            return (default_level, default_msg)

        elif isinstance(option, str):
            return (default_level, option)

        elif isinstance(option, tuple):
            return option

        elif not option or option is None:
            return None

    before = normalize('DEBUG', 'Calling {func} - args:{args}, kwargs:{kwargs}', before)
    after = normalize('INFO', 'Function {func} ended', after)
    on_exception = normalize('ERROR', 'Error on {func}: {e}', on_exception)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger = logging.getLogger(func.__module__)
            func_name = func.__name__

            fmt_context = {
                'func': func_name,
                'args': args,
                'kwargs': kwargs,
            }

            if before:
                level, msg = before
                logger.log(getattr(logging, level, logging.DEBUG), msg.format(**fmt_context))

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if on_exception:
                    level, msg = on_exception
                    fmt_context['e'] = e
                    logger.log(getattr(logging, level, logging.ERROR), msg.format(**fmt_context))
                raise e

            if after:
                level, msg = after
                logger.log(getattr(logging, level, logging.INFO), msg.format(**fmt_context))

            return result
        return wrapper
    return decorator


@overload
def suppress_errors(fallback: type[Exception]) -> Callable[[Callable[..., R]], Callable[..., Union[R, Exception]]]: ...
@overload
def suppress_errors(fallback: T) -> Callable[[Callable[..., R]], Callable[..., Union[R, T]]]: ...

def suppress_errors(fallback: Any) -> Callable[[Callable[..., R]], Callable[..., Union[R, Any]]]:
    """
    A decorator that suppresses exceptions raised by the wrapped function and returns
    a fallback value instead.

    Parameters:
        fallback: Determines what to return when an exception is caught.
            - Exception class (like Exception): Returns the caught exception object
            - Any other value: Returns that value when exception occurs

    Returns:
        Callable: A decorated version of the original function that returns either:
                  - The original return value, or
                  - The fallback value/exception

    Example:
    >>> @suppress_errors(Exception)
    ... def risky_op() -> int:
    ...     return 1 / 0
    >>> result = risky_op()  # Returns ZeroDivisionError

    >>> @suppress_errors(False)
    ... def safe_op() -> bool:
    ...     raise ValueError("error")
    >>> result = safe_op()  # Returns False

    Notes:
        - Only standard Python exceptions (derived from `Exception`) are caught.
        - Does not suppress `KeyboardInterrupt`, `SystemExit`, or `GeneratorExit`.
        - The decorator preserves the original function's metadata (name, docstring, etc.).
    """
    def decorator(func: Callable[..., R]) -> Callable[..., Union[R, Any]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[R, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if fallback is Exception:
                    return e
                return fallback
        return wrapper
    return decorator