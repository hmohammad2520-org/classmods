## `ConstantAttrib` Descriptor

### Overview

`ConstantAttrib` is a **data descriptor** that enforces **write-once (constant) attributes at the instance level**.

Once a value is assigned:

* It **cannot be reassigned**
* It **cannot be deleted**
* Access before assignment raises an error

This is useful when you want:

* Immutable instance configuration
* Late initialization with safety
* Explicit, self-documenting constants without `@property` boilerplate

---

## Key Characteristics

* Enforced **per instance**
* Allows **exactly one assignment**
* Read-only after initialization
* Works cleanly with static type checkers (Pylance, MyPy)
* Does **not** allow class-level assignment

---

## Basic Usage

```python
from classmods import ConstantAttrib

class MyClass:
    VALUE = ConstantAttrib()

obj = MyClass()
obj.VALUE = 42       # OK
print(obj.VALUE)     # 42

obj.VALUE = 10       # AttributeError
del obj.VALUE        # AttributeError
```

---

## Behavior Summary

| Operation                | Result             |
| ------------------------ | ------------------ |
| First assignment         | Allowed            |
| Second assignment        | ❌ `AttributeError` |
| Access before assignment | ❌ `AttributeError` |
| Deletion                 | ❌ `AttributeError` |
| Class-level access       | Returns descriptor |

---

## Typing & Static Analysis

Because `ConstantAttrib` is generic:

```python
class Config:
    PORT = ConstantAttrib[int]()
```

Type checkers infer:

```python
config.PORT  # int
```

This works without casts or `# type: ignore`.

---

## Advanced Example: Late Initialization

```python
class Service:
    token = ConstantAttrib[str]()

    def initialize(self, token: str) -> None:
        self.token = token
```

```python
svc = Service()
svc.initialize("abc123")
svc.token = "xyz"   # AttributeError
```

---

## Comparison With Alternatives

### vs `@property`

| Feature     | ConstantAttrib | property     |
| ----------- | -------------- | ------------ |
| Write-once  | Yes            | Manual       |
| Boilerplate | Minimal        | High         |
| Typing      | Excellent      | Often tricky |
| Storage     | Automatic      | Manual       |

---

### vs `frozen=True` dataclass

| Feature               | ConstantAttrib | Frozen dataclass |
| --------------------- | -------------- | ---------------- |
| Late init             | Yes            | No               |
| Partial immutability  | Yes            | No               |
| Per-attribute control | Yes            | No               |

---

## Design Philosophy

`ConstantAttrib` is:

* **Explicit**
* **Predictable**
* **Minimal**
* **Safe for public APIs**

It avoids:

* Metaclasses
* Magic mutation
* Runtime patching
* Silent behavior

This makes it ideal for **library code**, **configuration objects**, and **framework internals**.

---

## When to Use

Recommended for:

* Configuration values
* Identifiers
* Runtime-initialized constants
* Public API invariants

Avoid using when:

* Values must change
* Full immutability is required (use frozen dataclasses instead)
