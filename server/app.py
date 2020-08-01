import os
import socket
from abc import ABC
from typing import Any

import tornado.ioloop
import tornado.web
import uvloop
from tornado.options import define, options, parse_command_line
from tornado.platform.asyncio import BaseAsyncIOLoop

import config
from util import init_utils, log

logger = log.get_logger()


def get_address() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


class TornadoUvloop(BaseAsyncIOLoop, ABC):
    def initialize(self, **kwargs: Any) -> None:
        loop = uvloop.new_event_loop()
        super().initialize(loop, close_loop=True, **kwargs)


def run_server() -> None:
    # 首先,使用uvloop代替tornado的事件循环
    tornado.ioloop.IOLoop.configure(TornadoUvloop)
    # 然后,将需要异步初始化的组件初始化
    tornado.ioloop.IOLoop.current().run_sync(init_utils)
    # 然后,整一些服务器的设置
    define('address', default=get_address(), help='Run server on a specific address', type=str)
    define('port', default=8888, help='Run server on a specific port', type=int)
    options.log_file_prefix = os.path.join(config.log_path, 'tornado.log')
    parse_command_line()
    # 然后,配置app
    application = tornado.web.Application(handlers=config.handlers, **config.app_settings)
    application.listen(options.port, address=options.address)
    logger.info(f'run server in {options.address}:{options.port}')
    # 最后,启动事件循环
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    run_server()
