# `RemoteAttrib` Descriptor

### Remote-backed attributes made simple

`RemoteAttrib` is a **descriptor** that allows object attributes to transparently map to **remote operations** such as API calls, RPC methods, or external services.

It lets you **read, write, and delete attributes** while automatically calling the appropriate remote logic — with optional caching.

---

## Why `RemoteAttrib`?

Using `@property` for remote data quickly becomes painful:

* No argument forwarding
* No caching
* Large, repetitive code
* Hard to compose or reuse

`RemoteAttrib` solves this by turning **remote calls into attributes**.

---

## What You Get

* Attribute-style access (`obj.value`)
* Remote getter / setter / deleter
* Optional per-instance caching (TTL-based)
* Lambda-friendly API
* Strong typing (`Generic[T]`)
* Clean, declarative class definitions

---

## Minimal Example (Lambda-based)

```python
class User:
    def __init__(self, user_id: int):
        self.id = user_id

    name = RemoteAttrib[str](
        getter=lambda s: api_get(s.id, "name"),
        setter=lambda s, v: api_set(s.id, "name", v),
        cache_timeout=5,
    )
```

```python
u = User(42)

print(u.name)        # Remote fetch
print(u.name)        # Cached
u.name = "Alice"     # Remote update
```

---

## Read-Only Attribute

```python
status = RemoteAttrib[str](
    getter=lambda s: api_get(s.id, "status")
)
```

```python
print(user.status)   # OK
user.status = "x"    # AttributeError
```

---

## Write-Only Attribute

```python
trigger = RemoteAttrib[None](
    setter=lambda s, v: api_trigger(s.id, v)
)
```

```python
user.trigger = "refresh"
print(user.trigger)  # AttributeError
```

---

## Computed Remote Attribute

No setter, no remote storage — just composition:

```python
fullname = RemoteAttrib[str](
    getter=lambda s: f"{s.first_name} {s.last_name}"
)
```

This behaves like a compact, reusable `@property`.

---

## Caching Behavior

Each instance has an internal cache:

```python
instance._remote_attrib_cache
```

### Cache Rules

* Cache is **per instance**
* Cache entry format:

  ```python
  { "attr_name": (value, timestamp) }
  ```
* Automatically expires after `cache_timeout`
* Automatically invalidated on:

  * `__set__`
  * `__delete__`

---

## Argument Forwarding

Need to pass parameters to remote calls?

```python
email = RemoteAttrib[str](
    getter=lambda s, field: api_get(s.id, field),
    setter=lambda s, v, field: api_set(s.id, field, v),
    getter_args=("email",),
    setter_args=("email",),
)
```

---

## Deletion Support

```python
token = RemoteAttrib[str](
    getter=lambda s: api_get(s.id, "token"),
    deleter=lambda s: api_delete(s.id, "token"),
)
```

```python
del user.token   # Remote delete + cache clear
```

---

## Error Semantics

Errors are **explicit and predictable**:

| Operation  | Error            |
| ---------- | ---------------- |
| No getter  | `AttributeError` |
| No setter  | `AttributeError` |
| No deleter | `AttributeError` |

No silent failures.

---

## Class-Level Access

```python
User.name  # -> RemoteAttrib[str]
```

Useful for:

* Introspection
* Documentation tools
* Framework integration

---

## Typing & Tooling

Because `RemoteAttrib` is generic:

```python
name = RemoteAttrib[str](...)
```

Type checkers infer:

```python
user.name  # str
```

Works correctly with:

* Pyright
* Pylance
* MyPy

---

## When Should You Use This?

**Use `RemoteAttrib` when:**

* Attributes map to remote systems
* Reads are expensive
* Writes have side effects
* Caching matters
* Clean APIs matter

**Don’t use it when:**

* Data is purely local
* No side effects exist
* Simpler access is sufficient

---

## Design Philosophy

* Explicit over magical
* Descriptor-based (no metaclasses)
* Instance-safe caching
* No global state
* Library-friendly defaults

---

## Summary

`RemoteAttrib` gives you:

* `@property` ergonomics
* Remote power
* Caching
* Type safety
* Cleaner classes

All without boilerplate.