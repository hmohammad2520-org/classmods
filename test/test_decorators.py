import logging
import pytest
from classmods import logwrap, suppress_errors
import asyncio

# -----------------------------
# suppress_errors tests
# -----------------------------

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


def test_suppress_errors_behavior():
    result = return_exception()
    assert isinstance(result, Exception), 'Expected Exception'

    result = return_true()
    assert result is True, f"Expected True, got {result}"

    result = return_false()
    assert result is False, f"Expected False, got {result}"

    result = return_any()
    assert result == 'Failed', f"Expected 'Failed', got {result}"


# -----------------------------
# logwrap tests
# -----------------------------

def test_basic_logging(caplog):
    @logwrap(before=True, after=True)
    def greet(name):
        return f"Hello {name}"

    with caplog.at_level(logging.DEBUG):
        result = greet("Mohammad")

    assert result == "Hello Mohammad"
    # Check that logs were emitted
    assert any("Calling greet" in r.message for r in caplog.records)
    assert any("Function greet ended" in r.message for r in caplog.records)


def test_custom_level_logging(caplog):
    @logwrap(before=('INFO', 'Function starting'), after=('INFO', 'Function ended'))
    def my_func(my_arg, my_kwarg=None):
        return my_arg + str(my_kwarg)

    with caplog.at_level(logging.INFO):
        result = my_func("hello", my_kwarg=123)

    assert result == "hello123"
    messages = [r.message for r in caplog.records]
    assert "Function starting" in messages
    assert "Function ended" in messages

def test_exception_logging(caplog):
    @logwrap(on_exception=True)
    def explode():
        raise RuntimeError("Boom!")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError):
            explode()

    # Ensure exception was logged
    assert any("Error in explode" in r.message for r in caplog.records)
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_timing_logging(caplog):
    @logwrap(before=True, after=True, timing=True)
    def compute_heavy(x):
        total = sum(i * i for i in range(x))
        return total

    with caplog.at_level(logging.DEBUG):
        result = compute_heavy(1000)

    # Ensure timing message was logged
    timing_logs = [r for r in caplog.records if "executed in" in r.message]
    assert len(timing_logs) == 1
    # Ensure result is correct
    assert result == sum(i * i for i in range(1000))


@pytest.mark.asyncio
async def test_async_function_logging(caplog):
    @logwrap(before=True, after=True, timing=True)
    async def async_task(x):
        await asyncio.sleep(0.01)
        return x * 2

    with caplog.at_level(logging.DEBUG):
        result = await async_task(5)

    # Ensure logs captured
    messages = [r.message for r in caplog.records]
    assert any("Calling async_task" in m for m in messages)
    assert any("Function async_task ended" in m for m in messages)
    assert any("executed in" in m for m in messages)
    assert result == 10


def test_conditional_logging(caplog):
    def only_large_inputs(ctx):
        return ctx['kwargs'].get('size', 0) > 100

    @logwrap(before=('DEBUG', 'Large input detected', only_large_inputs))
    def process(size: int):
        return size

    with caplog.at_level(logging.DEBUG):
        process(50)   # should not log
        process(150)  # should log

    messages = [r.message for r in caplog.records]
    assert any("Large input detected" in m for m in messages)
    assert all("Large input detected" not in m for m in messages if "50" in m)


def test_logger_selection(caplog):
    logger_name = "custom.logger"

    @logwrap(before=True, after=True, logger=logger_name)
    def test_func():
        return 42

    with caplog.at_level(logging.DEBUG):
        test_func()

    assert any(r.name == logger_name for r in caplog.records)
