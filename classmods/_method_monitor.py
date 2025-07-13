from typing import Any, Dict, List, Tuple, Type, Callable
from functools import wraps

class MethodMonitor:
    # Dictionary to store monitors for each (class, method) pair
    monitors_registery: Dict[Tuple[Type, str], List['MethodMonitor']] = {}

    def __init__(
            self, 
            target: Type, 
            callable: Callable[..., None],
            monitor_args: tuple = (),
            monitor_kwargs: dict = {},
            *,
            target_method: str = '__init__',
            active: bool = True,
    ) -> None:
        """
        A class to monitor method calls of a target class, triggering a handler function after the method is called.

        The MethodMonitor wraps a target method of a class and executes a monitor handler whenever the method is invoked.
        Multiple monitors can be registered for the same (class, method) pair, and all active monitors will be triggered
        sequentially after the original method call.

        Args:
            target (Type): The target class whose method will be monitored.
            callable (MonitorCallable): A callable to execute when the target method is called. -
                Signature: monitor_callable(instance: object, *monitor_args, **monitor_kwargs). -
                **warning**: sends `None` as the first arg to `MonitorCallable` if target method is `StaticMethod` !!
            monitor_args (tuple): Positional arguments to pass to `callable` (default: empty tuple).
            monitor_kwargs (dict): Keyword arguments to pass to `callable` (default: empty dict).
            target_method (str): Name of the method to monitor (default: '__init__').
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
        self._monitor_callable = callable
        self._monitor_args = monitor_args
        self._monitor_kwargs = monitor_kwargs
        self._target_method = target_method
        self._active = active

        # Add this Monitor to the list of Monitors for each (class, method)
        key = self._create_registery_key()
        if key not in self.monitors_registery:
            self.monitors_registery[key] = []
            self._wrap_class_method(target, self._target_method)

        self.monitors_registery[key].append(self)


    def _create_registery_key(self) -> Tuple[Type, str]:
        return (self._target, self._target_method)

    def _create_original_name(self, method_name: str) -> str:
        return f'__original_{method_name}'

    @staticmethod
    def _is_static_method(method: staticmethod|classmethod|Callable[[Any] ,Any]) -> bool:
        return isinstance(method, (staticmethod, classmethod))

    def _wrap_class_method(self, target: Type, method_name: str) -> None:
        """Wrap the target method to call all Monitors."""
        original_name = self._create_original_name(method_name)

        if not hasattr(target, method_name):
            raise ValueError(f"The target class {target.__name__} does not have a method '{method_name}'.")

        # Save the original method if not already saved
        if not hasattr(target, original_name):
            setattr(target, original_name, getattr(target, method_name))

        original_method = getattr(target, original_name)

        @wraps(original_method)
        def new_method(*args, **kwargs) -> Any:
            output = original_method(*args, **kwargs)

            key = self._create_registery_key()
            for monitor in MethodMonitor.monitors_registery.get(key, []):
                if monitor.is_active():
                    monitor._monitor_callable(
                        args[0] if self._is_static_method(original_method) else None,
                        *monitor._monitor_args, 
                        **monitor._monitor_kwargs,
                    )

            return output

        setattr(target, method_name, new_method)


    def activate(self) -> None:
        """Activate the monitor."""
        self._active = True

    def deactivate(self) -> None:
        """Deactivate the monitor."""
        self._active = False

    def remove(self) -> None:
        """Remove the handler and restore the original method if no monitors are left."""
        key = self._create_registery_key()
        if key in self.monitors_registery:
            self.monitors_registery[key].remove(self)
            if not self.monitors_registery[key]:
                # Restore the original method
                original_name = self._create_original_name(self._target_method)
                if hasattr(self._target, original_name):
                    setattr(self._target, self._target_method, getattr(self._target, original_name))
                    delattr(self._target, original_name)

                del self.monitors_registery[key]


    def is_active(self) -> bool:
        return bool(self._active)

    def __bool__(self) -> bool:
        return self.is_active()

    def __str__(self) -> str:
        return f'<MethodMonitor of: {self._target} (method={self._target_method})>'

    def __repr__(self) -> str:
        return f'MethodMonitor({self._target}, {self._monitor_callable}, target_method={self._target_method}, monitor_args={self._monitor_args}, monitor_kwargs={self._monitor_kwargs})'

    def __del__(self) -> None:
        self.remove()
