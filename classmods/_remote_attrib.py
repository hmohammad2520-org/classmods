import time
from typing import Any, Optional, Callable, Type


class RemoteAttribMixin:
    def __init__(self) -> None:
        self._attribute_cache: dict[str, tuple[Any, float]] = {}


class RemoteAttribType:
    def __init__(
            self,
            raw_class: Type,
            constructor: Optional[Type | Callable[[Any], Any]] = None,
    ) -> None:

        self._raw_class = raw_class
        self._constructor = constructor

    def to_python(self, value: Any) -> Any:
        if self._constructor is not None:
            return self._constructor(value)

        elif isinstance(value, self._raw_class):
            return value

        else:
            return self._raw_class(value)

    def validate(self, value: Any) -> bool:
        return isinstance(value, self._raw_class)

    @property
    def expected_type(self) -> Type:
        return self._raw_class


class RemoteAttrib:
    def __init__(
            self,
            type: RemoteAttribType,
            getter: Optional[Callable[[RemoteAttribMixin], Any]] = None,
            setter: Optional[Callable[[RemoteAttribMixin, str], None]] = None,
            remover: Optional[Callable[[RemoteAttribMixin, str], None]] = None,
            *,
            validator: Optional[Callable[[str], bool]] = None,
            cache_timeout: int = 0,
            sensitive: bool = False,
            changeable: bool = False,
            nullable: bool = False,
    ) -> None:

        if setter is None and changeable:
            raise ValueError('Setter cannot be `None` when changeable is `True`.')

        if remover is None and nullable:
            raise ValueError('Remover cannot be `None` when nullable is `True`.')

        self._type = type
        self._getter = getter if not sensitive else None
        self._setter = setter
        self._remover = remover
        self._validator = validator
        self._cache_timeout = cache_timeout
        self._sensitive = sensitive
        self._changeable = changeable
        self._nullable = nullable
        self._name = "" # Initiated in __set_name__

    def __set_name__(self, owner, name: str) -> None:
        self._name = name

    def __get__(self, instance: Optional[RemoteAttribMixin], _) -> Any:
        if instance is None:
            return self

        if self._sensitive:
            raise PermissionError(f"Access to {self._name} is restricted. Data marked as sensetive.")

        cache_entry = instance._attribute_cache.get(self._name)
        if cache_entry and (time.time() - cache_entry[1] <= self._cache_timeout):
            return cache_entry[0]

        if self._getter is None:
            raise AttributeError(f"{self._name} does not have a getter function.")

        raw_value = self._getter(instance)
        value = self._type.to_python(raw_value)

        if self._cache_timeout > 0:
            instance._attribute_cache[self._name] = (value, time.time())

        return value

    def __set__(self, instance: RemoteAttribMixin, value: Any) -> None:
        if not self._changeable:
            raise AttributeError(f"{self._name} is read-only.")

        if value is None:
            if not self._nullable:
                raise AttributeError(f"{self._name} is not nullable.")
            if self._remover:
                self._remover(instance, value)

        else:
            if not self._type.validate(value):
                raise ValueError(f"Invalid value type for {self._name}: {value.__class__} -> expected: {self._type._raw_class}")

            if self._validator and not self._validator(value):
                raise ValueError(f"Custom validation failed for {self._name}")

            if self._setter:
                self._setter(instance, value)

        instance._attribute_cache.pop(self._name, None)

    def __delete__(self, instance: RemoteAttribMixin) -> None:
        if self._remover:
            self._remover(instance, self._name)
        instance._attribute_cache.pop(self._name, None)
