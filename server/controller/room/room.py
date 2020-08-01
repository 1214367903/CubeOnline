from typing import (Callable, Coroutine, Dict, Iterable, List, Optional, Tuple,
                    Union)

import tornado.gen
import tornado.ioloop

from controller import user, web
from controller.web import Message
from form.forms import MessageForm
from util.scrambler import get_scramble_pool

scramble_pool = get_scramble_pool()


class Room:
    """
    room主要做的事:管理房间成员,控制比赛流程
    至于长连接通信这一块,消息是直接转给handler对象,它只是member和handler之间的传话筒
    """
    capacity = 8
    pre_playing_state = 'preparation'
    playing_state = 'cubing'

    def __init__(self, room_id: str, settings: dict, on_finish_cb: Callable) -> None:
        self.id = room_id
        self.settings = settings
        self.members = set()
        # 每个用户都应该有个id,在房间内用于辨识,就从这个id库中取出
        self.member_ids = set(range(self.capacity))
        self.handler = EventHandler(self)
        # 下面这几个属性和每轮比赛的关联比较大
        self.state = self.pre_playing_state
        self.scramble = scramble_pool.get_scramble(self.settings['contest_item'])
        self.current_scores = {}
        # 比赛过程中如果有什么事情要处理,可以把这事先放到回调列表中,等这轮结束后一起处理
        # 这个回调必须是协程的形式
        self.contest_callbacks = []
        # 当一个房间的生命周期到头了,也就是没人的时候,调用这个回调
        self.on_finish_cb = on_finish_cb
        # 在创建完成后,检查一下这个房间有没有被使用,避免产生僵尸房
        tornado.ioloop.IOLoop.current().add_callback(self._is_room_used)

    async def add_member(self, web_socket: web.WebSocketHandler, session: user.Session) -> None:
        # 有新的连接加入后,首先为这个连接创建一个member对象
        # 然后,向这个连接发送房间的数据,使其完成初始化
        # 最后,向其他成员发送这个成员的信息,让他们知道来了新人
        member_id = self.member_ids.pop()
        member = await create_member(web_socket, session, self, member_id)
        self.members.add(member)
        await member.write_message(Message(
            event='initialize_room',
            data={
                'settings': self.settings,
                'scramble': self.scramble,
                'members': [m.info for m in self.members],
                'user_id': member_id
            }
        ))
        await self.write_message_to_others(Message(
            event='add_member',
            data={'member_info': member.info}
        ), member)

    async def delete_member(self, member: 'Member') -> None:
        # 首先,删除成员,回收成员id
        # 然后,群发消息告诉大家
        # 最后,检查一下房间是不是没人了,还用不用
        self.members.remove(member)
        self.member_ids.add(member.id)
        await self.write_message_group(Message('delete_member', {'member_id': member.id}))
        if not self.members:
            await self._is_room_used()

    async def on_member_left(self, member: 'Member') -> None:
        # 用户断连接的时候触发,如果当前不在比赛,直接删它就完了
        # 否则,就先设置回调,等结束比赛再删它
        # 此外,如果用户还没成绩,本轮成绩给它记为DNF
        member.has_left = True
        if self.is_playing:
            self.add_callback(self.delete_member(member))
            if member not in self.finished_members:
                await self.handler.handle(member, {'event': 'upload_score', 'data': {'score': 'DNF'}})
        else:
            await self.delete_member(member)

    # 下面几个方法和比赛相关

    def can_start_round(self) -> bool:
        # 确定当前的条件能否开始比赛
        if self.num_of_member < 2:
            return False
        for member in self.members:
            if not member.is_ready:
                return False
        return True

    def start_round(self) -> None:
        # 调用这个函数告诉room对象,开始比赛了,你把你那几个变量整一整
        self.state = self.playing_state

    def add_score(self, member: 'Member', score: Union[str, int]) -> None:
        self.current_scores[member] = score

    def is_everyone_finished(self) -> bool:
        return len(self.finished_members) == self.num_of_member

    async def finish_round(self) -> None:
        # 结束一轮比赛后,把房间状态改为赛前
        # 然后,计算排名,在后台给用户更新成绩和积分
        # 然后,更新room的打乱
        # 然后,把计算的排名和新一轮的打乱发给前端,让前端结束本轮
        # 所有事情都处理完后,就处理本轮比赛的回调,注意回调都是coroutine的形式,直接await就行
        self.state = self.pre_playing_state
        ranking = self.calculate_ranking()
        for member, score in self.current_scores.items():
            member.on_round_finish(score, ranking[member][1])
        self.current_scores.clear()
        self.scramble = scramble_pool.get_scramble(self.settings['contest_item'])
        await self.write_message_group(Message(
            event='finish_round',
            data={
                'new_scramble': self.scramble,
                'ranking': {m.id: v for m, v in ranking.items()}
            }
        ))
        for callback in self.contest_callbacks:
            await callback
        self.contest_callbacks.clear()

    def calculate_ranking(self) -> Dict['Member', Tuple[int, int]]:
        # 比赛结束后调用这个函数计算排名和积分
        # 返回一个字典,key是用户,value是包含排名和积分的元组
        # 计算方法是,首先把成绩放在一个列表中进行排序
        # 然后把排序后的列表转化为成绩->排名的字典,注意这里的相同成绩并列排名问题
        # 最后,把用户->成绩->排名这里串起来,顺便计算对应的积分
        scores = list(self.current_scores.values())
        scores.sort(key=lambda x: float('inf') if x == 'DNF' else x)
        score_rank = {}
        for index, score in enumerate(scores):
            if score not in score_rank:
                score_rank[score] = index + 1
        ranking = {}
        # 这里的积分计算是以2为底,按照人数-排名进行幂运算
        power = len(self.finished_members) - 1
        for member in self.finished_members:
            rank = score_rank[self.current_scores[member]]
            point = int(2 ** (power - rank))
            ranking[member] = (rank, point)
        return ranking

    def add_callback(self, callback: Coroutine) -> None:
        self.contest_callbacks.append(callback)

    # 下面几个属于room的被动方法,由相应事件来触发它

    async def _is_room_used(self) -> None:
        # 当房间没人的时候, 调用这个方法
        # 先等一会, 如果还没人就调用设置的on_finish_cb回调
        # 一般来说,on_finish_cb的作用是删除房间,回收房间号码
        await tornado.gen.sleep(30)
        if not self.members:
            self.on_finish_cb(self)

    async def on_message(self, member: 'Member', message: MessageForm) -> None:
        await self.handler.handle(member, message)

    # 下面的方法负责给用户群发消息

    async def write_message_group(self, message: Message, members: Optional[Iterable['Member']] = None) -> None:
        # 给指定的几个人群发消息,默认是所有人
        if members is None:
            members = self.members
        for member in members:
            await member.write_message(message)

    async def write_message_to_others(self, message: Message, excluded_member: 'Member') -> None:
        # 给房间内除了指定成员之外的成员写入message
        for member in self.members:
            if member == excluded_member:
                continue
            await member.write_message(message)

    # 下面是几个动态的属性,基本都和member相关

    @property
    def num_of_member(self) -> int:
        return len(self.members)

    @property
    def is_full(self) -> bool:
        return self.num_of_member >= self.capacity

    @property
    def is_playing(self) -> bool:
        return self.state == self.playing_state

    @property
    def finished_members(self) -> List['Member']:
        return list(self.current_scores.keys())


