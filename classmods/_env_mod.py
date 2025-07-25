import os
import inspect
from typing import ClassVar, Optional, List, Dict, Any, Callable, Set, Type, get_type_hints
from functools import wraps


class ENVMod:
    """
    A utility to generate .env files, auto-load environment variables from constructors,
    and support auto-documentation and integration with python-dotenv.
    """
    class _Item:
        """
        Represents a single environment variable item extracted from constructor args.
        """
        def __init__(
                self,
                arg_name: str,
                class_prefix: str = '',
                description: Optional[List[str]] = None,
                required: bool = False,
                default: Optional[str] = None,
            ) -> None:
            self._arg_name: str = arg_name
            self._default: str = default or ''
            self._required: bool = required
            self._description: List[str] = [line.strip() + '\n' for line in (description or [])]
            self._key: str = self._generate_key(class_prefix)

        def _generate_key(self, prefix: str) -> str:
            clean = self._arg_name
            for ch in "- .":
                clean = clean.replace(ch, "_")
            return f"{prefix}_{clean.upper()}" if prefix else clean.upper()

    class _Section:
        """
        A group of related environment items, grouped by class name.
        """
        def __init__(self, name: str) -> None:
            self.name: str = name.upper()
            self.items: List[ENVMod._Item] = []

        def _add_item(self, item: 'ENVMod._Item') -> None:
            self.items.append(item)

        def _generate(self) -> str:
            lines: List[str] = []
            lines.append(f"{'#' * (len(self.name) + 24)}")
            lines.append(f"########### {self.name} ###########")

            for item in self.items:
                lines.append(f"###### {item._arg_name} {'(Required)' if item._required else ''}")
                lines.append("####")
                if item._description:
                    lines.extend(f"## {line.strip()}" for line in item._description)
                lines.append(f"## Default={item._default}")
                lines.append("####")
                lines.append(f"{item._key}=")
                lines.append("")

            lines.append(f"{'#' * (len(self.name) + 24)}")
            return "\n".join(lines)

    class _ENVFile:
        """
        Handles the entire .env structure with multiple sections.
        """
        def __init__(self) -> None:
            self.sections: Dict[str, ENVMod._Section] = {}

        def _get_or_create(self, name: str) -> 'ENVMod._Section':
            name = name.upper()
            if name not in self.sections:
                self.sections[name] = ENVMod._Section(name)
            return self.sections[name]

        def _generate(self) -> str:
            return '\n'.join(section._generate() for section in self.sections.values())

        def _save_as_file(self, path: str) -> None:
            with open(path, 'w') as f:
                f.write(self._generate())

        def _get_all_keys(self) -> List[str]:
            return [item._key for section in self.sections.values() for item in section.items]

    _envfile: _ENVFile = _ENVFile()
    _registry: Dict[Callable, Dict[str, str]] = {}
    _used_env_keys: ClassVar[Set[str]] = set()

    @classmethod
    def register(cls, *, exclude: Optional[List[str]] = None) -> Callable:
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
            qualname = func.__qualname__.split('.')[0].upper()
            section = cls._envfile._get_or_create(qualname)
            arg_map: Dict[str, str] = {}

            docstring = inspect.getdoc(func) or ""
            doc_lines = docstring.splitlines() if docstring else []
            type_hints = get_type_hints(func)

            for param in sig.parameters.values():
                if param.name in ['self', 'cls'] or param.name in exclude:
                    continue

                param_type = type_hints.get(param.name, str)
                if param_type not in (str, int, float, bool):
                    raise TypeError(f"Cannot register parameter '{param.name}' of type '{param_type.__name__}'")

                param_doc = [line.strip() for line in doc_lines if param.name in line.lower()]
                default = (
                    None if param.default is inspect.Parameter.empty else str(param.default)
                )

                item = cls._Item(
                    arg_name=param.name,
                    class_prefix=qualname,
                    description=param_doc,
                    required=param.default is inspect.Parameter.empty,
                    default=default,
                )

                # Check for duplicates
                if item._key in cls._used_env_keys:
                    raise ValueError(
                        f"Duplicate environment key detected: '{item._key}' already registered. "
                        f"Check other registered methods or exclude this parameter."
                )
                cls._used_env_keys.add(item._key)
                section._add_item(item)
                arg_map[param.name] = item._key

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            cls._registry[wrapper] = arg_map

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
        mapping = cls._registry.get(func)
        if mapping is None:
            for f, keys in cls._registry.items():
                if getattr(f, '__wrapped__', None) == func:
                    mapping = keys
                    break

        if not mapping:
            raise ValueError(f'This method or function is not registerd: {func.__name__}')

        sig = inspect.signature(func)
        types = get_type_hints(func)

        def cast(value: str, _type: Type) -> Any:
            if _type == bool:
                if value.lower() in ('1', 'true', 'yes'): return True
                elif value.lower() in ('0', 'false', 'no'): return False
                else: raise ValueError(f"Casting env is not a valid bool: {value}. valid bool: '0', 'false', 'no', '1', 'true', 'yes'")

            return _type(value)

        result = {}
        for arg, env_key in mapping.items():
            value = os.environ.get(env_key)
            if value is None or value == '':
                result[arg] = None
                continue

            result[arg] = cast(value, types.get(arg, str))

        # Remove None from results
        result = {k: v for k, v in result.items() if v is not None}

        return result

    @classmethod
    def save_example(cls, path: str = ".env_example") -> None:
        """
        Save an example .env file based on all registered items.
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
            section_name: str,
            key: str,
            description: Optional[List[str]] = None,
            default: Optional[str] = None,
            required: bool = False,
        ) -> None:
        """
        Manually add an env item not tied to a class.
        """
        section = cls._envfile._get_or_create(section_name)
        item = cls._Item(
            arg_name=key,
            class_prefix=section.name,
            description=description,
            default=default,
            required=required,
        )
        section._add_item(item)

    @staticmethod
    def load_dotenv(*args: Any, **kwargs: Any) -> None:
        """
        Wrapper for python-dotenv, loads .env into os.environ.
        """
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(*args, **kwargs)
        except ImportError:
            raise NotImplementedError(
                "Dependency not present. Install it with `pip install python-dotenv`."
            )
