from contextlib import contextmanager
import time, logging, inspect
from functools import wraps
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    ParamSpec,
    Tuple,
    Dict,
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
Predicate: TypeAlias = Callable[[Dict[str, Any]], bool]

LogwrapStage: TypeAlias = Union[
    Tuple[LogLevelLike, str],
    Tuple[LogLevelLike, str, Predicate],
    str,
    bool,
    None,
]
NormalizedStage: TypeAlias = Optional[
    Tuple[int, str, Optional[Predicate]]
]

def logwrap(
        before: LogwrapStage = None,
        on_exception: LogwrapStage = None,
        after: LogwrapStage = None,
        *,
        logger: LoggerLike = None,
        timing: LogwrapStage = None,
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
            - `duration`: Time duration of the called function. (time.perf_counter)


    Warnings:
        - If an option is set to a negative value (e.g. `False`, `None`), logging for that
        stage is skipped.
        - If an invalid log level is provided, no exception is raised. The decorator
        safely falls back to the default log level.
        - High usage of `timing` can impact performance.
        
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
            stage: LogwrapStage,
        ) -> NormalizedStage:
        """
        Normalize the options to specified args and make the input to `Tuple[LOG_LEVEL, str] | None`.
        Returns None on negative inputs eg.(false, None).
        """
        if stage is None or stage is False:
            return

        if isinstance(stage, bool) and stage:
            return (default_level, default_msg, None)

        if isinstance(stage, str):
            return (default_level, stage, None)

        if isinstance(stage, tuple):
            if len(stage) == 2:
                level, msg = stage
                predicate = None

            elif len(stage) == 3:
                level, msg, predicate = stage

            else:
                raise IndexError(
                    f"logwrap tuple must have length 2 or 3, got {len(stage)}"
                )

            if isinstance(level, str):
                level = getattr(logging, level, default_level)

            if not isinstance(level, int) or not isinstance(msg, str):
                return None

            return level, msg, predicate

    def build_context(
            func: Callable,
            sig: inspect.Signature,
            args: Tuple,
            kwargs: Dict[str, Any],
        ) -> Dict[str, Any]:
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        return {
            'func': func.__name__,
            'args': tuple(bound.arguments.values()),
            'kwargs': dict(bound.arguments),
        }

    def log_stage(
            stage: NormalizedStage,
            log_obj: logging.Logger,
            context: Dict[str, Any],
        ) -> None:
        if stage:
            level, msg, predicate = stage
            if predicate is None or predicate(context):
                log_obj.log(level, msg.format(**context))


    nrml_before = normalize(logging.DEBUG, 'Calling {func} - kwargs={kwargs}', before)
    nrml_on_exception = normalize(logging.ERROR, 'Error in {func}: {e}', on_exception)
    nrml_after = normalize(logging.INFO, 'Function {func} ended. result={result}', after)
    nrml_timing = normalize(logging.DEBUG, 'Function {func} executed in {duration:.6f}s', timing)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        if logger is None:
            log_obj = logging.getLogger(func.__module__)

        elif isinstance(logger, logging.Logger):
            log_obj = logger

        elif isinstance(logger, str):
            log_obj = logging.getLogger(logger)

        else:
            raise TypeError(f'Logger object must be `None` or `str` or `Logger` not `{logger.__class__}`')

        @contextmanager
        def wrapper_context(args, kwargs):
            fmt_context = build_context(func, sig, args, kwargs)
            log_stage(nrml_before, log_obj, fmt_context)
            start = time.perf_counter() if nrml_timing else None

            try:
                yield fmt_context

            except Exception as e:
                fmt_context['e'] = e
                log_stage(nrml_on_exception, log_obj, fmt_context)
                raise

            else:
                log_stage(nrml_after, log_obj, fmt_context)

            finally:
                if start is not None:
                    fmt_context['duration'] = time.perf_counter() - start
                    log_stage(nrml_timing, log_obj, fmt_context)


        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with wrapper_context(args, kwargs) as fmt_context:
                fmt_context['result'] = await func(*args, **kwargs)  #type: ignore
                return fmt_context['result']


        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with wrapper_context(args, kwargs) as fmt_context:
                fmt_context['result'] = func(*args, **kwargs)
                return fmt_context['result']

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper  #type: ignore
    return decorator

@overload
def suppress_errors(fallback: type[Exception]) -> Callable[[Callable[..., R]], Callable[..., Union[R, Exception]]]: ...
@overload
def suppress_errors(fallback: T) -> Callable[[Callable[..., R]], Callable[..., Union[R, T]]]: ...
def suppress_errors(fallback: Any) -> Callable[[Callable[..., R]], Callable[..., Union[R, Any]]]:
    """
    A decorator that suppresses exceptions raised by the wrapped function and returns
    a fallback value instead.

    Supports async functions or methods.

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
        def sync_wrapper(*args: Any, **kwargs: Any) -> Union[R, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if fallback is Exception:
                    return e
                return fallback

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Union[R, Any]:
            try:
                return await func(*args, **kwargs)  #type: ignore
            except Exception as e:
                if fallback is Exception:
                    return e
                return fallback

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    return decorator
