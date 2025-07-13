from classmods import suppress_errors

@suppress_errors('exception')
def return_exception() -> bool:
    raise Exception('This is test Error')

@suppress_errors('true')
def return_true() -> bool:
    raise Exception('This is test Error')

@suppress_errors('false')
def return_false() -> bool:
    raise Exception('This is test Error')


def test_return_exception():
    result = return_exception()
    assert isinstance(result, Exception)

def test_true():
    result = return_true()
    assert result is True

def test_false():
    result = return_false()
    assert result is False
