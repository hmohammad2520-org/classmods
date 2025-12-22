# classmods

`classmods` is a lightweight Python package designed to enhance class behavior with minimal effort. It provides modular decorators and descriptors to automate and simplify class-related tasks like environment variable management, creating example env files, monitoring, logging, and more.

# Documentation

All features are well documented and use a high level of `type_hints` for easy understanding and usage.

## Features 

>(***Click names for more information***)
* [`ConstantAttrib`](docs/constant_attrib.md): A descriptor that acts like a constant. Once set, the value cannot be changed. Raises `AttributeError` on change detection.
* [`RemoteAttrib`](docs/remote_attrib.md): A descriptor that acts as a remote attribute. You can modify the mapped value on-the-fly.
* [`ENVMod`](docs/env_mod.md): The main API class for managing `.env` variables. Supports manual and decorator-based registration of environment items, type-safe value loading, and `.env_example` generation.
* [`MethodMonitor`](docs/method_monitor.md): A class to monitor method calls of a target class, triggering a handler function after the method is called.
* [`logwrap`](docs/logwrap.md): A dynamic decorator to log function calls. Uses the `logging` module with your current project configurations.
* [`suppress_errors`](docs/supress_errors.md): A decorator that suppresses exceptions raised by the wrapped function and returns a fallback value instead.

## Installation

1. Easy install with pip

```bash
pip install classmods
```

2. Install with git+pip

```bash
pip install git+https://github.com/hmohammad2520-org/classmods
```

## License

MIT License

---

Made with ❤️ by [hmohammad2520](https://github.com/hmohammad2520-org)
