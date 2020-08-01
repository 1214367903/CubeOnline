import asyncio
import functools
import json
from collections.abc import Coroutine
from typing import Any, Callable, Optional, Union

from tornado.escape import json_decode

from form.forms import BaseForm
from util import cache

redis = cache.redis()
user_items = (
    'username',
    'usericon'
)

"""
user这个模块就是围绕着redis来的
简单点说,就是把每个用户的数据作为value,某个不重复id作为key存到redis里面
然后就可以实现session和用户认证等等的功能
"""


async def create_cache(session_id: str, form_obj: BaseForm) -> None:
    # 调用这个方法将需要的用户的数据存入缓存,然后就可以调用下面的函数获取session对象了
    userData = {key: form_obj.get(key) for key in user_items}
    await redis.hmset_dict(session_id, userData)


async def create_session_obj(session_id: str) -> Optional['Session']:
    # 创建session对象的必要条件是,这个session_id和相应已经在缓存里了,如果不存在,是没法创建的
    user_cache = await redis.hgetall(session_id)
    for item in user_items:
        if item not in user_cache:
            return None
    return Session(session_id)


# redis的哈希类型数据,其key和value支持以下几种数据类型
hash_type = Union[bytearray, bytes, float, int, str]


class Session:

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    async def get(self, key: hash_type, default: Any = None) -> Any:
        result = await redis.hget(self.session_id, key)
        if result is not None:
            try:
                result = json.loads(result)
            except json.decoder.JSONDecodeError:
                pass
            return result
        else:
            return default

    async def set(self, key: hash_type, value: hash_type, timeout: int = None) -> None:
        value = json.dumps(value)
        await redis.hset(self.session_id, key, value)
        if timeout is not None:
            await self.expire(key, timeout)

    async def expire(self, key: hash_type, seconds: int) -> None:
        await asyncio.sleep(seconds)
        await self.delete(key)

    async def delete(self, key: hash_type) -> None:
        await redis.hdel(self.session_id, key)

    async def get_all(self) -> dict:
        dic = await redis.hgetall(self.session_id)
        return dic

    async def delete_all(self) -> None:
        await redis.delete(self.session_id)


def authenticated(method: Callable) -> Callable:
    """
    这个装饰器专门给RequestHandler的网络请求方法用的,验证用户是否已经在后台登录
    如果用户传的数据中没有session_id或者session_id不对,就直接return不管这个请求
    否则,为这个handler对象创建一个session实例,以后需要什么用户信息,直接去session中取就行了
    """

    @functools.wraps(method)
    async def wrapper(self, *args: Any, **kwargs: Any) -> None:
        try:
            session_id = json_decode(self.request.body)['session_id']
        except (json.decoder.JSONDecodeError, KeyError):
            return
        session = await create_session_obj(session_id)
        if session is None:
            self.resp.set_error_message('用户未登录!')
            self.write(self.resp)
            return
        self.session = session
        result = method(self, *args, **kwargs)
        if isinstance(result, Coroutine):
            await result

    return wrapper
