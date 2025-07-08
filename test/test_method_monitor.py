from typing import Any, Callable
from classmods import MethodMonitor

# a list to get results
test_list = []

class MyClass:
    def __init__(self, name):
        self.name = name
        print('Init')

    def my_method(self):
        print('My Method')
    
    @classmethod
    def class_method(cls):
        print(cls.__name__)

    @staticmethod
    def static_method():
        print('Static Method')
    
    def __str__(self):
        return f'<{self.name}>'

def monitor_callable(obj: object, *args, **kwargs) -> None:
    test_list.append(f'Monitor Called on: {obj.__class__.__name__} -- args={args}, kwargs={kwargs}')

def check_list():
    try: return test_list.pop()
    except IndexError: return
    finally: test_list.clear()

def test_init():
    monitor = MethodMonitor(
        MyClass, 
        monitor_callable,
    )
    MyClass('Init')
    assert test_list.pop(0)
    monitor.remove()

def test_remove():
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
    )
    monitor.remove()
    MyClass('Remove')
    assert not check_list()
    monitor.remove() # Reuse Must not Raise Errors

def test_activation():
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
    )
    monitor.deactivate()
    MyClass('Deactive')
    assert not check_list()

    monitor.activate()
    MyClass('Activate')
    assert check_list()

    monitor.remove()

def test_method_with_args_and_kwargs():
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        monitor_args=('Arg1','Arg2'),
        monitor_kwargs={'kwarg1': 1, 'kwarg2': 2},
        target_method=MyClass.my_method.__name__,
    )
    MyClass('Method').my_method()
    assert check_list()
    monitor.remove()

def test_class_method():
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        target_method=MyClass.class_method.__name__,
    )
    MyClass.class_method()
    assert check_list()
    monitor.remove()

def test_static_method():
    monitor = MethodMonitor(
        MyClass,
        monitor_callable,
        target_method=MyClass.static_method.__name__,
    )
    MyClass.static_method()
    assert check_list()
    monitor.remove()