from typing import Any, Dict, List, Tuple, Type, Callable
from functools import wraps

SpyCallable = Callable[..., None]

class MethodSpy:
    # Dictionary to store spies for each (class, method) pair
    spies_registery: Dict[Tuple[Type, str], List['MethodSpy']] = {}

    def __init__(
            self, 
            target: Type, 
            spy_callable: SpyCallable,
            spy_args: tuple = (),
            spy_kwargs: dict = {},
            *,
            target_method: str = '__init__',
            active: bool = True,
    ) -> None:
        """
        A class to spy on method calls of a target class, triggering a handler function after the method is called.

        The MethodSpy wraps a target method of a class and executes a spy handler whenever the method is invoked.
        Multiple spies can be registered for the same (class, method) pair, and all active spies will be triggered
        sequentially after the original method call.

        Args:
            target (Type): The target class whose method will be spied on.
            spy_callable (SpyCallable): A callable to execute when the target method is called.
                Signature: spy_callable(instance: object, *spy_args, **spy_kwargs).
            spy_args (tuple): Positional arguments to pass to `spy_callable` (default: empty tuple).
            spy_kwargs (dict): Keyword arguments to pass to `spy_callable` (default: empty dict).
            target_method (str): Name of the method to spy on (default: '__init__').
            active (bool): Whether the spy is active initially (default: True).

        Example:
            >>> class MyClass:
            ...     def my_method(self):
            ...         pass
            >>> def my_handler(instance):
            ...     print(f"Spy triggered on {instance}")
            >>> spy = MethodSpy(MyClass, my_handler, target_method='my_method')
            >>> obj = MyClass()
            >>> obj.my_method()  # Calls my_handler(obj)
        """

        self._target = target
        self._spy_callable = spy_callable
        self._spy_args = spy_args
        self._spy_kwargs = spy_kwargs
        self._target_method = target_method
        self._active = active

        # Add this Spy to the list of Spies for each (class, method)
        key = self._create_registery_key()
        if key not in self.spies_registery:
            self.spies_registery[key] = []
            self._wrap_class_method(target, self._target_method)

        self.spies_registery[key].append(self)


    def _create_registery_key(self) -> Tuple[Type, str]:
        return (self._target, self._target_method)

    def _create_original_name(self, method_name: str) -> str:
        return f'__original_{method_name}'


    def _wrap_class_method(self, target: Type, method_name: str) -> None:
        """Wrap the target method to call all Spies."""
        original_name = self._create_original_name(method_name)

        if not hasattr(target, method_name):
            raise ValueError(f"The target class {target.__name__} does not have a method '{method_name}'.")

        # Save the original method if not already saved
        if not hasattr(target, original_name):
            setattr(target, original_name, getattr(target, method_name))

        @wraps(getattr(target, original_name))
        def new_method(instance: Any, *args, **kwargs) -> Any:
            original_method: Callable = getattr(instance, original_name)
            output = original_method(*args, **kwargs)

            key = self._create_registery_key()
            for spy in MethodSpy.spies_registery.get(key, []):
                if spy._is_active():
                    spy._spy_callable(instance, *spy._spy_args, **spy._spy_kwargs)

            return output

        setattr(target, method_name, new_method)


    def activate(self) -> None:
        """Activate the spy."""
        self._active = True

    def deactivate(self) -> None:
        """Deactivate the spy."""
        self._active = False

    def remove(self) -> None:
        """Remove the handler and restore the original method if no spies are left."""
        key = self._create_registery_key()
        if key in self.spies_registery:
            self.spies_registery[key].remove(self)
            if not self.spies_registery[key]:
                # Restore the original method
                original_name = self._create_original_name(self._target_method)
                if hasattr(self._target, original_name):
                    setattr(self._target, self._target_method, getattr(self._target, original_name))
                    delattr(self._target, original_name)

                del self.spies_registery[key]


    def _is_active(self) -> bool:
        return bool(self._active)

    def __bool__(self) -> bool:
        return self._is_active()

    def __str__(self) -> str:
        return f'<MethodSpy of: {self._target} (method={self._target_method})>'

    def __repr__(self) -> str:
        return f'MethodSpy({self._target}, {self._spy_callable}, target_method={self._target_method}, spy_args={self._spy_args}, spy_kwargs={self._spy_kwargs})'

    def __del__(self) -> None:
        self.remove()