# 创建member对象需要进行异步的初始化,因此必须使用这个函数来创建member对象
async def create_member(web_socket: web.WebSocketHandler, session: user.Session, room: 'Room',
                        member_id: int) -> 'Member':
    member = Member(web_socket, session, room, member_id)
    await member.initialize()
    return member


class Member:
    """
    这东西可以理解为对web_socket的封装,主要是增加了一些用户的信息
    除此之外,它也只是传递信息的工具.web_socket来消息后,它再把消息传给room

    如果要实例化一个member对象,应该调用上面那个create_member函数
    这是因为,实例化过程中有一些异步的操作,__init__没法独立完成
    """
    attributes = {
        'username',
        'usericon',
        'state',
        'point',
        'best',
        'average',
        'tried',
        'solved',
        'id'
    }
    ready_state = 'ready'
    unready_state = 'unready'

    def __init__(self, web_socket: web.WebSocketHandler, session: user.Session, room: 'Room', member_id: int) -> None:
        # 首先对web_socket进行改造,触发什么事件的时候,member这边能够知道并处理
        self.web_socket = web_socket
        self.web_socket.register_callback('on_message', self._on_message)
        self.web_socket.register_callback('on_close', self._on_close)
        # 几个必要的属性
        self.session = session
        self.room = room
        # 下面几个都是用户的属性
        self.username = ''
        self.usericon = ''
        self.state = self.unready_state
        self.point = 0
        self.best = None
        self.average = 0
        self.tried = 0
        self.solved = 0
        self.id = member_id
        self.has_left = False

    async def initialize(self) -> None:
        self.username = await self.session.get('username')
        self.usericon = await self.session.get('usericon')

    def on_round_finish(self, score: Union[str, int], point: int) -> None:
        # 当一轮比赛结束的时候,调用这个方法,更新成绩和状态
        self.state = self.unready_state
        self.tried += 1
        self.point += point
        if score == 'DNF':
            return
        if self.best is None or score < self.best:
            self.best = score
        self.average = (self.average * self.solved + score) / (self.solved + 1)
        self.solved += 1

    async def write_message(self, message: web.Message) -> None:
        if self.has_left:
            return
        await self.web_socket.write_message(message)

    async def _on_message(self, message: Union[str, bytes]) -> None:
        # 把前端来的消息进行验证和处理后,发给room
        message = MessageForm(message)
        if not message.valid:
            return
        await self.room.on_message(self, message)

    def _on_close(self, _: web.WebSocketHandler) -> None:
        async def _on_close_callback():
            await self.room.on_member_left(self)

        tornado.ioloop.IOLoop.current().add_callback(_on_close_callback)

    @property
    def info(self) -> dict:
        return {attribute: getattr(self, attribute) for attribute in self.attributes}

    @property
    def is_ready(self) -> bool:
        return self.state == self.ready_state


