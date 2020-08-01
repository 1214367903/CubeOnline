from abc import ABC
from typing import Optional, Tuple, Union

from tornado.escape import json_decode

from config import applets_api
from controller import user, web
from controller.room.manager import RoomManager
from controller.room.room import Room
from form import forms
from util.connector import get_client
from util.log import get_logger

manager = RoomManager.instance()
client = get_client()
logger = get_logger()


class LoginHandler(web.RequestHandler, ABC):
    """
    每次用户进入小程序,都会向这个路由发送消息
    消息内容就是用户的数据,如果是初次使用的,后端还会帮忙获取open_id
    最后,还会在缓存中为用户创建一个session
    这样做的目的是,让后端知道有这样一个用户来了,确保后面的用户验证以及获取用户数据不会出问题
    """

    async def post(self) -> None:
        form = forms.LoginForm(self.request.body)
        if not form.valid:
            self.resp.set_error_message(form.error_message)
            self.write(self.resp)
            return
        if not form.get('has_session_id'):
            # 如果用户端没有session_id,就通过code获得open_id,进而得到session_id
            open_id = await self.get_open_id(form)
            if open_id is None:
                self.resp.set_error_message("获取用户ID失败!")
                self.write(self.resp)
                return
            else:
                session_id = self.create_session_id(open_id)
        else:
            session_id = form.get('session_id')
        self.resp.set('session_id', session_id)
        self.write(self.resp)
        await user.create_cache(session_id, form)

    @staticmethod
    async def get_open_id(form: forms.BaseForm) -> Optional[str]:
        api = applets_api[form.get('applet')]
        url = api['url'].format(
            appid=api['app_id'],
            secret=api['secret'],
            code=form.get('code', '')
        )
        response = await client.get(url)
        if response.status != 200:
            return None
        text = await response.text()
        text = json_decode(text)
        open_id = text.get('openid', '')
        if not open_id:
            logger.warning(f'请求open_id失败, 错误代码:{text.get("errcode", "unknown")}, 错误信息:{text.get("errmsg", "unknown")}')
            return None
        else:
            return open_id

    @staticmethod
    def create_session_id(open_id: str) -> str:
        # 直接把open_id给前端是不妥的
        # 这里把open_id进行一道加密, 加密结果作为session_id给前端
        return open_id[::-1]


class CreateRoomHandler(web.RequestHandler, ABC):

    @user.authenticated
    def post(self) -> None:
        form = forms.CreateRoomForm(self.request.body)
        if not form.valid:
            self.resp.set_error_message(form.error_message)
            self.write(self.resp)
            return
        room = manager.create_room(form.get('room_settings'))
        if room is None:
            self.resp.set_error_message('当前正在用的房间有点多, 等会再试试吧')
        else:
            self.resp.set('room_id', room.id)
        self.write(self.resp)


class RandomRoomHandler(web.RequestHandler, ABC):

    @user.authenticated
    def post(self) -> None:
        form = forms.RandomRoomForm(self.request.body)
        if not form.valid:
            self.resp.set_error_message(form.error_message)
            self.write(self.resp)
            return
        room = manager.get_room_randomly(form.get('room_settings').get('contest_item'))
        if room is None:
            self.resp.set_error_message('暂时没有合适的房间, 等会再试试吧')
        else:
            self.resp.set('room_id', room.id)
            self.resp.set('time_limit', room.settings['time_limit'])
        self.write(self.resp)


class JoinRoomHandler(web.WebSocketHandler, ABC):
    """
    这个对象只是一个工具人
    客户端创建连接后,它通过open函数内的逻辑判断用户是否合法,以及对应的房间是否能用
    确定能用之后,就将自己交由room对象去处理了.这之后它依然存在,但只是一个用于收发消息的工具
    """

    async def open(self) -> None:
        # 为了方便,连接时将需要的数据放在请求头里面了
        form = forms.JoinRoomForm({k.lower(): v for k, v in dict(self.request.headers).items()})
        if not form.valid:
            self.close(reason=form.error_message)
            return
        session = await user.create_session_obj(session_id=form.get('session_id'))
        if session is None:
            self.close(reason='用户未登录!')
            return
        room_id = form.get('room_id')
        room = manager.get_room(room_id)
        is_available, reason = self.is_room_available(room)
        if not is_available:
            self.close(reason=reason)
            return
        else:
            await room.add_member(self, session)

    @staticmethod
    def is_room_available(room: Optional['Room']) -> Tuple[bool, str]:
        if room is None:
            return False, '房间不存在!'
        elif room.is_full:
            return False, f'{room.id}号房间已满员!'
        elif room.is_playing:
            return False, f'{room.id}号房间正在比赛,稍后再试吧'
        else:
            return True, ''

    def check_origin(self, origin: str) -> bool:
        return True

    async def on_message(self, message: Union[str, bytes]) -> None:
        # 小程序没法指定opcode,所以ping包只能通过message发送
        # 这里验证一下是不是ping包,是的话直接返回一个pong,不是再走message那套流程
        # 需要注意的是,ping pong包不遵循为ws定义的一套协议
        # 首先因为这是底层的东西,event那套是给应用层用的
        # 然后是为了减少包的体积
        ping_message = forms.PingForm(message)
        if ping_message.valid:
            await self.write_message({'pong': ping_message.get('ping')})
            return
        callback = self.callbacks.get('on_message', None)
        if callback is not None:
            await callback(message)

    def on_close(self) -> None:
        if self.close_code != 1000:
            logger.warning(f'WebSocket发生了异常关闭,关闭码:{self.close_code},关闭原因:{self.close_reason}')
        callback = self.callbacks.get('on_close', None)
        if callback is not None:
            callback(self)
