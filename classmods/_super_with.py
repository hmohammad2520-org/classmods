from contextlib import ExitStack, AsyncExitStack
from typing import Any, Tuple, TypeVar, Union, cast
from contextlib import AbstractContextManager, AbstractAsyncContextManager

T = TypeVar("T")

# Type hint for multiple sync contexts
SyncCtx = AbstractContextManager[T]

# Type hint for multiple async contexts
AsyncCtx = AbstractAsyncContextManager[T]


class SuperWith:
    """
    The 'CEO' of context managers: combine multiple context managers into a single `with` or `async with`.
    Supports unpacking of returned values.

    Example (sync):
        with SuperWith(Connection(), Session(), Lock()) as (conn, sess, lock):
            do_work(conn, sess, lock)

    Example (async):
        async with SuperWith(AsyncConnection(), AsyncSession()) as (conn, sess):
            await do_work(conn, sess)
    """
    def __init__(self, *contexts: Union[SyncCtx[Any], AsyncCtx[Any]]):
        """
        Initialize the SuperWith context manager.

        Args:
            *contexts: Any number of context managers (sync or async) to be managed together.
                - Sync contexts must implement `__enter__` and `__exit__`
                - Async contexts must implement `__aenter__` and `__aexit__`

        Notes:
            - Sync and async contexts are **mutually exclusive**; use either `with` or `async with`.
            - Zero contexts are allowed; in that case, `__enter__` / `__aenter__` returns an empty tuple `()`.
            - One context returns the object itself for convenient unpacking.
            - Multiple contexts return a tuple of all entered objects, in the order passed.
            - Contexts are entered in the order provided and exited in **reverse order**, following Python context manager conventions.
        """
        self._contexts = contexts
        self._sync_stack = ExitStack()
        self._async_stack = AsyncExitStack()
        self._entered = None

    def __enter__(self) -> Tuple[Any]:
        # Ensure all contexts support __enter__/__exit__
        for ctx in self._contexts:
            if not hasattr(ctx, "__enter__") or not hasattr(ctx, "__exit__"):
                raise TypeError(
                    f"Sync 'with' requires all contexts to implement __enter__/__exit__, but {ctx} does not"
                )

        self._entered = tuple(self._sync_stack.enter_context(cast(AbstractContextManager[Any], ctx)) for ctx in self._contexts)
        return self._entered[0] if len(self._entered) == 1 else self._entered

    def __exit__(self, exc_type, exc_value, traceback) -> bool | None:
        return self._sync_stack.__exit__(exc_type, exc_value, traceback)


    async def __aenter__(self) -> Tuple[Any]:
        # Ensure all contexts support __aenter__/__aexit__
        for ctx in self._contexts:
            if not hasattr(ctx, "__aenter__") or not hasattr(ctx, "__aexit__"):
                raise TypeError(
                    f"Async 'with' requires all contexts to implement __aenter__/__aexit__, but {ctx} does not"
                )

        self._entered = tuple([await self._async_stack.enter_async_context(cast(AbstractAsyncContextManager[Any], ctx)) for ctx in self._contexts])
        return self._entered[0] if len(self._entered) == 1 else self._entered

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool | None:
        return await self._async_stack.__aexit__(exc_type, exc_value, traceback)
