import os, inspect
from functools import wraps
from typing import (
    Literal,
    Optional,
    List,
    Dict,
    Any,
    Callable,
    Set,
    Type,
    TypeAlias,
    Union,
    get_type_hints
)

try:
    import dotenv as _
except ImportError:
    print("ENVMod Warning: `python-dotenv` not installed. install for better usage")

ENVParsableTypes: TypeAlias = Type[str | int | float | bool]
ENVParsable: TypeAlias = str | int | float | bool


class _Item:
    """
    Represents a single environment variable with metadata, type casting,
    default handling, and formatting support for .env example generation.
    """
    def __init__(
            self,
            name: str,
            type_hint: Any,
            prefix: str = '',
            description: Optional[List[str]] = None,
            required: bool = False,
            default: Optional[Any] = None
        ) -> None:
        self._name = name
        self._prefix = prefix
        self._default = default
        self._required = required
        self._description = [line.strip() + '\n' for line in (description or [])]
        self._value = None
        self._normal_type = self._normalize_type(type_hint)
        self._env_key = self._generate_env_key()

    def _generate_env_key(self) -> str:
        clean = self._name
        for ch in "- .":
            clean = clean.replace(ch, "_")
        return f"{self._prefix}_{clean.upper()}" if self._prefix else clean.upper()

    def _normalize_type(self, type_hint: Any) -> ENVParsableTypes:
        """
        Resolve supported env types from typing hints (e.g., Optional[str], Literal['x'], etc.).
        """
        origin = getattr(type_hint, '__origin__', None)

        # Direct types
        if type_hint in (str, int, float, bool):
            return type_hint

        # Optional[...] or Union[...]
        elif origin is Union:
            args = [arg for arg in type_hint.__args__ if arg is not type(None)]
            if len(args) == 1:
                return self._normalize_type(args[0])

        # Literal['a', 'b'] => treat as str
        elif origin is Literal:
            return str

        raise TypeError(
                f"Cannot register parameter '{self._name}' of type '{type_hint}'"
            )

    def cast(self, value: str) -> ENVParsable | None:
        """
        Cast the string value to its type_hint.
        """
        if self._normal_type == bool:
            if value.lower() in ("1", "true", "yes"): return True
            if value.lower() in ("0", "false", "no"): return False
            if value.lower() in ("none", "null"): return None
            raise ValueError(f"Invalid boolean: {value}")
        if value is None:
            return None
        return self._normal_type(value)

    def load_value(self) -> ENVParsable | None:
        """
        Loads the value from env.
        """
        value = os.environ.get(self._env_key)
        if value is None or value == "":
            if self._required:
                self._value = None
                raise ValueError(f"This env is required and can't be None: {self._env_key}")
            elif self._default is not None:
                self._value = self._default
                return self._default
            else:
                self._value = None
                return None
        self._value = value
        return self.cast(value)


    def __str__(self) -> str:
        return f"{self._env_key}={self._value or self._default if self._default is not None else ''}"

    def __repr__(self) -> str:
        return f"<_Item key={self._env_key!r}, type={self._normal_type.__name__}, default={self._default}, required={self._required}>"


class _Section:
    """
    Represents a logical group of environment variables, typically tied to a class or component.
    Holds multiple _Item instances and provides formatted string output for .env_example sections.
    """
    def __init__(
            self,
            name: str,
            key: Optional[Any] = None
        ) -> None:

        self._name = name.upper()
        self._key = key
        self._items: Dict[str, _Item] = {}
        self._order: List[str] = []

    def add_item(
                self,
                item: _Item,
            ) -> None:
        if item._name in self._items:
            raise ValueError(f"Duplicate parameter '{item._name}' in section '{self._name}'")

        self._items[item._name] = item
        if item._name not in self._order:
            self._order.append(item._name)

    def _generate(self) -> str:
        lines: List[str] = []
        lines.append("#" * (len(self._name) + 24))
        lines.append(f"########### {self._name} ###########")
        for name in self._order:
            item = self._items[name]
            lines.append(f"###### {item._name} {'(Required)' if item._required else ''}")
            lines.append("####")
            if item._description:
                lines.extend(f"## {line.strip()}" for line in item._description)
            lines.append(f"## Default={item._default}")
            lines.append("####")
            lines.append(f"{item._env_key}=")
            lines.append("")
        lines.append("#" * (len(self._name) + 24))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<_Section name={self._name}, key={self._key}, items={list(self._items.keys())}>"


class _ENVFile:
    """
    Handles generation of the .env_example file based on the current
    registered environment sections and items.
    """
    def __init__(self) -> None:
        self._sections: Dict[tuple[str, Optional[Any]], _Section] = {}

    def get_or_create(self, section_name: Optional[str] = None, key: Optional[Any] = None) -> _Section:
            if section_name:
                # Shared section by name: ignore key
                lookup = (section_name, None)
            elif key:
                # Unique section per function
                lookup = (str(key), key)
            else:
                raise ValueError("Either section_name or key must be specified.")

            if lookup in self._sections:
                return self._sections[lookup]

            section = _Section(section_name if section_name else str(key), key)
            self._sections[lookup] = section
            return section

    def _generate(self) -> str:
        return "\n".join(sec._generate() for sec in self._sections.values())

    def _save_as_file(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self._generate())

    def get_all_env_keys(self) -> List[str]:
        keys: List[str] = []
        for sec in self._sections.values():
            keys.extend(sec._items[name]._env_key for name in sec._order)
        return keys


