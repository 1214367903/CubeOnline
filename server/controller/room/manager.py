import random
from typing import Optional

from config import available_contest_items, room_manager_settings
from controller.room.room import Room


class RoomManager:
    """
    这东西负责对房间进行管理,也就是创建,查找,删除等等
    如果要使用的话,用instance方法来获取实例,因为它是单例的
    需要注意的是,这里所有room_id的数据类型都是字符串
    """
    _manager = None

    @classmethod
    def instance(cls) -> 'RoomManager':
        if cls._manager is None:
            cls._manager = cls(**room_manager_settings)
        return cls._manager

    def __init__(self, capacity: int) -> None:
        self.rooms = {}
        self.open_rooms = {item: [] for item in available_contest_items}
        self.capacity = capacity

    def create_room(self, settings: dict) -> Optional[Room]:
        room_id = self.create_room_id()
        if room_id is None:
            return None
        room = Room(room_id, settings, self.delete_room)
        self.rooms[room_id] = room
        if not settings['is_room_private']:
            self.open_rooms[settings['contest_item']].append(room_id)
        return room

    def create_room_id(self) -> Optional[str]:
        if self.is_full:
            return None
        # 这里最多尝试100次, 避免出点什么问题, 整个线程在这里卡死
        for i in range(100):
            room_id = str(random.randrange(1000, 10000))
            if room_id not in self.rooms:
                return room_id
        return None

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id, None)

    def get_room_randomly(self, contest_item: str) -> Optional[Room]:
        # 这个方法是给随机推荐房间功能做的
        # 传入需要的比赛项目,随机返回一个正在进行该项目的房间
        rooms = self.open_rooms.get(contest_item)
        if not rooms:
            return None
        room_id = random.choice(rooms)
        return self.get_room(room_id)

    def delete_room(self, room: Room) -> None:
        # 如果用户刚进来就离开房间,这个回调就可能会触发两次,第二次是删不了房间的
        try:
            del self.rooms[room.id]
            if not room.settings['is_room_private']:
                self.open_rooms[room.settings['contest_item']].remove(room.id)
        except KeyError:
            return

    @property
    def current_room_num(self) -> int:
        return len(self.rooms)

    @property
    def is_full(self) -> bool:
        return self.current_room_num >= self.capacity
