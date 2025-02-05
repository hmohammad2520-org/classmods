import time
from typing import Any, Optional, Callable, Type


class ORMClass:
    def __init__(self) -> None:
        self._attribute_cache: dict[str, tuple[Any, float]] = {}


class ORMDescriptorType:
    def __init__(
            self,
            raw_class: Type,
            constructor: Type | Callable[[Any], Any] = None,
    ) -> None:
        self.raw_class = raw_class
        self.constructor = constructor

    def to_python(self, value: Any) -> Any:
        if self.constructor is not None:
            return self.constructor(value)

        elif isinstance(value, self.raw_class):
            return value

        else:
            return self.raw_class(value)

    def validate(self, value: Any) -> bool:
        return isinstance(value, self.raw_class)

    @property
    def expected_type(self) -> Type:
        return self.raw_class


class ORMDescriptor:
    def __init__(
            self,
            type: ORMDescriptorType,
            getter: Optional[Callable[[ORMClass], Any]] = None,
            setter: Optional[Callable[[ORMClass, str], None]] = None,
            remover: Optional[Callable[[ORMClass, str], None]] = None,
            *,
            validator: Optional[Callable[[str], bool]] = None,
            cache_timeout: int = 0,
            changeable: bool = False,
            nullable: bool = False,
            sensitive: bool = False,
    ) -> None:
        if setter is None and changeable:
            raise ValueError('Setter cannot be `None` when changeable is `True`.')

        if remover is None and nullable:
            raise ValueError('Remover cannot be `None` when nullable is `True`.')

        self.type = type
        self.getter = getter if not sensitive else None
        self.setter = setter
        self.remover = remover
        self.validator = validator
        self.cache_timeout = cache_timeout
        self.changeable = changeable
        self.nullable = nullable
        self.sensitive = sensitive
        self.name = ""

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance: Optional[ORMClass], _) -> Any:
        if instance is None:
            return self

        if self.sensitive:
            raise AttributeError(f"Access to {self.name} is restricted. Data marked as sensetive")  # Prevent access

        cache_entry = instance._attribute_cache.get(self.name)
        if cache_entry and (time.time() - cache_entry[1] <= self.cache_timeout):
            return cache_entry[0]

        if self.getter is None:
            raise AttributeError(f"{self.name} does not have a getter function.")

        raw_value = self.getter(instance)
        value = self.type.to_python(raw_value)

        if self.cache_timeout > 0:
            instance._attribute_cache[self.name] = (value, time.time())

        return value

    def __set__(self, instance: ORMClass, value: Any) -> None:
        if not self.changeable:
            raise AttributeError(f"{self.name} is read-only.")

        if value is None:
            if not self.nullable:
                raise AttributeError(f"{self.name} is not nullable.")
            if self.remover:
                self.remover(instance, value)

        else:
            if not self.type.validate(value):
                raise ValueError(f"Invalid value type for {self.name}: {value.__class__} -> expected: {self.type.raw_class}")

            if self.validator and not self.validator(value):
                raise ValueError(f"Custom validation failed for {self.name}")

            if self.setter:
                self.setter(instance, value)

        instance._attribute_cache.pop(self.name, None)

    def __delete__(self, instance: ORMClass) -> None:
        if self.remover:
            self.remover(instance, self.name)
        instance._attribute_cache.pop(self.name, None)