class ENVMod:
    """
    Main API class for managing .env variables. Supports manual and decorator-based
    registration of environment items, type-safe value loading, and .env_example generation.
    """
    _envfile: _ENVFile = _ENVFile()
    _registry: Dict[Callable, _Section] = {}

    @classmethod
    def register(
            cls,
            *,
            section_name: Optional[str] = None,
            exclude: Optional[List[str]] = None,
            cast: Optional[Dict[str, ENVParsableTypes]] = None,
            shared_parameters: bool = False,
        ) -> Callable:
        """
        Decorator to register a class or instance method for environment variable parsing.

        This decorator inspects the function signature, automatically creates environment variable
        items for each parameter (excluding 'self', 'cls', or parameters listed in `exclude`),
        and registers them in the specified section.
        By default, parameters must be unique within the section.
        Use `shared_parameters=True` to allow multiple methods to share the same parameter name,
        with type consistency checks.

        Args:
            section_name (Optional[str]): The name of the section in the .env file. If None, a
                unique section is created based on the function's qualified name.
            exclude (Optional[List[str]]): A list of parameter names to exclude from environment
                registration.
            cast (Optional[Dict[str, ENVParsableTypes]]): A dictionary to override type hints for
                specific parameters. Keys are parameter names, values are types (str, int, float, bool).
            shared_parameters (bool): If True, allows parameters with the same name to be shared
                across multiple functions in the same section. Type conflicts will raise TypeError.

        Raises:
            TypeError: If a parameter type is not supported or if a shared parameter type conflicts
                with an existing one in the section.
            ValueError: If a parameter already exists in the section and `shared_parameters` is False.

        Example:
            >>> class APIService:
            ...     @ENVMod.register(section_name="API", exclude=["ssl_key"])
            ...     def __init__(self, host: str, port: int, username: str = None, password: str = None, ssl_key: str = None):
            ...         ...
            ...
            >>> class AnotherService:
            ...     @ENVMod.register(section_name="API", shared_parameters=True)
            ...     def connect_db(self, host: str, port: int, db_name: str):
            ...         ...
            ...
            >>> # Usage: load arguments from environment
            >>> api_service = APIService(**ENVMod.load_args(APIService.__init__))
            >>> db_service = AnotherService(**ENVMod.load_args(AnotherService.connect_db))

            ## Not Recommended ##
            >>> api_service = APIService(envmod_loader=True) #type: ignore

        Notes:
            - Type hints must be provided to ensure proper type casting from environment strings.
            - Default values are automatically handled; required parameters are those without defaults.
            - Environment variable names are generated using the section name and the parameter name
            (e.g., "API_HOST").
            - You can use the `envmod_loader` as a parameter to magicly load args, but it is not IDE friendly.
        """
        exclude = exclude or []

        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)
            # Use section_name if provided, otherwise unique section per function
            sec_name = section_name or func.__qualname__.replace(".", "_")
            section = cls._envfile.get_or_create(sec_name, key=None if section_name else func)

            doc_lines = (inspect.getdoc(func) or "").splitlines()
            type_hints = get_type_hints(func)

            for param in sig.parameters.values():
                if param.name in ("self", "cls") or param.name in exclude:
                    continue

                item = _Item(
                    name=param.name,
                    prefix=section._name,
                    type_hint=cast[param.name] if cast and param.name in cast else type_hints.get(param.name, str),
                    description=[line.strip() for line in doc_lines if param.name in line.lower()],
                    default=None if param.default is inspect.Parameter.empty else param.default,
                    required=param.default is inspect.Parameter.empty,
                )

                if param.name in section._items:
                    if shared_parameters:
                        existing_item = section._items[param.name]

                        if existing_item._normal_type != item._normal_type:
                            raise TypeError(
                                f'There are conflicts in types for parameter `{param.name}`: exsiting={existing_item._normal_type}, new={item._normal_type}'
                            )

                        continue

                    raise ValueError(
                        f"Parameter '{param.name}' is already registered in section '{section._name}'"
                    )
                section.add_item(item)

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if kwargs.pop("envmod_loader", False):
                    loaded_args = cls.load_args(func)
                    kwargs = {**loaded_args, **kwargs}
                return func(*args, **kwargs)

            cls._registry[wrapper] = section

            return wrapper
        return decorator

    @classmethod
    def load_args(cls, func: Callable) -> Dict[str, Any]:
        """
        Load registered function/class args from environment variables.

        Example:
        >>> api_service = APIService(**ENVMod.load_args(APIService.__init__))

        In above example the ENVMod will load the registered variables and pass them to the method.

        """
        section = cls._registry.get(func)
        if section is None:
            raise ValueError(f"Function not registered: {func.__name__}")
        return {name: section._items[name].load_value() for name in section._order}

    @classmethod
    def save_example(cls, path: str = ".env_example") -> None:
        """
        Save an example .env file based on all registered items.

        WARNING: Do not store your values in the example file,
        it gets overwritten on secound execution.
        """
        cls._envfile._save_as_file(path)

    @classmethod
    def sync_env_file(cls, path: str = ".env") -> None:
        """
        Merge existing .env file with missing expected keys
        while preserving definition order.
        """
        expected_keys = cls._envfile.get_all_env_keys()

        existing: Dict[str, str] = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.rstrip("\n").split("=", 1)
                        existing[key.strip()] = value.strip()

        written: Set[str] = set()
        lines: List[str] = []
        for key in expected_keys:
            value = existing.get(key, "")
            lines.append(f"{key}={value}")
            written.add(key)
        for key, value in existing.items():
            if key not in written:
                lines.append(f"{key}={value}")

        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")


    @staticmethod
    def load_dotenv(*args: Any, **kwargs: Any) -> None:
        """
        Wrapper for python-dotenv, loads .env into os.environ.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(*args, **kwargs)
        except ImportError:
            raise NotImplementedError("Install python-dotenv for this feature: `pip install python-dotenv`")
