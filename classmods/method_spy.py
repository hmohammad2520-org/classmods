from typing import Any, Dict, List, Tuple, Type, Callable
from functools import wraps

HandlerCallable = Callable[[object], None]

class MethodSpy:
    # Dictionary to store handlers for each (class, method) pair
    spies_registery: Dict[Tuple[Type, str], List['MethodSpy']] = {}

    def __init__(
            self, 
            target: Type, 
            spy_callable: HandlerCallable,
            spy_args: tuple = (),
            spy_kwargs: dict = {},
            *,
            target_method: str = '__init__',
            active: bool = True,
    ) -> None:

        self._target = target
        self._spy_callable = spy_callable
        self._spy_args = spy_args
        self._spy_args = spy_kwargs
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

        # Check if the target method exists
        if not hasattr(target, method_name):
            raise AttributeError(f'Target must contain {method_name} method.')

        # Save the original method if not already saved
        if not hasattr(target, original_name):
            setattr(target, original_name, getattr(target, method_name))

        # Define the new method
        @wraps(getattr(target, original_name))
        def new_method(instance: Any, *args, **kwargs) -> Any:
            # Call the original method
            original_method: Callable = getattr(instance, original_name)
            output = original_method(*args, **kwargs)

            # Call all active spies for this (class, method)
            key = self._create_registery_key()
            for handler in MethodSpy.spies_registery.get(key, []):
                if handler._active:
                    handler._spy_callable(instance, *self._spy_args, **self._spy_args)

            return output

        # Replace the target method with the new one
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


    def __str__(self) -> str:
        return f'<MethodSpy of: {self._target} (method={self._target_method})>'

    def __repr__(self) -> str:
        return f'MethodSpy({self._target}, {self._spy_callable}, active={self._active}, target_method={self._target_method}, handler_args={self._spy_args}, handler_kwargs={self._spy_args})'

    def __delete__(self) -> None:
        self.remove()
