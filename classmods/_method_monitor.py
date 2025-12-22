from typing import Any, Dict, List, Tuple, Type, Callable, Optional
from functools import wraps
import inspect

class MethodMonitor:
    """
    Monitor calls to a specific method on a class.

    Multiple monitors may be attached to the same (class, method) pair.
    All active monitors are executed AFTER the original method call.
    """

    _registry: Dict[Tuple[Type, str], List["MethodMonitor"]] = {}

    def __init__(
            self,
            target: Type,
            monitor_callable: Callable[..., None],
            monitor_args: Optional[Tuple] = None,
            monitor_kwargs: Optional[Dict[str, Any]] = None,
            *,
            target_method: str | Callable = "__init__",
            active: bool = True,
        ) -> None:
        """
        A class to monitor method calls of a target class, triggering a handler function after the method is called.

        The MethodMonitor wraps a target method of a class and executes a monitor handler whenever the method is invoked.
        Multiple monitors can be registered for the same (class, method) pair, and all active monitors will be triggered
        sequentially after the original method call.

        Args:
            target (Type): The target class whose method will be monitored.
            monitor_callable (MonitorCallable): A callable to execute when the target method is called. -
                Signature: monitor_callable(instance: object, *monitor_args, **monitor_kwargs). -
                **warning**: sends `None` as the first arg to `MonitorCallable` if target method is `StaticMethod` !!
            monitor_args (Optional[Tuple]): Positional arguments to pass to `callable` (default: empty tuple).
            monitor_kwargs (Optional[Dict[str, Any]]): Keyword arguments to pass to `callable` (default: empty dict).
            target_method (str | Callable): Name of the method to monitor or the method itself (default: '__init__').
            active (bool): Whether the monitor active initially (default: True).

        Example:
            >>> class MyClass:
            ...     def my_method(self):
            ...         pass
            >>> def my_handler(instance):
            ...     print(f"Monitor triggered on {instance}")
            >>> monitor = MethodMonitor(MyClass, my_handler, target_method='my_method')
            >>> obj = MyClass()
            >>> obj.my_method()  # Also calls `my_handler(obj)`
        """
        self._target = target
        self._monitor_callable = monitor_callable
        self._monitor_args = monitor_args or ()
        self._monitor_kwargs = monitor_kwargs or {}
        self._target_method = target_method if isinstance(target_method, str) else target_method.__name__
        self._active = active

        key = (self._target, self._target_method)

        if key not in self._registry:
            self._wrap_method()
            self._registry[key] = []

        self._registry[key].append(self)

    @staticmethod
    def _get_method_type(target_class, method_name) -> str:
        """Return 'instance', 'class', or 'static'."""
        for cls in target_class.__mro__:
            if method_name in cls.__dict__:
                attr = cls.__dict__[method_name]
                if isinstance(attr, staticmethod):
                    return "static"
                elif isinstance(attr, classmethod):
                    return "class"
                else:
                    return "instance"
        return "instance"

    def _wrap_method(self) -> None:
        if not hasattr(self._target, self._target_method):
            raise AttributeError(
                f"{self._target.__name__} has no method '{self._target_method}'"
            )

        # Get the original descriptor
        original_attr = None
        for cls in self._target.__mro__:
            if self._target_method in cls.__dict__:
                original_attr = cls.__dict__[self._target_method]
                break

        if original_attr is None:
            raise AttributeError(f"Cannot find method {self._target_method}")

        method_type = self._get_method_type(self._target, self._target_method)

        # Extract the original function for wrapping
        if isinstance(original_attr, (staticmethod, classmethod)):
            original_func = original_attr.__func__
        else:
            original_func = original_attr

        @wraps(original_func)
        def wrapper(*args, **kwargs):
            result = original_func(*args, **kwargs)

            for monitor in self._registry.get((self._target, self._target_method), []):
                if not monitor._active:
                    continue

                if method_type == "static":
                    first_arg = None
                else:
                    first_arg = args[0]

                monitor._monitor_callable(
                    first_arg, *monitor._monitor_args, **monitor._monitor_kwargs
                )

            return result

        # Reapply descriptor to preserve type
        if method_type == "static":
            wrapped = staticmethod(wrapper)
        elif method_type == "class":
            wrapped = classmethod(wrapper)
        else:
            wrapped = wrapper

        # Store reference to original for unwrapping
        wrapped.__methodmonitor_original__ = original_func  # type: ignore[attr-defined]
        wrapped.__methodmonitor_wrapped__ = True  # type: ignore[attr-defined]

        setattr(self._target, self._target_method, wrapped)

    def activate(self) -> None:
        """Activate the monitor."""
        self._active = True

    def deactivate(self) -> None:
        """Deactivate the monitor."""
        self._active = False

    def remove(self) -> None:
        """Remove the monitor and restore original method if no monitors left."""
        key = (self._target, self._target_method)
        monitors = self._registry.get(key)
        if not monitors:
            return

        if self in monitors:
            monitors.remove(self)

        if not monitors:
            wrapped = getattr(self._target, self._target_method)
            original = getattr(wrapped, "__methodmonitor_original__", None)
            if original:
                # Reapply original descriptor type
                method_type = self._get_method_type(self._target, self._target_method)
                if method_type == "static":
                    original = staticmethod(original)
                elif method_type == "class":
                    original = classmethod(original)
                setattr(self._target, self._target_method, original)

            del self._registry[key]

    def is_active(self) -> bool:
        return self._active

    def __bool__(self) -> bool:
        return self._active

    def __repr__(self) -> str:
        return (
            f"MethodMonitor("
            f"target={self._target.__name__}, "
            f"method={self._target_method}, "
            f"active={self._active})"
        )
