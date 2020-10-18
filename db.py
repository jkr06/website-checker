import aiopg
import asyncio
from dynaconf import settings


class ConnPool:
    _pool = []

    @classmethod
    async def pool(cls):
        if not cls._pool:
            cls._pool = await aiopg.create_pool(**(dict(settings.DATABASE)))
        return cls._pool

    @classmethod
    async def clear(cls):
        await cls._pool.clear()
