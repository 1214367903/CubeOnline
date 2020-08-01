from typing import Dict, List, Optional

import requests
import tornado.ioloop
from aiohttp.client_exceptions import ClientConnectorError

import util.connector
from config import contest_to_cube, scrambler_config
from util import UtilError, log

client = util.connector.get_client()
logger = log.get_logger()

_scramble_pool = None


def get_scramble_pool() -> Optional['ScramblePool']:
    if _scramble_pool is None:
        raise UtilError('The scramble pool has not been initialized')
    return _scramble_pool


async def init() -> None:
    global _scramble_pool
    if _scramble_pool is not None:
        return
    _scramble_pool = await ScramblePool.instance()


class ScramblePool:
    """
    这个池子负责储存各种魔方的打乱,它是单例的
    必须调用initialize进行初始化,这个过程会把打乱池填满,不然得到的是一个空池子
    """
    _pool = None

    @classmethod
    async def instance(cls) -> 'ScramblePool':
        if cls._pool is None:
            cls._pool = cls(**scrambler_config)
            try:
                await cls._pool.initialize()
            except ClientConnectorError:
                raise UtilError('the scrambler server has not started')
        return cls._pool

    def __init__(self, capacity: Dict[str, int], url: str) -> None:
        self.capacity = capacity
        self.url = url
        self.scrambles = {}
        self.flags = {}

    async def initialize(self) -> None:
        for cube in self.capacity.keys():
            self.scrambles[cube] = await self.request_scrambles(cube)
            self.flags[cube] = False

    def get_scramble(self, contest: str = '333') -> str:
        """
        这个方法由外界调用,从打乱池中取出一个指定项目的打乱
        首先,打乱池会在自己的缓存中找打乱然后返回
        如果缓存中的打乱不多了,就添加个回调补充一波打乱
        最坏的情况就是缓存空了,此时只好先用同步的方式去补充一波
        这种情况如果常常出现,就要修改config中的capacity了
        """
        cube = contest_to_cube[contest]
        if not self.scrambles[cube]:
            self.scrambles[cube] += self.request_scrambles_sync(cube)
            logger.warning(f'{cube}的缓存打乱已经被击穿')
        scramble = self.scrambles[cube].pop()
        if len(self.scrambles[cube]) <= self.capacity[cube] // 2:
            tornado.ioloop.IOLoop.current().add_callback(self.supplement_scramble, cube)
        return scramble

    async def supplement_scramble(self, cube: str) -> None:
        # 缓存里面某种打乱不足的时候,可能会多次触发这个函数
        # 因此使用一个flag来拦截多余的补充
        if self.flags[cube]:
            return
        self.flags[cube] = True
        scrambles = await self.request_scrambles(cube)
        self.scrambles[cube] += scrambles
        self.flags[cube] = False

    async def request_scrambles(self, cube: str) -> List[str]:
        response = await client.get(self.url.format(cube=cube, n=self.capacity[cube]))
        content = await response.text()
        return content.split('\r\n')[:-1]

    def request_scrambles_sync(self, cube: str) -> List[str]:
        response = requests.get(self.url.format(cube=cube, n=self.capacity[cube]))
        return response.text.split('\r\n')[:-1]
