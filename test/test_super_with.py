import asyncio
import pytest
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from classmods import SuperWith


# -------------------------------
# Helper context managers for testing
# -------------------------------

class DummySync(AbstractContextManager):
    def __init__(self, name):
        self.name = name
        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        return self.name

    def __exit__(self, exc_type, exc_val, tb):
        self.exited = True


class DummyAsync(AbstractAsyncContextManager):
    def __init__(self, name):
        self.name = name
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self.name

    async def __aexit__(self, exc_type, exc_val, tb):
        self.exited = True


# -------------------------------
# Sync tests
# -------------------------------

def test_sync_single_context():
    ctx = DummySync("x")
    with SuperWith(ctx) as val:
        assert val == "x"
        assert ctx.entered is True
        assert ctx.exited is False
    assert ctx.exited is True


def test_sync_multiple_contexts():
    ctx1 = DummySync("a")
    ctx2 = DummySync("b")
    with SuperWith(ctx1, ctx2) as (v1, v2):
        assert v1 == "a"
        assert v2 == "b"
        assert ctx1.entered and ctx2.entered
        assert not (ctx1.exited or ctx2.exited)
    assert ctx1.exited and ctx2.exited


def test_sync_zero_contexts():
    with SuperWith() as val:
        assert val == ()


def test_sync_exception_propagation():
    ctx1 = DummySync("a")
    ctx2 = DummySync("b")
    with pytest.raises(ValueError):
        with SuperWith(ctx1, ctx2):
            raise ValueError("oops")
    # contexts should still exit
    assert ctx1.exited and ctx2.exited


# -------------------------------
# Async tests
# -------------------------------

@pytest.mark.asyncio
async def test_async_single_context():
    ctx = DummyAsync("x")
    async with SuperWith(ctx) as val:
        assert val == "x"
        assert ctx.entered and not ctx.exited
    assert ctx.exited


@pytest.mark.asyncio
async def test_async_multiple_contexts():
    ctx1 = DummyAsync("a")
    ctx2 = DummyAsync("b")
    async with SuperWith(ctx1, ctx2) as (v1, v2):
        assert v1 == "a"
        assert v2 == "b"
        assert ctx1.entered and ctx2.entered
        assert not (ctx1.exited or ctx2.exited)
    assert ctx1.exited and ctx2.exited


@pytest.mark.asyncio
async def test_async_zero_contexts():
    async with SuperWith() as val:
        assert val == ()


@pytest.mark.asyncio
async def test_async_exception_propagation():
    ctx1 = DummyAsync("a")
    ctx2 = DummyAsync("b")
    with pytest.raises(ValueError):
        async with SuperWith(ctx1, ctx2):
            raise ValueError("oops")
    assert ctx1.exited and ctx2.exited


# -------------------------------
# Mixed-mode tests
# -------------------------------

def test_sync_fails_on_async_context():
    async_ctx = DummyAsync("x")
    with pytest.raises(TypeError):
        with SuperWith(async_ctx):
            pass


@pytest.mark.asyncio
async def test_async_fails_on_sync_context():
    sync_ctx = DummySync("x")
    with pytest.raises(TypeError):
        async with SuperWith(sync_ctx):
            pass
