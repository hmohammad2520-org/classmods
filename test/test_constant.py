from classmods import ConstantAttrib

class TestClass:
    test_constant = ConstantAttrib()

    def __init__(self) -> None:
        self.test_constant = 'Random Value'


def test_get_value():
    test = TestClass()
    assert test.test_constant == 'Random Value' 

def test_change():
    try:
        test = TestClass()
        test.test_constant = 'New Value'
        raise Exception('Expected AttrebiuteError exception')
    except AttributeError as e:
        return

def test_delete():
    try:
        test = TestClass()
        del test.test_constant
        raise Exception('Expected AttrebiuteError exception')
    except AttributeError as e:
        return