import logging, inspect
from functools import wraps
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    ParamSpec,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)

LOG_LEVEL: TypeAlias = Literal[
    'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'
]

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

LogLevelLike: TypeAlias = Union[int, LOG_LEVEL]
LoggerLike: TypeAlias = Union[str, logging.Logger, None]
Predicate: TypeAlias = Callable[[dict[str, Any]], bool]

LogwrapParameter: TypeAlias = Union[
    Tuple[LogLevelLike, str],
    Tuple[LogLevelLike, str, Predicate],
    str,
    bool,
    None,
]
NormalizedParameter: TypeAlias = Optional[
    Tuple[int, str, Optional[Predicate]]
]

def logwrap(
        before: LogwrapParameter = None,
        on_exception: LogwrapParameter = None,
        after: LogwrapParameter = None,
        *,
        logger: LoggerLike = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A simple dynamic decorator to log function calls using the standard `logging` module
    and your project’s existing logging configuration.

    Use the `LOG_LEVEL` literal or integer log levels to specify standard logging severity.

    LOG_LEVEL = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

    Features:
        - Supports integer log levels (e.g. `logging.DEBUG`)
        - Custom logger selection
        - Async function support
        - Conditional logging via predicates

    Message Formatting:
        Log messages are dynamically formatted using string templates.

        Available template variables:
            - `func`: Function name
            - `args`: Tuple of positional arguments
            - `kwargs`: Dictionary of keyword arguments
            - `e`: Exception object (on exception only)
            - `result`: Return value (after execution only)

    Default Behavior:
        If `True` is passed to an option, the following defaults are used:

            - Before: DEBUG - Calling {func} - kwargs={kwargs}
            - After: INFO - Function {func} ended. result={result}
            - On Exception: ERROR - Error in {func}: {e}

    Warnings:
        - If an option is set to a negative value (e.g. `False`, `None`), logging for that
        stage is skipped.
        - If an invalid log level is provided, no exception is raised. The decorator
        safely falls back to the default log level.

    Parameters:
        before:
            A tuple of `(level, message)` or `(level, message, predicate)` to log
            *before* function execution, or `True` to use the default behavior.

        on_exception:
            A tuple of `(level, message)` or `(level, message, predicate)` to log
            *when an exception occurs*, or `True` to use the default behavior.

        after:
            A tuple of `(level, message)` or `(level, message, predicate)` to log
            *after* successful function execution, or `True` to use the default behavior.

    For usage examples, advanced configuration, and best practices, see:
        https://github.com/hmohammad2520-org/classmods/docs/logwrap.md
    """
    def normalize(
            default_level: int,
            default_msg: str,
            option: LogwrapParameter,
        ) -> NormalizedParameter:
        """
        Normalize the options to specified args and make the input to `Tuple[LOG_LEVEL, str] | None`.
        Returns None on negative inputs eg.(false, None).
        """
        if option is None or option is False:
            return

        if isinstance(option, bool) and option:
            return (default_level, default_msg, None)

        if isinstance(option, str):
            return (default_level, option, None)

        if isinstance(option, tuple):
            if len(option) == 2:
                level, msg = option
                predicate = None

            elif len(option) == 3:
                level, msg, predicate = option

            else:
                raise IndexError(
                    f"logwrap tuple must have length 2 or 3, got {len(option)}"
                )

            if isinstance(level, str):
                level = getattr(logging, level, default_level)

            if not isinstance(level, int) or not isinstance(msg, str):
                return None

            return level, msg, predicate

    ## n means normalized
    before_n = normalize(logging.DEBUG, 'Calling {func} - kwargs={kwargs}', before)
    on_exception_n = normalize(logging.ERROR, 'Error in {func}: {e}', on_exception)
    after_n = normalize(logging.INFO, 'Function {func} ended. result={result}', after)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        is_async = inspect.iscoroutinefunction(func)

        if logger is None:
            log_obj = logging.getLogger(func.__module__)

        elif isinstance(logger, logging.Logger):
            log_obj = logger

        elif isinstance(logger, str):
            log_obj = logging.getLogger(logger)

        else:
            raise TypeError(f'Logger object must be `None` or `str` or `Logger` not `{logger.__class__}`')

        def build_context(args, kwargs) -> dict[str, Any]:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            return {
                'func': func.__name__,
                'args': tuple(bound.arguments.values()),
                'kwargs': dict(bound.arguments),
            }

        if is_async:
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                fmt_context = build_context(args, kwargs)

                if before_n:
                    level, msg, predicate = before_n
                    if predicate is None or predicate(fmt_context):
                        log_obj.log(level, msg.format(**fmt_context))

                try:
                    result = await func(*args, **kwargs)
                    fmt_context['result'] = result
                except Exception as e:
                    if on_exception_n:
                        level, msg, predicate = on_exception_n
                        fmt_context['e'] = e
                        if predicate is None or predicate(fmt_context):
                            log_obj.log(level, msg.format(**fmt_context))
                    raise

                if after_n:
                    level, msg, predicate = after_n
                    if predicate is None or predicate(fmt_context):
                        log_obj.log(level, msg.format(**fmt_context))

                return result
            return async_wrapper  # type: ignore

        else:
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                fmt_context = build_context(args, kwargs)

                if before_n:
                    level, msg, predicate = before_n
                    if predicate is None or predicate(fmt_context):
                        log_obj.log(level, msg.format(**fmt_context))

                try:
                    result = func(*args, **kwargs)
                    fmt_context['result'] = result
                except Exception as e:
                    if on_exception_n:
                        level, msg, predicate = on_exception_n
                        fmt_context['e'] = e
                        if predicate is None or predicate(fmt_context):
                            log_obj.log(level, msg.format(**fmt_context))
                    raise

                if after_n:
                    level, msg, predicate = after_n
                    if predicate is None or predicate(fmt_context):
                        log_obj.log(level, msg.format(**fmt_context))

                return result
            return sync_wrapper
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
