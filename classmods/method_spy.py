from typing import Any, Dict, List, Iterable, Tuple, Type, Callable, Union
from functools import wraps

HandlerCallable = Callable[[object], None]

class MethodSpy:
    # Dictionary to store handlers for each (class, method) pair
    class_method_handlers: Dict[Tuple[Type, str], List['MethodSpy']] = {}

    def __init__(
            self, 
            targets: Union[Type, Iterable[Type]], 
            handler_function: HandlerCallable,
            handler_args: tuple = (),
            handler_kwargs: dict = {},
            *,
            target_method: str = '__init__',
            active: bool = True,
    ) -> None:
        # Ensure targets is always a list
        if not isinstance(targets, (list, tuple)):
            targets = [targets]

        self._targets = list(targets)
        self._handler_function = handler_function
        self._handler_args = handler_args
        self._handler_kwargs = handler_kwargs
        self._target_method = target_method
        self._active = active

        # Add this handler to the list of handlers for each (class, method)
        for target in self._targets:
            key = (target, self._target_method)
            if key not in self.class_method_handlers:
                self.class_method_handlers[key] = []
                self._wrap_class_method(target, self._target_method)
            self.class_method_handlers[key].append(self)

    def _create_original_name(self, method_name: str) -> str:
        return f'__original_{method_name}'

    def _wrap_class_method(self, target: Type, method_name: str) -> None:
        """Wrap the target method to call all handlers."""
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
            original_method = getattr(instance, original_name)
            output = original_method(*args, **kwargs)

            # Call all active handlers for this (class, method)
            key = (target, method_name)
            for handler in MethodSpy.class_method_handlers.get(key, []):
                if handler._active:
                    handler._handler_function(instance, *self._handler_args, **self._handler_kwargs)

            return output

        # Replace the target method with the new one
        setattr(target, method_name, new_method)

    def activate(self) -> None:
        """Activate the handler."""
        self._active = True

    def deactivate(self) -> None:
        """Deactivate the handler."""
        self._active = False

    def remove(self) -> None:
        """Remove the handler and restore the original method if no handlers are left."""
        for target in self._targets:
            key = (target, self._target_method)
            if key in self.class_method_handlers:
                self.class_method_handlers[key].remove(self)
                if not self.class_method_handlers[key]:  # No handlers left
                    # Restore the original method
                    original_name = self._create_original_name(self._target_method)
                    if hasattr(target, original_name):
                        setattr(target, self._target_method, getattr(target, original_name))
                        delattr(target, original_name)
                    del self.class_method_handlers[key]


    def __str__(self) -> str:
        return f'<Handler of: {self._targets} (method={self._target_method})>'

    def __repr__(self) -> str:
        return f'Handler({self._targets}, {self._handler_function}, active={self._active}, target_method={self._target_method}, handler_args={self._handler_args}, handler_kwargs={self._handler_kwargs})'
