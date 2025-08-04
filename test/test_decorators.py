from classmods import logwrap, suppress_errors

@suppress_errors(Exception)
def return_exception():
    raise Exception('This is test Error')

@suppress_errors(True)
def return_true():
    raise Exception('This is test Error')

@suppress_errors(False)
def return_false():
    raise Exception('This is test Error')

@suppress_errors('Failed')
def return_any():
    raise Exception('This is test Error')

def test_supress_error():
    result = return_exception()
    assert isinstance(result, Exception), 'Expected Exception'

    result = return_true()
    assert result is True, f"Expected True, got {result}"

    result = return_false()
    assert result is False, f"Expected False, got {result}"

    result = return_any()
    assert result == 'Failed', f"Expected 'Failed', got {result}"

def test_standard_use():
    # Example with defaults.
    @logwrap(before='Starting', after='Ended')
    def my_new_func():
        ...
    my_new_func()

def test_with_custom_leveling():
    # Example with Custom Levels
    @logwrap(before=('INFO', 'Function starting'), after=('INFO', 'Function ended'))
    def my_func(my_arg, my_kwarg=None):
        ...
    my_func('hello', my_kwarg=123) # calling the function
