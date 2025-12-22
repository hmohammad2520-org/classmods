from classmods import MethodMonitor


class CallLog(list):
    """Helper to store monitor calls explicitly."""
    def record(self, value):
        self.append(value)


class MyClass:
    def __init__(self, name):
        self.name = name

    def my_method(self, x=1):
        return x * 2

    @classmethod
    def class_method(cls):
        return cls.__name__

    @staticmethod
    def static_method():
        return "static"

    def objects_test_callable(self):
        return True

    def __str__(self):
        return f"<{self.name}>"


def monitor_callable(obj, log: CallLog, *args, **kwargs):
    if obj is not None:
        assert hasattr(obj, "objects_test_callable")

        if obj is not MyClass:
            assert obj.objects_test_callable() is True

    log.record({
        "obj": obj,
        "args": args,
        "kwargs": kwargs,
    })


def test_init_monitor():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log,),
    )

    obj = MyClass("InitTest")

    assert len(call_log) == 1
    entry = call_log[0]
    assert entry["obj"] is obj
    assert entry["args"] == ()
    assert entry["kwargs"] == {}

    monitor.remove()


def test_activation_toggle():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log,),
    )

    monitor.deactivate()
    MyClass("inactive")
    assert call_log == []

    monitor.activate()
    obj = MyClass("active")
    assert len(call_log) == 1
    assert call_log[0]["obj"] is obj

    monitor.remove()


def test_remove_is_idempotent():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log,),
    )

    monitor.remove()
    monitor.remove()  # must not raise
    MyClass("no-monitor")
    assert call_log == []


def test_instance_method_args_kwargs():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log, "A", "B"),
        monitor_kwargs={"x": 10},
        target_method="my_method",
    )

    obj = MyClass("MethodTest")
    result = obj.my_method(5)

    assert result == 10
    assert len(call_log) == 1
    entry = call_log[0]
    assert entry["obj"] is obj
    assert entry["args"] == ("A", "B")
    assert entry["kwargs"] == {"x": 10}

    monitor.remove()


def test_class_method_monitor():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log,),
        target_method="class_method",
    )

    result = MyClass.class_method()
    assert result == "MyClass"

    assert len(call_log) == 1
    entry = call_log[0]
    assert entry["obj"] is MyClass  # cls is passed
    assert entry["args"] == ()
    assert entry["kwargs"] == {}

    monitor.remove()


def test_static_method_monitor():
    call_log = CallLog()
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=(call_log,),
        target_method="static_method",
    )

    result = MyClass.static_method()
    assert result == "static"

    assert len(call_log) == 1
    entry = call_log[0]
    assert entry["obj"] is None
    assert entry["args"] == ()
    assert entry["kwargs"] == {}

    monitor.remove()


def test_multiple_monitors_order():
    call_log = CallLog()
    monitor1 = MethodMonitor(
        MyClass,
        lambda obj, log: log.record("first"),
        monitor_args=(call_log,),
        target_method="my_method",
    )

    monitor2 = MethodMonitor(
        MyClass,
        lambda obj, log: log.record("second"),
        monitor_args=(call_log,),
        target_method="my_method",
    )

    MyClass("X").my_method()
    assert call_log == ["first", "second"]

    monitor1.remove()
    monitor2.remove()


def test_original_method_restored():
    original = MyClass.my_method

    monitor = MethodMonitor(
        MyClass,
        lambda *_: None,
        target_method="my_method",
    )

    assert MyClass.my_method is not original

    monitor.remove()
    assert MyClass.my_method is original
