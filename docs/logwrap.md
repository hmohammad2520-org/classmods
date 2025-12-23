# `logwrap` Decorator

A flexible, zero-boilerplate logging decorator built on Python’s standard `logging` module.

`logwrap` allows you to log:

* **Before** a function is called
* **After** a function returns
* **When an exception occurs**

All **without modifying the function body**.

---

## Why `logwrap`?

Logging function behavior often leads to:

* Repetitive boilerplate
* Inconsistent log formats
* Scattered `print()` statements
* Manual `try/except` logging blocks

`logwrap` solves this by providing:

* Declarative logging
* Centralized formatting
* Dynamic message templating
* Full compatibility with existing `logging` configuration

---

## Key Features

* Works with **any function or method**
* Uses **standard `logging`**
* Supports **sync and async functions**
* Dynamic message templating
* Per-stage configuration (before / after / exception)
* Optional conditional logging via predicates
* Zero overhead when a stage is disabled

---

## Installation

No extra dependencies required.

```python
from classmods import logwrap
```

---

## Supported Log Levels

`logwrap` supports all standard logging levels:

```python
LOG_LEVEL = [
    'CRITICAL',
    'ERROR',
    'WARNING',
    'INFO',
    'DEBUG',
    'NOTSET',
]
```

You may also pass integer levels (e.g. `logging.DEBUG`).

Invalid levels automatically fall back to a safe default.

---

## Template Variables

Log messages use Python string formatting with the following variables:

| Variable   | Description                             |
| ---------- | --------------------------------------- |
| `{func}`   | Function name                           |
| `{args}`   | Positional arguments (tuple)            |
| `{kwargs}` | Keyword arguments (dict)                |
| `{result}` | Return value (after stage only)         |
| `{e}`      | Exception object (exception stage only) |

---

## Basic Usage

### Log Before and After a Function Call

```python
@logwrap(before=True, after=True)
def greet(name: str):
    return f"Hello {name}"

greet("Mohammad")
```

**Logs:**

```text
DEBUG - Calling greet - kwargs={'name': 'Mohammad'}
INFO  - Function greet ended. result=Hello Mohammad
```

---

## Explicit Message and Level

```python
@logwrap(
    before=('INFO', 'Starting {func} with args={args}'),
    after=('INFO', '{func} completed successfully')
)
def process(data):
    return len(data)
```

---

## Logging Exceptions

```python
@logwrap(on_exception=True)
def explode():
    raise RuntimeError("Boom")
```

**Logs:**

```text
ERROR - Error in explode: Boom
```

---

## Custom Exception Message

```python
@logwrap(
    on_exception=('CRITICAL', 'Fatal error in {func}: {e}')
)
def critical_section():
    raise ValueError("Invalid state")
```

---

## Enabling Only One Stage

You can enable logging for **only one phase**:

```python
@logwrap(after=True)
def compute():
    return 42
```

---

## Skipping Logging Explicitly

If an option is set to a *negative value*, that stage is skipped:

```python
@logwrap(before=False, after=True)
def silent_start():
    return "Done"
```

Supported skip values:

* `False`
* `None`

---

## Default Behaviors

Passing `True` uses the following defaults:

| Stage        | Level | Message                                  |
| ------------ | ----- | ---------------------------------------- |
| before       | DEBUG | `Calling {func} - kwargs={kwargs}`       |
| after        | INFO  | `Function {func} ended. result={result}` |
| on_exception | ERROR | `Error in {func}: {e}`                   |

---

## Conditional Logging (Predicates)

You may provide a predicate function to conditionally log:

```python
def only_large_inputs(ctx):
    return ctx["kwargs"].get("size", 0) > 100

@logwrap(
    before=('DEBUG', 'Large input detected', only_large_inputs)
)
def process(size: int):
    ...
```

Predicate signature:

```python
Callable[[dict[str, Any]], bool]
```

The predicate receives the formatting context.

---

## Async Function Support

`logwrap` automatically detects async functions:

```python
@logwrap(before=True, after=True)
async def fetch_data():
    ...
```

No configuration changes required.

---

## Logging Methods

`logwrap` works seamlessly with class methods:

```python
class Service:
    @logwrap(before=True, after=True)
    def start(self, port: int):
        return f"Started on {port}"
```

---

## Custom Logger Selection

You may specify a logger explicitly:

```python
@logwrap(before=True, logger="myapp.service")
def run():
    ...
```

Accepted values:

* `None` (default: module logger)
* `str` (logger name)
* `logging.Logger` instance

---

## Timing / Performance Logging

`logwrap` can optionally log the **execution time** of a function.

* Enable it by passing the `timing` argument.
* Timing logs appear **after function execution** and have their own formatting.
* Works for both sync and async functions.

### Example

```python
@logwrap(before=True, after=True, timing=True)
def compute_heavy(x: int):
    total = sum(i * i for i in range(x))
    return total

compute_heavy(10000)
```

**Logs:**

```text
DEBUG - Calling compute_heavy - kwargs={'x': 10000}
INFO  - Function compute_heavy ended. result=333283335000
DEBUG - Function compute_heavy executed in 0.005432s
```

* `timing` uses `DEBUG` by default, but you can customize it:

```python
@logwrap(timing=('INFO', '{func} took {duration:.4f}s'))
def fast_task():
    ...
```

* `{duration}` is automatically available in the template and represents **elapsed time in seconds**.
* Timing logging is optional. If not enabled (`timing=None`), no timing data is collected.
* Timing logs are separate from `after` logs to keep **function result logs and performance logs distinct**.
* Works with both **sync** and **async** functions.

---

## When NOT to Use `logwrap`

* Ultra-hot code paths
* Tight loops
* Functions called thousands of times per second
* When logging is globally disabled anyway

In those cases, inline logging may be more efficient.

---

## Design Philosophy

* Explicit over implicit
* Logging must not change program behavior
* Configuration over repetition
* Runtime-safe by default

`logwrap` is intentionally:

* Non-invasive
* Fail-safe
* IDE-friendly
* Compatible with any logging setup

---

## Summary

`logwrap` is ideal when you want:

* Clean function bodies
* Consistent, structured logs
* Powerful debugging hooks
* Zero boilerplate

It scales from small scripts to large production systems without getting in your way.