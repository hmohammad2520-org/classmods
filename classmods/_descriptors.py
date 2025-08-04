import time
from typing import Any, Dict, Optional, Callable, Self, Tuple, Type, TypeVar, Generic, Union, overload

T = TypeVar('T')

class ConstantAttrib(Generic[T]):
    """
    A descriptor that enforces constant values at instance level.
    (Does not support class-level assignment)

    Example:
    >>> class MyClass:
    ...     VALUE = ConstantAttrib[int]()
    ...
    >>> obj = MyClass()
    >>> obj.VALUE = 42  # First assignment works
    >>> obj.VALUE = 10  # Raises AttributeError
    >>> print(obj.VALUE)  # 42
    """

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.name = name
        self.private_name = f"_{name}_constant"

    @overload
    def __get__(self, instance: None, owner: Type[Any]) -> 'ConstantAttrib[T]': ...
    @overload
    def __get__(self, instance: Any, owner: Type[Any]) -> T: ...
    def __get__(self, instance: Any, owner: Type[Any]) -> Union[T, "ConstantAttrib[T]"]:
        if instance is None:
            return self

        if self.private_name not in instance.__dict__:
            raise AttributeError(f"Constant attribute '{self.name}' not set")

        return instance.__dict__[self.private_name]

    def __set__(self, instance: Any, value: T) -> None:
        if self.private_name in instance.__dict__:
            raise AttributeError(f"Cannot modify constant attribute '{self.name}'")
        instance.__dict__[self.private_name] = value

    def __delete__(self, instance: Any) -> None:
        raise AttributeError(f"Cannot delete constant attribute '{self.name}'")

class RemoteAttrib(Generic[T]):
    """
    Descriptor that acts as a remote attribute.
    It allows calling a method on the object to `getter`, `setter`, `deleter`.
    You can modify mapped value on remote side with ease.

    Why not use `@property`?
    - You can`t pass additional args, kwargs to a call; so your class keeps getting bigger.
    - caching is not available on `property`.
    - easy usage with lambda ! and you save a lot of code.

    Example:
    >>> import requests
    >>>
    >>> class RemoteUser:
    ...     def __init__(self, user_id: int):
    ...         self.user_id = user_id
    ...
    ...     def _get_parm(self, parameter: str):
    ...         print("Fetching from API...")
    ...         return requests.get(f"https://api.example.com/user/{self.user_id}").json()[parameter]
    ...
    ...     def _set_parm(self, value, parameter):
    ...         print("Sending update to API...")
    ...         requests.post(
    ...             f"https://api.example.com/user/{self.user_id}",
    ...             json={parameter: value}
    ...         )
    ...
    ...     first_name = RemoteAttrib[str](  # Specify true type if using type hints.
    ...         getter=_get_name,
    ...         setter=_set_name,
    ...         cache_timeout=10,
    ...         getter_kwargs={'parameter': 'first_name'},
    ...         setter_kwargs={'parameter': 'first_name'},
    ...     )
    ...     last_name = RemoteAttrib[str](
    ...         getter=lambda self: self._get_parm('last_name'),  # getter has self as first arg.
    ...         setter=lmabda self, value: self._set_parm(value, 'last_name'),  # setter get value as arg.
    ...         cache_timeout=10,
    ...     )
    ...     fullname = RemoteAttrib[str](getter=lambda s: s.first_name+' '+s.last_name)  # compact alternative to property.
    ...
    >>> user = RemoteUser(user_id=42)
    >>>
    >>> print(user.first_name)
    >>> print(user.last_name)
    >>> time.sleep(11)
    >>> print(user.first_name)  # Refreshes from API
    >>> 
    >>> user.first_name = "Alice"  # Sends update to API
    """
    def __init__(
            self,
            getter: Optional[Callable[..., Any]] = None,
            setter: Optional[Callable[..., None]] = None,
            deleter: Optional[Callable[..., None]] = None,
            cache_timeout: int | float = 0,
            *,
            getter_args: Optional[Tuple[Any]] = None,
            getter_kwargs: Optional[Dict[str, Any]] = None,
            setter_args: Optional[Tuple[Any]] = None,
            setter_kwargs: Optional[Dict[str, Any]] = None,
            deleter_args: Optional[Tuple[Any]] = None,
            deleter_kwargs: Optional[Dict[str, Any]] = None,
        ) -> None:
        '''
        A mixin for remote attributes.

        Args:
            getter: A function that gets the attribute value.
            setter: A function that sets the attribute value.
            deleter: A function that deletes the attribute.
            cache_timeout: The time in seconds to cache the attribute value. Defaults to 0.
            getter_args: The arguments to pass to the get function.
            getter_kwargs: The keyword arguments to pass to the get function.
            setter_args: The arguments to pass to the set function.
            setter_kwargs: The keyword arguments to pass to the set function.
            deleter_args: The arguments to pass to the delete function.
            deleter_kwargs: The keyword arguments to pass to the delete function.
        '''
        self._getter = getter
        self._setter = setter
        self._deleter = deleter
        self._getter_args = getter_args or ()
        self._setter_args = setter_args or ()
        self._deleter_args = deleter_args or ()
        self._setter_kwargs = setter_kwargs or {}
        self._getter_kwargs = getter_kwargs or {}
        self._deleter_kwargs = deleter_kwargs or {}
        self._cache_timeout = cache_timeout
        self.name: str = ''

    @staticmethod
    def __ensure_cache__(instance: Any) -> None:
        if not hasattr(instance, '_remote_attrib_cache'):
            setattr(instance, '_remote_attrib_cache', {})

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.name = name

    @overload
    def __get__(self, instance: None, owner: Type[Any]) -> "RemoteAttrib[T]": ...
    @overload
    def __get__(self, instance: Any, owner: Type[Any]) -> T: ...
    def __get__(self, instance: Optional[Any], owner: Optional[Type] = None) -> Union[T, "RemoteAttrib[T]"]:
        if instance is None:
            return self

        self.__ensure_cache__(instance)
        cache_entry = instance._remote_attrib_cache.get(self.name)
        if cache_entry and (time.time() - cache_entry[1] <= self._cache_timeout):
            return cache_entry[0]

        if self._getter is None:
            raise AttributeError(f'No getter for attribute {self.name}.')

        value = self._getter(
            instance,
            *self._getter_args,
            **self._getter_kwargs,
        )

        if self._cache_timeout > 0:
            instance._remote_attrib_cache[self.name] = (value, time.time())

        return value

    def __set__(self, instance: Any, value: Any) -> None:
        if self._setter is None:
            raise AttributeError(f'No setter for attribute {self.name}.')

        self.__ensure_cache__(instance)
        self._setter(
            instance,
            value,
            *self._setter_args,
            **self._setter_kwargs,
        )
        instance._remote_attrib_cache.pop(self.name, None)

    def __delete__(self, instance: Any) -> None:
        if self._deleter is None:
            raise AttributeError(
                f'No deleter for attribute {self.name}.')

        self.__ensure_cache__(instance)
        self._deleter(
            instance,
            *self._deleter_args,
            **self._deleter_kwargs,
        )
        instance._remote_attrib_cache.pop(self.name, None)
