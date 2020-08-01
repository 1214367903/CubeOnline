"""
这里的缓存本质上是一个redis连接池,通过redis实现缓存效果
后面可能还会加别的东西,现在反正只有个redis
首先调用init_cache函数初始化,然后调用redis函数就能得到一个redis对象
"""

from typing import Optional

import aioredis

from config import redis_config
from util import UtilError

_redis = None


def redis() -> Optional[aioredis.commands.Redis]:
    if _redis is None:
        raise UtilError('The cache util has not been initialized')
    return _redis


async def init() -> None:
    global _redis
    if _redis is not None:
        return
    try:
        _redis = await aioredis.create_redis_pool(**redis_config)
    except ConnectionRefusedError:
        raise UtilError('The redis server has not started')


if __name__ == '__main__':
    import asyncio


    async def f() -> None:
        await init()
        assert isinstance(redis(), aioredis.commands.Redis)


    asyncio.new_event_loop().run_until_complete(f())
