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
    It allows calling a method on the object to `get`, `set`, `delete`.
    You can modify mapped value on remote side with ease.

    Example:
    >>> import requests
    >>>
    >>> class RemoteUser:
    ...     def __init__(self, user_id: int):
    ...         self.user_id = user_id
    >>>
    ...     def _get_name(self):
    ...         print("Fetching from API...")
    ...         return requests.get(f"https://api.example.com/user/{self.user_id}/name").json()["name"]
    >>>
    ...     def _set_name(self, value):
    ...         print("Sending update to API...")
    ...         requests.post(
    ...             f"https://api.example.com/user/{self.user_id}/name",
    ...             json={"name": value}
    ...         )
    >>>
    ...     name = RemoteAttrib[str](  # Specify true type if using type hints.
    ...         get=_get_name,
    ...         set=_set_name,
    ...         cache_timeout=10
    ...     )
    ... user = RemoteUser(user_id=42)
    >>>
    ... print(user.name)  # Calls API, caches result
    ... print(user.name)  # Uses cache
    ... time.sleep(11)
    ... print(user.name)   # Refreshes from API
    >>> 
    ... user.name = "Alice"  # Sends update to API
    """
    def __init__(
            self,
            get: Optional[Callable[..., Any]] = None,
            set: Optional[Callable[..., None]] = None,
            delete: Optional[Callable[..., None]] = None,
            cache_timeout: int | float = 0,
            *,
            get_args: Optional[Tuple[Any]] = None,
            get_kwargs: Optional[Dict[str, Any]] = None,
            set_args: Optional[Tuple[Any]] = None,
            set_kwargs: Optional[Dict[str, Any]] = None,
            delete_args: Optional[Tuple[Any]] = None,
            delete_kwargs: Optional[Dict[str, Any]] = None,
        ) -> None:
        '''
        A mixin for remote attributes.

        Args:
            get: A function that gets the attribute value. Defaults to None.
            set: A function that sets the attribute value. Defaults to None.
            delete: A function that deletes the attribute. Defaults to None.
            cache_timeout: The time in seconds to cache the attribute value. Defaults to 0.
            get_args: The arguments to pass to the get function. Defaults to None.
            get_kwargs: The keyword arguments to pass to the get function. Defaults to None.
            set_args: The arguments to pass to the set function. Defaults to None.
            set_kwargs: The keyword arguments to pass to the set function. Defaults to None.
            delete_args: The arguments to pass to the delete function. Defaults to None.
            delete_kwargs: The keyword arguments to pass to the delete function. Defaults to None.
        '''
        self._get = get
        self._set = set
        self._del = delete
        self._get_args = get_args or ()
        self._set_args = set_args or ()
        self._del_args = delete_args or ()
        self._set_kwargs = set_kwargs or {}
        self._get_kwargs = get_kwargs or {}
        self._del_kwargs = delete_kwargs or {}
        self._cache_timeout = cache_timeout
        self.name: str = ''  # python will fill this

    def __ensure_cache__(self, instance: Any) -> None:
        if not hasattr(instance, '_remote_attrib_cache'):
            instance._remote_attrib_cache = {}

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

        if self._get is None:
            raise AttributeError(f'No getter for attribute {self.name}.')

        value = self._get(
            instance,
            *self._get_args,
            **self._get_kwargs,
        )

        if self._cache_timeout > 0:
            instance._remote_attrib_cache[self.name] = (value, time.time())

        return value

    def __set__(self, instance: Any, value: Any) -> None:
        if self._set is None:
            raise AttributeError(f'No setter for attribute {self.name}.')

        self.__ensure_cache__(instance)
        self._set(
            instance,
            value,
            *self._set_args,
            **self._set_kwargs,
        )
        instance._remote_attrib_cache.pop(self.name, None)

    def __delete__(self, instance: Any) -> None:
        if self._del is None:
            raise AttributeError(
                f'No deleter for attribute {self.name}.')

        self.__ensure_cache__(instance)
        self._del(
            instance,
            *self._del_args,
            **self._del_kwargs,
        )
        instance._remote_attrib_cache.pop(self.name, None)
