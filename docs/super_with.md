# SuperWith — The CEO of Context Managers

`SuperWith` is a **powerful context manager utility** that allows you to combine multiple context managers into a single `with` or `async with` statement. It makes code cleaner, safer, and more readable, especially when you have deeply nested contexts.

It supports:

* Both **sync and async context managers** (mutually exclusive in one usage)
* **Tuple unpacking** of returned values
* Zero, single, or multiple contexts
* Proper **exception propagation**

---

## Features

* **Single `with` for multiple contexts**
  Avoid nested `with` statements like:

  ```python
  with Connection():
      with Session():
          with Lock():
              do_work(conn, sess, lock)
  ```

  Use:

  ```python
  with SuperWith(Connection(), Session(), Lock()) as (conn, sess, lock):
      do_work(conn, sess, lock)
  ```

* **Async context support**
  Fully supports async contexts:

  ```python
  async with SuperWith(AsyncConn(), AsyncSession()) as (conn, sess):
      await do_work(conn, sess)
  ```

* **Safe type enforcement**
  Ensures only **sync contexts** are used in `with` and only **async contexts** in `async with`. Mixed usage raises a `TypeError`.

* **Automatic tuple unpacking**

  * Single context returns the object itself
  * Multiple contexts return a tuple
  * Zero contexts return `()`

* **Proper exception handling**
  Context managers always exit in **reverse order**, even if exceptions occur.

---

## Usage

### Sync Context Managers

```python
from classmods._super_with import SuperWith
from contextlib import ExitStack

class Connection:
    def __enter__(self):
        print("Conn enter")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Conn exit")

class Session:
    def __enter__(self):
        print("Session enter")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Session exit")

conn = Connection()
sess = Session()

with SuperWith(conn, sess) as (c, s):
    print("Working with", c, s)

# Output:
# Conn enter
# Session enter
# Working with <Connection> <Session>
# Session exit
# Conn exit
```

### Async Context Managers

```python
import asyncio
from contextlib import AbstractAsyncContextManager

class AsyncConn(AbstractAsyncContextManager):
    async def __aenter__(self):
        print("AsyncConn enter")
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("AsyncConn exit")

async def main():
    async with SuperWith(AsyncConn()) as conn:
        print("Working async with", conn)

asyncio.run(main())

# Output:
# AsyncConn enter
# Working async with <AsyncConn>
# AsyncConn exit
```

### Zero Contexts

```python
with SuperWith() as val:
    print(val)  # ()
```

### Single Context

```python
with SuperWith(conn) as c:
    print(c)  # <Connection>
```

---

## Best Practices

1. **Do not mix sync and async contexts** in the same `SuperWith` call.
2. **Use unpacking** for multiple contexts to keep code readable.
3. **Always handle exceptions** in your code — `SuperWith` ensures contexts exit correctly.
4. **Zero context usage** is allowed for dynamic cases:

```python
ctxs = []
with SuperWith(*ctxs) as val:
    ...
```

---

## Why “CEO” of Context Managers?

* Simplifies complex nested `with` statements
* Handles multiple contexts elegantly
* Makes both **sync and async workflows cleaner**
* Improves readability and maintainability in large projects