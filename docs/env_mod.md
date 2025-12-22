# ENVMod

## Using Docstrings as Environment Documentation

ENVMod **parses function and method docstrings** to generate documentation for environment variables.

Any line in the docstring that references a parameter name is attached to that parameter in the generated `.env_example`.

### Example

```python
class APIService:
    @ENVMod.register(section_name="API")
    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 10,
        debug: bool = False,
    ):
        """
        Initialize the API service.

        Args:
            host: API server hostname or IP address
            port: TCP port used to connect to the API
            timeout: Request timeout in seconds
            debug: Enable verbose debug logging
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.debug = debug
```

### Generated `.env_example`

```env
############################
########### API ###########
###### host (Required)
####
## API server hostname or IP address
## Default=None
####
API_HOST=

###### port (Required)
####
## TCP port used to connect to the API
## Default=None
####
API_PORT=

###### timeout
####
## Request timeout in seconds
## Default=10
####
API_TIMEOUT=

###### debug
####
## Enable verbose debug logging
## Default=False
####
API_DEBUG=
############################
```

---

## Parameter Rules

| Parameter Type   | Behavior                         |
| ---------------- | -------------------------------- |
| No default       | Required env variable            |
| Has default      | Optional                         |
| `Optional[T]`    | Treated as optional              |
| `bool`           | Supports `true/false/1/0/yes/no` |
| Missing required | Raises `ValueError`              |

---

## Large Real-World Example

```python
class DatabaseClient:
    @ENVMod.register(section_name="DATABASE", exclude=["ssl_context"])
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        pool_size: int = 10,
        timeout: float = 5.0,
        ssl_enabled: bool = False,
        ssl_context=None,
    ):
        """
        Database connection configuration.

        Args:
            host: Database server hostname
            port: Database TCP port
            username: Login username
            password: Login password
            database: Default database name
            pool_size: Maximum number of pooled connections
            timeout: Connection timeout in seconds
            ssl_enabled: Enable SSL/TLS for the connection
            ssl_context: Runtime SSL context (not stored in env)
        """
        ...
```

### Resulting Environment Keys

```env
DATABASE_HOST=
DATABASE_PORT=
DATABASE_USERNAME=
DATABASE_PASSWORD=
DATABASE_DATABASE=
DATABASE_POOL_SIZE=
DATABASE_TIMEOUT=
DATABASE_SSL_ENABLED=
```

---

## Multiple Methods Sharing a Section

```python
class CacheService:
    @ENVMod.register(section_name="CACHE")
    def connect(self, host: str, port: int):
        """
        Connect to cache backend.

        Args:
            host: Cache server hostname
            port: Cache server port
        """
        ...

    @ENVMod.register(section_name="CACHE", shared_parameters=True)
    def disconnect(self, port: int):
        """
        Disconnect from cache backend.

        Args:
            port: Cache server port
        """
        ...
```

✔ Shared parameter allowed
✖ Type mismatch is rejected

---

## Explicit Loading (Recommended)

```python
ENVMod.load_dotenv(".env")

cache = CacheService(**ENVMod.load_args(CacheService.__init__))
```

### Why this is recommended

* Fully IDE- and type-checker-friendly
* No hidden behavior
* Explicit and predictable

---

## Magic Auto Loader (Optional)

```python
cache = CacheService(envmod_loader=True)  # type: ignore
```

### How it works

* `envmod_loader=True` triggers ENVMod inside the wrapper
* ENVMod loads env values automatically
* Keyword arguments override env values

### Important Notes

* ❌ Static type checkers will complain
* ❌ IDE autocomplete cannot infer injected parameters
* ✔ Runtime-safe
* ✔ Useful for rapid prototyping

---

## Overriding Types with `cast`

```python
@ENVMod.register(
    section_name="SERVICE",
    cast={"retries": int}
)
def connect(self, retries):
    """
    Args:
        retries: Number of retry attempts
    """
    ...
```

---

## Handling Optional & Union Types

```python
from typing import Optional, Union

@ENVMod.register()
def start(
    host: Optional[str],
    mode: Union[str, None] = None,
):
    """
    Args:
        host: Optional hostname override
        mode: Optional startup mode
    """
    ...
```

---

## Error Behavior Summary

| Condition                  | Result       |
| -------------------------- | ------------ |
| Duplicate param            | `ValueError` |
| Shared param type conflict | `TypeError`  |
| Unsupported type           | `TypeError`  |
| Missing required env       | `ValueError` |

---

## Best Practices

✔ Use type hints everywhere
✔ Write meaningful docstrings
✔ Use explicit `load_args` in libraries
✔ Group related config with `section_name`
✖ Avoid magic auto-loading in public APIs

---

## TL;DR

ENVMod lets you write this:

```python
ENVmod.register()
def __init__(self, host: str, port: int):
    ...
```

And automatically get:

* Documentation
* Type casting
* Defaults
* Validation
* `.env_example`
* `.env` synchronization

All from **one place**.
