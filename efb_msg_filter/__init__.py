# coding=utf-8

from typing import Optional
from ehforwarderbot import Middleware, Message

class FilterMiddleware(Middleware):
    middleware_id: str = "rileysoong.msg_filter"
    middleware_name: str = "EFB MsgFilter Middleware"
    __version__: str = "0.0.2"

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)

    def process_message(self, message: Message) -> Optional[Message]:
        if message.chat.uid.split('_',1)[0] == 'group':
            if   message.text == '收到':
                return None
            elif message.uid[0:16] == '__group_notice__' and ') joined the group(' in message.text:
                return None
            elif message.uid[0:16] == '__group_notice__' and ') quited the group(' in message.text:
                return None
            elif message.uid[0:16] == '__group_notice__' and ') uploaded a file to group(' in message.text:
                return None
        return message
