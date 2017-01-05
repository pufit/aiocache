import pytest
import asyncio

from unittest.mock import MagicMock

from aiocache.backends import SimpleMemoryBackend


@pytest.fixture
def memory(event_loop, mocker):
    SimpleMemoryBackend._handlers = {}
    SimpleMemoryBackend._cache = {}
    mocker.spy(SimpleMemoryBackend, "_cache")
    return SimpleMemoryBackend()


class TestSimpleMemoryBackend:

    @pytest.mark.asyncio
    async def test_get(self, memory):
        await memory._get(pytest.KEY)
        SimpleMemoryBackend._cache.get.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_set(self, memory):
        await memory._set(pytest.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_set_no_ttl_no_handle(self, memory):
        await memory._set(pytest.KEY, "value", ttl=0)
        assert pytest.KEY not in memory._handlers

        await memory._set(pytest.KEY, "value")
        assert pytest.KEY not in memory._handlers

    @pytest.mark.asyncio
    async def test_set_ttl_handle(self, memory):
        await memory._set(pytest.KEY, "value", ttl=100)
        assert pytest.KEY in memory._handlers
        assert isinstance(memory._handlers[pytest.KEY], asyncio.Handle)

    @pytest.mark.asyncio
    async def test_multi_get(self, memory):
        await memory._multi_get([pytest.KEY, pytest.KEY_1])
        SimpleMemoryBackend._cache.get.assert_any_call(pytest.KEY)
        SimpleMemoryBackend._cache.get.assert_any_call(pytest.KEY_1)

    @pytest.mark.asyncio
    async def test_multi_set(self, memory):
        await memory._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")])
        SimpleMemoryBackend._cache.__setitem__.assert_any_call(pytest.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_any_call(pytest.KEY_1, "random")

    @pytest.mark.asyncio
    async def test_add(self, memory):
        await memory._add(pytest.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_add_existing(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        with pytest.raises(ValueError):
            await memory._add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_exists(self, memory):
        await memory._exists(pytest.KEY)
        SimpleMemoryBackend._cache.__contains__.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire_no_handle_no_ttl(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(pytest.KEY, 0)
        assert memory._handlers.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_expire_no_handle_ttl(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(pytest.KEY, 1)
        assert isinstance(memory._handlers.get(pytest.KEY), asyncio.Handle)

    @pytest.mark.asyncio
    async def test_expire_handle_ttl(self, memory):
        fake = MagicMock()
        SimpleMemoryBackend._handlers[pytest.KEY] = fake
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(pytest.KEY, 1)
        assert fake.cancel.call_count == 1
        assert isinstance(memory._handlers.get(pytest.KEY), asyncio.Handle)

    @pytest.mark.asyncio
    async def test_delete(self, memory):
        fake = MagicMock()
        SimpleMemoryBackend._handlers[pytest.KEY] = fake
        await memory._delete(pytest.KEY)
        assert fake.cancel.call_count == 1
        assert pytest.KEY not in SimpleMemoryBackend._handlers
        SimpleMemoryBackend._cache.pop.assert_called_with(pytest.KEY, None)

    @pytest.mark.asyncio
    async def test_clear_namespace(self, memory):
        SimpleMemoryBackend._cache.__iter__.return_value = iter(['nma', 'nmb', 'no'])
        await memory._clear("nm")
        assert SimpleMemoryBackend._cache.pop.call_count == 2
        SimpleMemoryBackend._cache.pop.assert_any_call('nma', None)
        SimpleMemoryBackend._cache.pop.assert_any_call('nmb', None)

    @pytest.mark.asyncio
    async def test_clear_no_namespace(self, memory):
        SimpleMemoryBackend._handlers = "asdad"
        SimpleMemoryBackend._cache = "asdad"
        await memory._clear("nm")
        SimpleMemoryBackend._handlers = {}
        SimpleMemoryBackend._cache = {}

    @pytest.mark.asyncio
    async def test_raw(self, memory):
        await memory._raw("get", pytest.KEY)
        SimpleMemoryBackend._cache.get.assert_called_with(pytest.KEY)

        await memory._set(pytest.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(pytest.KEY, "value")
