import asyncio

import nest_asyncio
import pytest

from .fixtures import *


nest_asyncio.apply()


@pytest.fixture(autouse=True, scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