class EventHandler:
    """
    Room对象主要负责人员和信息的管理
    这个对象则负责处理具体的客户端请求
    这些信息一般都有event和data两部分
    通过event反射自身找到对应的处理方法,然后将data交由这个方法去处理
    """

    def __init__(self, room: Room) -> None:
        self.room = room

    async def handle(self, member: Member, message: Union[MessageForm, dict]) -> None:
        # 通过反射的方式找到事件对应的处理方法,将消息中的数据交由这个方法去处理
        event = message.get('event')
        data = message.get('data')
        func = getattr(self, event)
        await func(member, data)

    async def on_ready(self, member: Member, _: dict) -> None:
        # 如果用户已经准备了,前端没拦截住,直接不管它
        # 否则,将后端的用户状态改为准备
        # 这时判断一下能不能开始比赛
        # 然后在发的消息中,首先告诉用户,有人改了状态,同时也告诉用户,能不能开始比赛
        # 最后,如果可以开始比赛,后端也更新为比赛状态
        if member.is_ready:
            return
        member.state = member.ready_state
        can_start_round = self.room.can_start_round()
        message = Message(
            event='change_state',
            data={
                'member_id': member.id,
                'new_state': member.state,
                'can_start_round': can_start_round
            }
        )
        await self.room.write_message_group(message)
        if can_start_round:
            self.room.start_round()

    async def upload_score(self, member: Member, data: dict) -> None:
        # 用户上传成绩时触发这个函数
        # 首先,把它的成绩发给已经完事的成员
        # 然后,将它的成绩加入当前成绩列表,再把当前成绩列表发给它
        # 最后,如果比赛结束了,就调用room.finish_round
        score = data['score']
        await self.room.write_message_group(Message(
            event='update_score',
            data={
                'scores': {member.id: score},
            }
        ), self.room.finished_members)
        self.room.add_score(member, score)
        await member.write_message(Message(
            event='update_score',
            data={
                'scores': {m.id: s for m, s in self.room.current_scores.items()},
            }
        ))
        if self.room.is_everyone_finished():
            await self.room.finish_round()
