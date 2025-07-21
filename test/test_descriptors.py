from classmods import ConstantAttrib, RemoteAttrib

_remote_item = 1

class MyClass:
    _constant = ConstantAttrib()

    def __init__(self) -> None:
        self._constant = 1

    def change_constant(self):
        # This should raise
        self._constant = 2


    def _get_remote(self):
        global _remote_item
        return _remote_item

    def _set_remote(self, value):
        global _remote_item
        _remote_item = value

    def _del_remote(self):
        global _remote_item
        del _remote_item

    _remote = RemoteAttrib(
        _get_remote, _set_remote, _del_remote,
    )


def test_constant_attrib():
    my_instance = MyClass()
    assert my_instance._constant == 1, "Expected 1"

    # Testing inside method changes
    try: my_instance.change_constant()
    except AttributeError: ...
    else: assert False, "Expected AttributeError"

    # Testing outside method changes
    try: my_instance._constant = 2
    except AttributeError: ...
    else: assert False, "Expected AttributeError"

def test_remote_attrib():
    my_instance = MyClass()
    # Get
    assert my_instance._remote == 1, "Expected 1"

    # Set
    my_instance._remote = 2
    assert my_instance._remote == 2, "Expected 2"

    # Del
    del my_instance._remote
    try: 
        global _remote_item
        _remote_item  # type: ignore
    except NameError: ...
    else: assert False, "Expected AttributeError"