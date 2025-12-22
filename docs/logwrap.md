# `logwrap` Decorator

A flexible, zero-boilerplate logging decorator built on Python’s standard `logging` module.

`logwrap` allows you to log:

* **Before** a function is called
* **After** a function returns
* **When an exception occurs**

All without modifying the function body.

---

## Why `logwrap`?

Logging function behavior usually leads to:

* Repetitive boilerplate
* Inconsistent log formats
* Hard-to-maintain debug prints
* Manual try/except logging blocks

`logwrap` solves this by providing:

* Declarative logging
* Centralized formatting
* Dynamic templating
* Full compatibility with your existing logging configuration

---

## Key Features

* Works with **any function or method**
* Uses **standard `logging`** (no custom logger required)
* Supports **dynamic message templating**
* Fully configurable per stage (before / after / exception)
* Safe defaults, no crashes on invalid config
* Zero runtime overhead when disabled

---

## Installation

No extra dependencies required.

```python
from classmods import logwrap
```

---

## Supported Log Levels

`logwrap` uses the standard logging levels:

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

Invalid levels automatically fall back to a safe default.

---

## Template Variables

Log messages support **string templating** using the following variables:

| Variable   | Description                          |
| ---------- | ------------------------------------ |
| `{func}`   | Function name                        |
| `{args}`   | Positional arguments (tuple)         |
| `{kwargs}` | Keyword arguments (dict)             |
| `{result}` | Return value (after call only)       |
| `{e}`      | Exception object (on exception only) |

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

## Using Only One Stage

You can enable logging for **only one phase**:

```python
@logwrap(after=True)
def compute():
    return 42
```

---

## Skipping Logging Explicitly

If an option is set to a **negative value**, logging for that stage is skipped:

```python
@logwrap(before=False, after=True)
def silent_start():
    return "Done"
```

---

## Default Behaviors

If `True` is passed, the following defaults are used:

| Stage        | Level | Message                                  |
| ------------ | ----- | ---------------------------------------- |
| before       | DEBUG | `Calling {func} - kwargs={kwargs}`       |
| after        | INFO  | `Function {func} ended. result={result}` |
| on_exception | ERROR | `Error in {func}: {e}`                   |

---

## Advanced Example: Debugging Business Logic

```python
@logwrap(
    before=('DEBUG', 'Entering {func} with {kwargs}'),
    after=('DEBUG', '{func} returned {result}'),
    on_exception=('ERROR', '{func} failed: {e}')
)
def calculate_discount(price: float, percent: float):
    if percent > 100:
        raise ValueError("Invalid discount")
    return price * (1 - percent / 100)
```

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

## When NOT to Use `logwrap`

* Ultra-hot performance paths (tight loops)
* Functions called thousands of times per second
* When logging is globally disabled anyway

In those cases, traditional inline logging may be more efficient.

---

## Design Philosophy

* **Explicit is better than implicit**
* **Logging should not change program behavior**
* **Configuration over repetition**
* **Runtime-safe by default**

`logwrap` is intentionally:

* Non-invasive
* Fail-safe
* IDE-friendly
* Compatible with any logging setup

---

## Summary

`logwrap` is ideal when you want:

* Clean function bodies
* Consistent logs
* Powerful debugging
* Zero boilerplate

It scales from small scripts to large production systems without getting in your way.