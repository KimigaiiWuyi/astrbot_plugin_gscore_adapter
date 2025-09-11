import asyncio
import base64
import os
from base64 import b64encode
from pathlib import Path
from typing import List

import aiofiles
import websockets.client
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.message.components import (
    At,
    BaseMessageComponent,
    File,
    Image,
    Nodes,
    Node,
    Plain,
    Reply,
)
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.core.platform.message_type import MessageType
from astrbot.core.star.filter.event_message_type import EventMessageType
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from .models import Message as GsMessage
from .models import MessageReceive, MessageSend

gsconnecting = False


@register(
    "astrbot_plugin_gscore_adapter",
    "KimigaiiWuyi",
    "用于链接SayuCore（早柚核心）的适配器！适用于多种游戏功能, 原神、星铁、绝区零、鸣朝、雀魂等游戏的最佳工具箱！",
    "0.4",
)
class GsCoreAdapter(Star):

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.is_connect = False
        self.BOT_ID = self.config.BOT_ID
        self.IP = self.config.IP
        self.PORT = self.config.PORT

    async def async_connect(
        self,
    ):
        self.is_alive = True
        self.ws_url = f'ws://{self.IP}:{self.PORT}/ws/{self.BOT_ID}'
        logger.info(f'Bot_ID: {self.BOT_ID}连接至[gsuid-core]: {self.ws_url}...')
        self.ws = await websockets.client.connect(  # type: ignore
            self.ws_url, max_size=2**26, open_timeout=60, ping_timeout=60
        )
        logger.info(f'与[gsuid-core]成功连接! Bot_ID: {self.BOT_ID}')
        self.is_connect = True
        self.msg_list = asyncio.queues.Queue()
        self.pending = []

    async def connect(self):
        global gsconnecting
        if not gsconnecting and not self.is_connect:
            gsconnecting = True
            try:
                await self.async_connect()
                logger.info('[gsuid-core]: 发起一次连接')
                await self.start()
                gsconnecting = False
            except ConnectionRefusedError:
                gsconnecting = False
                logger.error(
                    '[链接错误] Core服务器连接失败...请确认是否根据文档安装【早柚核心】！'
                )

    @filter.event_message_type(EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        if self.is_connect is False:
            await self.connect()

        if not hasattr(self, 'ws'):
            logger.error(
                '[链接错误] Core服务器连接失败...请确认是否根据文档安装【早柚核心】！'
            )

        assert self.ws is not None
        try:
            await self.ws.ping()
        except ConnectionClosed:
            await self.connect()

        user_name = event.get_sender_name()

        logger.debug(event.unified_msg_origin)

        message_chain = (
            event.get_messages()
        )  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)

        pn = event.get_platform_name()
        sender = {
            'nickname': user_name,
        }

        self_id = event.get_self_id()
        user_id = str(event.get_sender_id())
        if pn == 'qq_official':
            avatar = f'https://q.qlogo.cn/qqapp/{self_id}/{user_id}/100'
        elif pn == 'aiocqhttp':
            avatar = f'https://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640'
        else:
            avatar = ''
        sender['avatar'] = avatar

        message: List[GsMessage] = []
        for msg in message_chain:
            if isinstance(msg, Image):
                img_path = msg.path
                if not img_path:
                    img_path = msg.url
                if img_path:
                    if img_path.startswith('http'):
                        message.append(
                            GsMessage(
                                type='image',
                                data=img_path,
                            )
                        )
                    else:
                        if not os.path.exists(img_path):
                            img_path = Path(__file__).parent / img_path
                            async with aiofiles.open(img_path, 'rb') as f:
                                img_data = await f.read()
                            base64_data = b64encode(img_data).decode('utf-8')
                            message.append(
                                GsMessage(
                                    type='image',
                                    data=f'base64://{base64_data}',
                                )
                            )
            elif isinstance(msg, File):
                if msg.file and msg.name:
                    if msg.file_:
                        file_val = await file_to_base64(Path(msg.file_))
                    else:
                        file_val = msg.url
                    file_name = msg.name
                    message.append(
                        GsMessage(
                            type='file',
                            data=f'{file_name}|{file_val}',
                        )
                    )
            elif isinstance(msg, Plain):
                message.append(
                    GsMessage(
                        type='text',
                        data=msg.text,
                    )
                )
            elif isinstance(msg, At):
                message.append(
                    GsMessage(
                        type='at',
                        data=str(msg.qq),
                    )
                )
            elif isinstance(msg, Reply):
                message.append(
                    GsMessage(
                        type='reply',
                        data=msg.id,
                    )
                )
            else:
                logger.warning(f'不支持的消息类型: {type(msg)}')

        user_type = (
            'group'
            if event.get_message_type() == MessageType.GROUP_MESSAGE
            else 'direct'
        )
        pm = 1 if event.is_admin() else 6

        platform_id = event.get_platform_id()
        msg = MessageReceive(
            # bot_id在gscore内部数据库具有唯一标识符，修改将会造成breaking change
            bot_id='onebot' if pn == 'aiocqhttp' else pn,
            bot_self_id=platform_id,
            user_type=user_type,
            group_id=event.get_group_id(),
            user_id=user_id,
            sender=sender,
            content=message,
            msg_id=event.get_session_id(),
            user_pm=pm,
        )
        logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
        await self._input(msg)

    async def _input(self, msg: MessageReceive):
        await self.msg_list.put(msg)

    async def send_msg(self):
        while True:
            msg: MessageReceive = await self.msg_list.get()
            msg_send = msgjson.encode(msg)
            await self.ws.send(msg_send)

    async def start(self):
        asyncio.create_task(self.recv_msg())
        asyncio.create_task(self.send_msg())
        # _, self.pending = await asyncio.wait(
        #     [recv_task, send_task],
        #     return_when=asyncio.FIRST_COMPLETED,
        # )

    async def recv_msg(self):
        try:
            await asyncio.sleep(5)
            async for message in self.ws:
                try:
                    msg = msgjson.decode(message, type=MessageSend)
                    logger.info(
                        f'【接收】[gsuid-core]: '
                        f'{msg.bot_id} - {msg.target_type} - {msg.target_id}'
                    )
                    # 解析消息
                    if msg.bot_id == 'AstrBot':
                        if msg.content:
                            _data = msg.content[0]
                            if _data.type and _data.type.startswith('log'):
                                _type = _data.type.split('_')[-1].lower()
                                getattr(logger, _type)(_data.data)
                        continue

                    bid = msg.bot_id
                    if bid == 'aiocqhttp' or bid == 'dingtalk':
                        session_id = msg.target_id
                    elif bid == 'lark':
                        session_id = msg.target_id
                    elif bid == 'dingtalk':
                        session_id = msg.target_id
                    elif bid == 'wechatpadpro':
                        session_id = msg.target_id
                    else:
                        session_id = msg.msg_id

                    if session_id is None:
                        logger.warning(f'[GsCore] 消息{msg}没有session_id')
                        continue

                    if msg.target_id and msg.content:
                        session = MessageSesion(
                            msg.bot_self_id,
                            (
                                MessageType.GROUP_MESSAGE
                                if msg.target_type == 'group'
                                else MessageType.FRIEND_MESSAGE
                            ),
                            session_id,
                        )
                        await self.bot_send_msg(msg.content, session, bid)
                except Exception as e:
                    logger.exception(e)
        except RuntimeError:
            pass
        except ConnectionClosedError:
            for task in self.pending:
                task.cancel()
            logger.warning(f'与[gsuid-core]断开连接! Bot_ID: {self.BOT_ID}')
            self.is_alive = False
            for _ in range(30):
                await asyncio.sleep(5)
                try:
                    await self.async_connect()
                    await self.start()
                    break
                except:  # noqa
                    logger.debug('自动连接core服务器失败...五秒后重新连接...')

    async def _to_msg(
        self, msg: List[GsMessage], bot_id: str
    ) -> List[BaseMessageComponent]:
        message = []
        for _c in msg:
            if _c.data:
                if _c.type == 'text':
                    message.append(Plain(_c.data))
                elif _c.type == 'image':
                    if _c.data.startswith('link://'):
                        message.append(Image.fromURL(_c.data[7:]))
                    else:
                        if _c.data.startswith('base64://'):
                            _c.data = _c.data[9:]
                        message.append(
                            Image.fromBase64(_c.data),  # type: ignore
                        )
                elif _c.type == 'node':
                    # 特殊处理 qq 平台
                    if bot_id == 'onebot':
                        node_message: List[Node] = []
                        for _node in _c.data:
                            node_message.append(
                                Node(
                                    await self._to_msg(
                                        [GsMessage(**_node)],
                                        bot_id,
                                    )
                                )
                            )

                        # 将一条消息转为多条消息，优化观感
                        message.append(
                            Nodes(
                                node_message,
                            )
                        )
                    else:
                        for _node in _c.data:
                            message.extend(
                                await self._to_msg(
                                    [GsMessage(**_node)],
                                    bot_id,
                                )
                            )
                elif _c.type == 'file':
                    file_name, file_content = _c.data.split('|')
                    path = Path(__file__).resolve().parent / file_name
                    store_file(path, file_content)
                    message.append(File(file_name, str(path)))
                elif _c.type == 'at':
                    message.append(At(qq=_c.data))
        return message

    async def bot_send_msg(
        self,
        gsmsgs: List[GsMessage],
        session: MessageSesion,
        bot_id: str,
    ):
        messages = MessageChain()
        message = await self._to_msg(gsmsgs, bot_id)

        messages.chain.extend(message)
        logger.info(f'【即将发送】[gsuid-core]: {messages}')
        await self.context.send_message(session, messages)


def store_file(path: Path, file: str):
    file_content = base64.b64decode(file)
    with open(path, 'wb') as f:
        f.write(file_content)


def del_file(path: Path):
    if path.exists():
        os.remove(path)


async def file_to_base64(file_path: Path):
    # 读取文件内容
    async with aiofiles.open(str(file_path), 'rb') as file:
        file_content = await file.read()

    # 将文件内容转换为base64编码
    base64_encoded = b64encode(file_content)

    # 将base64编码的字节转换为字符串
    base64_string = base64_encoded.decode('utf-8')

    return base64_string
