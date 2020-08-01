"""
目前的服务主要是请求本地的一个接口,以及微信获取open_id的接口
因此,使用连接池理论上会有更好的性能
tornado没有自带的连接池,只好上aiohttp了
"""

from typing import Optional

import aiohttp

from config import connection_config
from util import UtilError

_client = None


async def init() -> None:
    global _client
    if _client is not None:
        return
    # client对象必须在协程中初始化,否则它会自己new一个loop,最终造成混乱
    _client = aiohttp.ClientSession(**connection_config)


def get_client() -> Optional[aiohttp.ClientSession]:
    if _client is None:
        raise UtilError('the connector has not been initialized')
    return _client


if __name__ == '__main__':
    import asyncio


    async def f() -> None:
        await init()
        assert isinstance(get_client(), aiohttp.ClientSession)


    asyncio.new_event_loop().run_until_complete(f())
