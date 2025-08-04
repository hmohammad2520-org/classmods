import logging, inspect
from functools import wraps
from typing import Any, Callable, Literal, Optional, ParamSpec, Tuple, TypeAlias, TypeVar, Union, overload

LOG_LEVEL: TypeAlias = Literal['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

def logwrap(
        before: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
        on_exception: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
        after: Optional[Tuple[LOG_LEVEL, str]] | str | bool = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A simple dynamic decorator to log function calls using the `logging` module with your current project configurations.
    Use the `LOG_LEVEL` literal to specify standard log levels.

    LOG_LEVEL = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

    - The messages are formatted dynamically using templating.
        - Available variables:
            - `func`: Function name
            - `args`: Tuple of positional arguments
            - `kwargs`: Dictionary of keyword arguments
            - `e`: Exception object (if any)
            - `result`: Return value of the function

    - If `True` is passed to an option, it will use the default log level and message:
        - Before: DEBUG - Calling {func} - args={args}, kwargs={kwargs}
        - After: INFO - Function {func} ended. result={result}
        - On Exception: ERROR - Error in {func}: {e}

    - **Warning**: If an option is set to a negative value, logging for that stage will be skipped.
    - **Warning**: If an invalid log level is provided, no exception will be raised. Instead, the decorator will fall back to the default log level.

    Args:
        before: A tuple of log level and message to log *before* the function call, or `True` to use the default.
        on_exception: A tuple of log level and message to log *on exception*, or `True` to use the default.
        after: A tuple of log level and message to log *after* the function call, or `True` to use the default.

    Examples:
    >>> @logwrap(before=('INFO', '{func} starting, args={args}, kwargs={kwargs}'), after=('INFO', '{func} ended'))
    ... def my_func(my_arg, my_kwarg=None):
    ...     ...
    ... my_func('hello', my_kwarg=123)
    Info - my_func starting, args={'my_arg', 123}, kwargs={'my_arg': 'hello','my_kwarg': 123}
    Info - my_func ended

    >>> @logwrap(before=True, after=True)
    ... def my_new_func():
    ...     ...
    ... my_new_func()
    Debug - Calling my_new_func - kwargs={}
    Info - Function my_new_func ended. result=None

    >>> @logwrap(on_exception=True)
    ... def error_func():
    ...     raise Exception('My exception msg')
    ... error_func()
    Error - Error in error_func: My exception msg
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
        if isinstance(option, bool) and option:
            return (default_level, default_msg)

        elif isinstance(option, str):
            return (default_level, option)

        elif isinstance(option, tuple):
            return option

    before = normalize('DEBUG', 'Calling {func} - kwargs={kwargs}', before)
    on_exception = normalize('ERROR', 'Error in {func}: {e}', on_exception)
    after = normalize('INFO', 'Function {func} ended. result={result}', after)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        logger = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            func_name = func.__name__
            unified_kwargs = dict(bound_args.arguments)

            fmt_context = {
                'func': func_name,
                'args': tuple(unified_kwargs.values()),
                'kwargs': unified_kwargs,
            }

            if before:
                level, msg = before
                logger.log(getattr(logging, level, logging.DEBUG), msg.format(**fmt_context))

            try:
                result = func(*args, **kwargs)
                fmt_context['result'] = result
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
