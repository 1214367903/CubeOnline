import os

handlers = [
    (r'/user/login', 'controller.handlers.LoginHandler'),
    (r'/room/create', 'controller.handlers.CreateRoomHandler'),
    (r'/room/random', 'controller.handlers.RandomRoomHandler'),
    (r'/room/join', 'controller.handlers.JoinRoomHandler'),
]

app_settings = {
    'autoreload': True,
    'compress_response': True
}

redis_config = {
    'address': 'redis://127.0.0.1',
    'encoding': 'utf-8',
    'minsize': 1,
    'maxsize': 10,
}

log_path = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_path):
    os.mkdir(log_path)

connection_config = {}

scrambler_config = {
    'capacity': {
        '222': 100,
        '333': 200,
        '444': 80,
        '555': 80,
        '666': 40,
        '777': 40,
        'pyram': 100,
        'skewb': 100,
        'minx': 60,
        'sq1': 60,
        'clock': 60,
    },
    'url': 'http://127.0.0.1:2014/scramble/.txt?e={cube}*{n}'
}

room_manager_settings = {
    'capacity': 100,
}

room_events = {
    'on_ready',
    'upload_score',
}

applets_api = {
    'wx': {
        'url': 'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code',
        'app_id': '',
        'secret': ''
    },
    'qq': {
        'url': 'https://api.q.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code',
        'app_id': '',
        'secret': '',
    }
}

available_contest_items = (
    '222',
    '333',
    '444',
    '555',
    '666',
    '777',
    '333oh',
    '333bf',
    '444bf',
    '555bf',
    'pyram',
    'skewb',
    'minx',
    'sq1',
    'clock',
    '333wf',
)

# 比赛项目对应的魔方
contest_to_cube = {
    '333': '333',
    '444': '444',
    '555': '555',
    '666': '666',
    '777': '777',
    '222': '222',
    '333oh': '333',
    '333bf': '333',
    '444bf': '444',
    '555bf': '555',
    'pyram': 'pyram',
    'skewb': 'skewb',
    'minx': 'minx',
    'sq1': 'sq1',
    'clock': 'clock',
    '333wf': '333',
}
