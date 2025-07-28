import os, inspect
from functools import wraps
from typing import (
    ClassVar,
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
    print('ENVMod Warning: python-dotenv not installed. install for better usage')

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
            default: Optional[str] = None,
        ) -> None:
        self._name = name
        self._prefix = prefix
        self._default = default
        self._required = required
        self._description = [line.strip() + '\n' for line in (description or [])]

        self._value = None
        self._normal_type = self._normalize_type(type_hint)
        self._env_key = self._generate_key()

    def _generate_key(self) -> str:
        """
        Generate and normalize env key.
        """
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
            if value.lower() in ('1', 'true', 'yes'): return True
            if value.lower() in ('0', 'false', 'no'): return False
            if value.lower() in ('null', 'none'): return None
            raise ValueError(f"Invalid boolean: {value}")

        if value == None:
            return None

        return self._normal_type(value)

    def load_value(self) -> ENVParsable | None:
        """
        Loads the value from env.
        """
        value = os.environ.get(self._env_key)
        if value is None or value == '':
            if self._required:
                self._value = None
                raise ValueError(f'This env is required and can not be None: {self._env_key}')

            elif self._default:
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
        return (
            f"<_Item key={self._env_key!r}, type={self._normal_type.__name__}, "
            f"default={self._default if self._default is not None else ''}, required={self._required}>"
        )


class _Section:
    """
    Represents a logical group of environment variables, typically tied to a class or component.
    Holds multiple _Item instances and provides formatted string output for .env_example sections.
    """
    def __init__(self, name: str) -> None:
        self._name: str = name.upper()
        self._items: List[_Item] = []

    def _add_item(self, item: _Item) -> None:
        self._items.append(item)

    def _generate(self) -> str:
        lines: List[str] = []
        lines.append(f"{'#' * (len(self._name) + 24)}")
        lines.append(f"########### {self._name} ###########")

        for item in self._items:
            lines.append(f"###### {item._name} {'(Required)' if item._required else ''}")
            lines.append("####")
            if item._description:
                lines.extend(f"## {line.strip()}" for line in item._description)
            lines.append(f"## Default={item._default}")
            lines.append("####")
            lines.append(f"{item._env_key}=")
            lines.append("")

        lines.append(f"{'#' * (len(self._name) + 24)}")
        return "\n".join(lines)


    def __str__(self) -> str:
        return f"Section: {self._name} ({len(self._items)} items)"

    def __repr__(self) -> str:
        return f"<_Section name={self._name!r}, items={[i._env_key for i in self._items]}>"


class _ENVFile:
    """
    Handles generation of the .env_example file based on the current
    registered environment sections and items.
    """
    def __init__(self) -> None:
        self._sections: Dict[str, _Section] = {}

    def _get_or_create(self, name: str) -> _Section:
        name = name.upper()
        if name not in self._sections:
            self._sections[name] = _Section(name)

        return self._sections[name]

    def _generate(self) -> str:
        return '\n'.join(section._generate() for section in self._sections.values())

    def _save_as_file(self, path: str) -> None:
        with open(path, 'w') as f:
            f.write(self._generate())

    def _get_all_keys(self) -> List[str]:
        return [item._env_key for section in self._sections.values() for item in section._items]


    def __str__(self) -> str:
        return f".env_example generator for {len(self._sections)} sections"

    def __repr__(self) -> str:
        return f"<_ENVFile sections={[s._name for s in self._sections.values()]}>"


class ENVMod:
    """
    Main API class for managing .env variables. Supports manual and decorator-based
    registration of environment items, type-safe value loading, and .env_example generation.
    """
    _envfile: _ENVFile = _ENVFile()
    _registry: Dict[Callable, _Section] = {}
    _used_env_keys: ClassVar[Set[str]] = set()

    @classmethod
    def register(
            cls,*,
            exclude: Optional[List[str]] = None,
            cast: Optional[Dict[str, ENVParsableTypes]] = None,
        ) -> Callable:
        """
        Decorator to register class methods for env parsing.

        Raise:
            TypeError: If an argument is not env parsable.

        Example:
        >>> class APIService:
        ...    @ENVMod.register(exclude=['ssl_key'])
        ...    def __init__(
                    self,
                    host: str,
                    port: int,
                    username: str = None,
                    password: str = None,
                    ssl_key: SSLKey
                ) -> none:
        ...        ...
        
        In this example ENVMod will create env items for each argument except ssl_key.
        
        Note: Make sure you add type hints to get the same type when loading from env file.
        """
        exclude = exclude or []

        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)
            class_name = func.__qualname__.split('.')[0].upper()
            section = cls._envfile._get_or_create(class_name)
            arg_map: Dict[str, str] = {}

            docstring = inspect.getdoc(func) or ""
            doc_lines = docstring.splitlines() if docstring else []
            type_hints = get_type_hints(func)

            for param in sig.parameters.values():
                if param.name in ['self', 'cls'] or param.name in exclude:
                    continue

                item = cls.add(
                    name = param.name,
                    section_name = class_name,
                    type_hint = cast.get(param.name) if cast and param.name in cast else type_hints.get(param.name, str),
                    description = [line.strip() for line in doc_lines if param.name in line.lower()],
                    default = None if param.default is inspect.Parameter.empty else param.default,
                    required = param.default is inspect.Parameter.empty,
                )

                arg_map[param.name] = item._env_key

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
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
            for f, s in cls._registry.items():
                if getattr(f, '__wrapped__', None) == func:
                    section = s
                    break

        if section is None:
            raise ValueError(f'This method or function is not registered: {func.__name__}')

        result = {}
        for item in section._items:
            result[item._name] = item.load_value()

        return result

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
        Merge existing .env file with missing expected keys.
        """
        expected_keys = set(cls._envfile._get_all_keys())

        existing: Dict[str, str] = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        existing[key.strip()] = value.strip()

        new_content = ''
        all_keys = expected_keys.union(existing.keys())

        for key in sorted(all_keys):
            value = existing.get(key, '')
            new_content += f"{key}={value}\n"

        with open(path, 'w') as f:
            f.write(new_content)

    @classmethod
    def add(
            cls,
            name: str,
            section_name: str,
            type_hint: Any,
            description: Optional[List[str]] = None,
            default: Optional[str] = None,
            required: bool = False,
        ) -> _Item:
        """
        Manually add an env item not tied to a class.
        """
        section = cls._envfile._get_or_create(section_name)
        item = _Item(
            name = name,
            prefix = section._name,
            type_hint = type_hint,
            description = description,
            default = default,
            required = required,
        )                

        # Check for duplicates
        if item._env_key in cls._used_env_keys:
            raise ValueError(
                f"Duplicate environment key detected: '{item._env_key}' already registered. "
                f"Check other registered methods or exclude this parameter."
        )

        cls._used_env_keys.add(item._env_key)
        section._add_item(item)

        return item

    @staticmethod
    def load_dotenv(*args: Any, **kwargs: Any) -> None:
        """
        Wrapper for python-dotenv, loads .env into os.environ.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(*args, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "Dependency not present. Install it with `pip install python-dotenv`."
            )
