# classmods

`classmods` is a lightweight Python package designed to enhance class behavior with minimal effort. It provides modular decorators and descriptors to automate and simplify class-related tasks like environment variable management and creating env example files, monitoring, logging and more.

# Documentation
All features are documented well and use high level of `type_hints` for easy understanding and usage.

## Features

- `ConstantAttrib`: A descriptor that acts like a constant, when you set a constant, it cannot get changed. Raises AttributeError on change detection.
- `RemoteAttrib`: Descriptor that acts as a remote attribute. You can modify mapped value on 
- `ENVMod`: Main API class for managing .env variables. Supports manual and decorator-based registration of environment items, type-safe value loading, and .env_example generation.
- `MethodMonitor`: A class to monitor method calls of a target class, triggering a handler function after the method is called.
- `logwarp`: Simple dynamic decorator to log function calls. Uses the logging module with your current project configurations.
- `supress_errors`: A decorator that suppresses exceptions raised by the wrapped function and returns a fallback value instead.

## Installation

1. Esay install with pip
```bash
pip install classmods
```
2. Install with git+pip
```bash
pip install git+https://github.com/hmohammad2520-org/classmods
```

## Examples
- Constant Attribute
```python
from classmods import ConstantAttrib

class Config:
    app_name = ConstantAttrib[str]()

    def __init__(self, app_name):
        self.app_name = app_name

config = Config('new app')
config.app_name = 'my app'  # This will raise AttibuteError
```

- Remote Attribute
```python
import requests
from classmods import RemoteAttrib

class Config:
    token = RemoteAttrib[str](
        get = lambda: requests.get(f"https://api.example.com/auth").json()["token"],
        cache_timeout = 10,  # keeps result for 10 secounds
    )

config = Config()
token = config.token  # this will send a request and return result
```

- ENVMod
```python
from os import PathLike
from requests import Session
from classmods import ENVMod

class Config:
    ENVMod.register(exclude=['session'], cast={'log_Path': str})
    def __init__(
        self,
        app_name: str,  # type hinting is required
        session: Session,  # Excluded not parsable objects
        log_path: PathLike,  # Gets cast as `str`
        log_level: Optional[str] = None,  # Can use optional or literal
        port: int = 10,  # if not set in env
    )
    '''
    You can add documents to the example env file by simply document the args in normal way.

    Args:
        app_name(str): Application name.
        session(Session): Requests session
        log_path(PathLike): Path of log file.
        log_level(str, Optional): Level of log, E.G. info.
        port(int): Session port defaults to 10
    '''

ENVMod.save_example('.my_example_path')  # generates an example file
ENVMod.load_dotenv('.my_env')  # executes python-dotenv.load_dotenv
ENVMod.sync_env_file('.my_env')  # adds new registered
config = Config(**ENVMod.load_args(Config.__init__), session = Session())  # loads and passes arguments from generated env file
```

- Method Monitor
```python
class MyClass:
    def my_method(self):
        pass
def my_handler(instance):
    print(f"Monitor triggered on {instance}")
monitor = MethodMonitor(MyClass, my_handler, target_method='my_method')
obj = MyClass()
obj.my_method()
```

- logwrap
``` python
from classmods import logwrap

@logwrap(before=('INFO', '{func} starting, args={args} kwargs={kwargs}'), after=('INFO', '{func} ended'))
def my_func(my_arg, my_kwarg=None):
    ...
my_func('hello', my_kwarg=123)  # read logs to see the magic
```

- Suppress Errors
```python
from classmods import suppress_errors

@suppress_errors(Exception)
def risky_op() -> int:
    return 1 / 0
result = risky_op()  # result=ZeroDivisionError


@suppress_errors(False)
def safe_op() -> bool:
    raise ValueError("error")
result = safe_op()  # result=False

```

## License

MIT License

---

Made with ❤️ by [hmohammad2520](https://github.com/hmohammad2520-org)
