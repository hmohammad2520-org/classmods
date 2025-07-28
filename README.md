# classmods

`classmods` is a lightweight Python package designed to enhance class behavior with minimal effort. It provides modular decorators and descriptors to automate and simplify class-related tasks like environment variable management, creating example env files, monitoring, logging, and more.

# Documentation

All features are well documented and use a high level of `type_hints` for easy understanding and usage.

## Features

* `ConstantAttrib`: A descriptor that acts like a constant. Once set, the value cannot be changed. Raises `AttributeError` on change detection.
* `RemoteAttrib`: A descriptor that acts as a remote attribute. You can modify the mapped value on-the-fly.
* `ENVMod`: The main API class for managing `.env` variables. Supports manual and decorator-based registration of environment items, type-safe value loading, and `.env_example` generation.
* `MethodMonitor`: A class to monitor method calls of a target class, triggering a handler function after the method is called.
* `logwrap`: A dynamic decorator to log function calls. Uses the `logging` module with your current project configurations.
* `suppress_errors`: A decorator that suppresses exceptions raised by the wrapped function and returns a fallback value instead.

## Installation

1. Easy install with pip

```bash
pip install classmods
```

2. Install with git+pip

```bash
pip install git+https://github.com/hmohammad2520-org/classmods
```

## Examples

### Constant Attribute

```python
from classmods import ConstantAttrib

class Config:
    app_name = ConstantAttrib[str]()

    def __init__(self, app_name):
        self.app_name = app_name

config = Config('new app')
config.app_name = 'my app'  # This will raise AttributeError
```

### Remote Attribute

```python
import requests
from classmods import RemoteAttrib

class Config:
    token = RemoteAttrib[str](
        get=lambda: requests.get("https://api.example.com/auth").json()["token"],
        cache_timeout=10,  # keeps result for 10 seconds
    )

config = Config()
token = config.token  # This will send a request and return the result
```

### ENVMod

```python
from os import PathLike
from requests import Session
from classmods import ENVMod

class Config:
    ENVMod.register(exclude=['session'], cast={'log_path': str})
    def __init__(
        self,
        app_name: str,
        session: Session,  # Excluded non-parsable object
        log_path: PathLike,
        log_level: Optional[str] = None,
        port: int = 10,
    ):
        '''
        Args:
            app_name (str): Application name.
            session (Session): Requests session.
            log_path (PathLike): Path of log file.
            log_level (Optional[str]): Log level, e.g., info.
            port (int): Session port, defaults to 10.
        '''

ENVMod.save_example('.my_example_path')
ENVMod.load_dotenv('.my_env')
ENVMod.sync_env_file('.my_env')
config = Config(**ENVMod.load_args(Config.__init__), session=Session())
```

### Method Monitor

```python
from classmods import MethodMonitor

class MyClass:
    def my_method(self):
        pass

def my_handler(instance):
    print(f"Monitor triggered on {instance}")

monitor = MethodMonitor(MyClass, my_handler, target_method='my_method')
obj = MyClass()
obj.my_method()
```

### logwrap

```python
from classmods import logwrap

@logwrap(before=('INFO', '{func} starting, args={args} kwargs={kwargs}'), after=('INFO', '{func} ended'))
def my_func(my_arg, my_kwarg=None):
    ...

my_func('hello', my_kwarg=123)  # Check logs to see the output
```

### Suppress Errors

```python
from classmods import suppress_errors

@suppress_errors(Exception)
def risky_op() -> int:
    return 1 / 0

result = risky_op()  # result = ZeroDivisionError

@suppress_errors(False)
def safe_op() -> bool:
    raise ValueError("error")

result = safe_op()  # result = False
```

## License

MIT License

---

Made with ❤️ by [hmohammad2520](https://github.com/hmohammad2520-org)
