from abc import ABC
from typing import Any, Callable, Union

import tornado.web
import tornado.websocket
from tornado.escape import json_encode

from util.log import get_logger

logger = get_logger()


class RequestHandler(tornado.web.RequestHandler, ABC):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.session = None
        self.resp = Response()
        super().__init__(*args, **kwargs)

    # def initialize(self) -> None:
    #     import time
    #     time.sleep(1)

    def write(self, chunk: Union[str, bytes, dict, 'Response']) -> None:
        if isinstance(chunk, Response):
            chunk = str(chunk)
        super().write(chunk)


class WebSocketHandler(tornado.websocket.WebSocketHandler, ABC):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.session = None
        self.callbacks = {}
        super().__init__(*args, **kwargs)

    async def write_message(self, message: Union[str, bytes, dict, 'Response'], binary: bool = False) -> None:
        if self.ws_connection is None or self.ws_connection.is_closing():
            logger.warning(f'WebSocket发送消息失败,连接已异常关闭.关闭码:{self.close_code},关闭原因:{self.close_reason}')
            return
        if isinstance(message, Response):
            message = str(message)
        await super().write_message(message, binary)

    def register_callback(self, event: str, callback: Callable) -> None:
        # websocket有回调功能,首先调用这个函数设置回调,然后重写对应的事件,让它去调用回调就行
        self.callbacks[event] = callback


class Response:
    """
    一般的http通信,返回的数据就用这个类来封装
    """
    success = 200
    failed = 400

    def __init__(self, data: dict = None) -> None:
        self.code = self.success
        self.message = 'OK'
        self.data = {}
        if data is not None:
            self.data.update(data)

    def __str__(self) -> str:
        return json_encode(self.__dict__)

    def set_error_message(self, message: str) -> None:
        self.code = self.failed
        self.message = message

    def set(self, key: Any, value: Any) -> None:
        self.data[key] = value


class Message(Response):
    """
    使用ws通信的时候, 就传递这个包
    这个包和Response的主要区别是, 加了一个event事件, 必须在初始化的时候就说明是什么事件
    """

    def __init__(self, event: str, data: dict = None) -> None:
        self.event = event
        super().__init__(data)
