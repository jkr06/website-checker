import aiopg
import asyncio
from dynaconf import settings


class ConnPool:
    _pool = None

    @classmethod
    async def pool(cls):
        if cls._pool is None:
            cls._pool = await aiopg.create_pool(**(dict(settings.DATABASE)))
        return cls._pool

    @classmethod
    async def clear(cls):
        if cls._pool is not None:
            await cls._pool.clear()
