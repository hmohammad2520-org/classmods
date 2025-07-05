import logging
from functools import wraps
from typing import Any, Callable


def return_exception_on_error(func) -> Callable[[Any], Any]:
    """Decorator to return an exception on error instead of raising it."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: result = func(*args, **kwargs)
        except Exception as e: return e
        return result
    return wrapper

def return_true_on_error(func) -> Callable[[Any], Any]:
    """Decorator used to return True when an error occurs."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: result = func(*args, **kwargs)
        except: return True
        return result
    return wrapper

def return_false_on_error(func) -> Callable[[Any], Any]:
    """Decorator used to return False when an error occurs."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: result = func(*args, **kwargs)
        except: return False
        return result
    return wrapper