# MethodMonitor

`MethodMonitor` is a utility class to monitor method calls on Python classes. It supports **instance methods**, **class methods**, and **static methods**, and allows attaching multiple monitors to a single method.

---

## Installation

```python
from classmods import MethodMonitor
```

---

## Overview

* **Purpose**: Trigger custom callables whenever a method is invoked.
* **Features**:

  * Monitor `__init__` or any other method.
  * Supports multiple monitors per method.
  * Works with `@staticmethod`, `@classmethod`, and regular instance methods.
  * Can pass extra `args` and `kwargs` to the monitor callable.
  * Activate, deactivate, or remove monitors at runtime.

---

## Class Signature

```python
class MethodMonitor:
    def __init__(
        self,
        target: Type,
        monitor_callable: Callable[..., None],
        monitor_args: Optional[Tuple] = None,
        monitor_kwargs: Optional[Dict[str, Any]] = None,
        *,
        target_method: str | Callable = "__init__",
        active: bool = True
    )
```

### Parameters

| Parameter          | Type                       | Description                                                                                                            |                                                                                |
| ------------------ | -------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `target`           | `Type`                     | The class to monitor.                                                                                                  |                                                                                |
| `monitor_callable` | `Callable[..., None]`      | Function to call after the method is executed. Signature: `(instance_or_cls_or_none, *monitor_args, **monitor_kwargs)` |                                                                                |
| `monitor_args`     | `Optional[Tuple]`          | Extra positional arguments passed to the monitor callable.                                                             |                                                                                |
| `monitor_kwargs`   | `Optional[Dict[str, Any]]` | Extra keyword arguments passed to the monitor callable.                                                                |                                                                                |
| `target_method`    | `str                       | Callable`                                                                                                              | Name of the method to monitor, or the method itself. Defaults to `'__init__'`. |
| `active`           | `bool`                     | If True, the monitor is active immediately.                                                                            |                                                                                |

---

## Usage Examples

### 1. Monitor an instance method

```python
class MyClass:
    def greet(self, name):
        print(f"Hello {name}")

def monitor_fn(instance, *args, **kwargs):
    print(f"Monitor: Called {instance} with args={args}, kwargs={kwargs}")

monitor = MethodMonitor(
    MyClass,
    monitor_fn,
    monitor_args=("ExtraArg",),
    target_method=MyClass.greet,
)

obj = MyClass()
obj.greet("Alice")  
# Output:
# Hello Alice
# Monitor: Called <MyClass instance> with args=('ExtraArg',), kwargs={}
```

---

### 2. Monitor a class method

```python
class MyClass:
    @classmethod
    def announce(cls, message):
        print(f"{cls.__name__}: {message}")

def monitor_cls(cls, *args, **kwargs):
    print(f"Monitor: class={cls}, args={args}, kwargs={kwargs}")

monitor = MethodMonitor(
    MyClass,
    monitor_cls,
    monitor_args=("ExtraArg",),
    target_method=MyClass.announce,
    )

MyClass.announce("Hello")  
# Output:
# MyClass: Hello
# Monitor: class=<class 'MyClass'>, args=('ExtraArg',), kwargs={}
```

---

### 3. Monitor a static method

```python
class MyClass:
    @staticmethod
    def static_print(msg):
        print(msg)

def monitor_static(_none, *args, **kwargs):
    print(f"Monitor: args={args}, kwargs={kwargs}")

monitor = MethodMonitor(MyClass, monitor_static, monitor_args=("ExtraArg",), target_method="static_print")

MyClass.static_print("Hello")  
# Output:
# Hello
# Monitor: args=('ExtraArg',), kwargs={}
```

> **Note:** For static methods, the first argument passed to the monitor is always `None`.

---

### 4. Activating / Deactivating / Removing Monitors

```python
monitor.deactivate()  # Monitor will not trigger
monitor.activate()    # Monitor triggers again
monitor.remove()      # Monitor is removed and original method restored
```

---

### 5. Multiple Monitors

```python
def monitor_a(instance, *args, **kwargs):
    print("Monitor A triggered")

def monitor_b(instance, *args, **kwargs):
    print("Monitor B triggered")

MethodMonitor(MyClass, monitor_a, target_method=MyClass.greet)
MethodMonitor(MyClass, monitor_b, target_methodMyClass.greet)

obj = MyClass()
obj.greet("Bob")
# Output:
# Hello Bob
# Monitor A triggered
# Monitor B triggered
```

---

## Best Practices

* Use `target_method` as a string or the actual method reference.
* Static methods always receive `None` as the first argument in the monitor.
* Class methods receive `cls` as the first argument.
* Avoid monitoring methods that return large or sensitive data for performance and security reasons.

---

### Notes

* `MethodMonitor` modifies the class method dynamically (monkey-patching).
* Removing all monitors restores the original method.
* Supports any callable signature in `monitor_callable`, as long as it accepts the first argument (instance/cls/None).