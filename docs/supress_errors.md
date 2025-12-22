## `suppress_errors` Decorator

### Overview

`suppress_errors` is a decorator factory that wraps a function and **suppresses runtime exceptions**, returning a predefined fallback value instead of raising the error.

It is designed for:

* Safe execution paths
* Optional or best-effort operations
* Library code where failures should not crash the caller
* Situations where returning a sentinel value is preferable to exception handling

The decorator supports **type-aware fallbacks** using `@overload` to preserve static typing as much as possible.

---

## Parameters

### `fallback`

Determines what the wrapped function returns when an exception occurs.

Supported behaviors:

| `fallback` value    | Behavior on exception                     |
| ------------------- | ----------------------------------------- |
| `Exception` (class) | Returns the **caught exception instance** |
| Any other value     | Returns that value                        |

**Important notes:**

* Only exceptions derived from `Exception` are caught
* `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` are **not suppressed**

---

## Behavior Details

* Exceptions are **silently suppressed**
* No logging or re-raising is performed
* The decorator does **not modify arguments or signatures**
* The function is always executed exactly once

---

## Examples

### Example 1: Return the exception object

```python
@suppress_errors(Exception)
def risky_division() -> float:
    return 1 / 0

result = risky_division()

assert isinstance(result, ZeroDivisionError)
```

Use this when:

* You want to inspect the error
* You want to propagate error information without raising

---

### Example 2: Return a sentinel value

```python
@suppress_errors(False)
def read_flag() -> bool:
    raise ValueError("invalid state")

result = read_flag()
assert result is False
```

Use this when:

* A default value makes sense
* Failure should be treated as “no result”

---

### Example 3: Safe optional computation

```python
@suppress_errors(None)
def parse_int(value: str) -> int:
    return int(value)

parse_int("42")     # 42
parse_int("oops")   # None
```

---

## Typing Behavior

Thanks to `@overload`, static type checkers infer return types correctly:

```python
@suppress_errors(None)
def f() -> int:
    ...

# inferred return type: int | None
```

```python
@suppress_errors(Exception)
def g() -> int:
    ...

# inferred return type: int | Exception
```

This makes the decorator **type-safe and IDE-friendly**.

---

## What This Decorator Does *Not* Do

* Does **not** log errors
* Does **not** retry execution
* Does **not** catch BaseException
* Does **not** modify function arguments
* Does **not** hide programmer mistakes silently unless you explicitly choose to

---

## When to Use

Recommended use cases:

* Optional integrations
* Configuration parsing
* Non-critical I/O
* Plugin hooks
* Defensive library APIs

Avoid using it when:

* Errors must be visible
* Silent failures are dangerous
* Debugging correctness matters more than resilience

---

## Design Philosophy

`suppress_errors` is intentionally **explicit and minimal**:

* You must consciously choose the fallback behavior
* No magic, no hidden state
* Predictable and composable