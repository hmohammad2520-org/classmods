from classmods import logwrap

def test_standard_use():
    # Example with defaults.
    @logwrap(before='Starting', after='Ended')
    def my_new_func():
        ...
    my_new_func()

def test_with_custom_leveling():
    # Example with Custom Levels
    @logwrap(before=('INFO', 'Function starting'), after=('INFO', 'Function ended'), show_args='DEBUG')
    def my_func(my_arg, my_kwarg=None):
        ...
    my_func('hello', my_kwarg=123) # calling the function
