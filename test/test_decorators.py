from classmods import (
    return_exception_on_error,
    return_true_on_error,
    return_false_on_error,
)

@return_exception_on_error
def exception():
    raise Exception('This is test Error')

@return_true_on_error
def true():
    raise Exception('This is test Error')

@return_false_on_error
def false():
    raise Exception('This is test Error')


def test_return_exception():
    result = exception()
    assert isinstance(result, Exception)

def test_true():
    result = true()
    assert result is True

def test_false():
    result = false()
    assert result is False
