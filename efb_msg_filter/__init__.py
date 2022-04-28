# coding=utf-8
from os.path import exists
import uuid
from typing import Optional
from ehforwarderbot import Middleware, Message, coordinator, MsgType
from ehforwarderbot import utils as efb_utils
from requests import post
from threading import Timer
import time
import emoji as Emoji
import json
import yaml


class FilterMiddleware(Middleware):
    middleware_id: str = "rileysoong.msg_filter"
    middleware_name: str = "EFB MsgFilter Middleware"
    __version__: str = "0.0.4"

    config = {}
    """
        robot_wxid: "wxid_xxxxxxxxxxxxx"
        autoreply_delay: 1.5
        autoreply_freq: 0.3
        autoreply_wxid_extra: [...]
        autoreply_presets: [...]
    """
    autoreply = {
        "last_wxid": None,
        "last_ts": None
    }
    autoreply_tmpfile = {
        "timestamp": 0.0,
        "reply_text": ""
    }
    autoreply_tmpfile_path = str(efb_utils.get_data_path(middleware_id)) + '/' + 'cache'

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        self.load_config()

    def load_config(self):
        config_path = efb_utils.get_config_path(self.middleware_id)
        if not config_path.exists():
            return
        with config_path.open() as f:
            d = yaml.full_load(f)
            if not d:
                return
            self.config = d

    def load_autoreply_tmpfile(self):
        if not exists(self.autoreply_tmpfile_path):
            open(self.autoreply_tmpfile_path, 'w').close()
        with open(self.autoreply_tmpfile_path, 'r') as f:
            try:
                tmp = next(f).rstrip('\n')
                if tmp == 'x':
                    self.autoreply_tmpfile["timestamp"] = 99999999999.9999
                else:
                    self.autoreply_tmpfile["timestamp"] = float(tmp)
            except:
                self.autoreply_tmpfile["timestamp"] = 0.0
            try:
                next(f)
            except:
                ...
            self.autoreply_tmpfile["reply_text"] = f.read().rstrip('\n')

    def process_message(self, message: Message) -> Optional[Message]:
        if message.deliver_to != coordinator.master:  # sent from master
            if message.text.startswith('/ar'):
                self.load_autoreply_tmpfile()
                def get_presets_with_num():
                    ret = ''
                    for i in range(len(self.config['autoreply_presets'])):
                        if i == 0:
                            ret += f"[{i + 1}]    {self.config['autoreply_presets'][i]}"
                        else:
                            ret += f"\n[{i + 1}]    {self.config['autoreply_presets'][i]}"
                    return ret

                if message.text == '/ar d':
                    with open(self.autoreply_tmpfile_path, 'w') as f:
                        f.write("0.0\n\n" + str(self.autoreply_tmpfile['reply_text']))
                    tx = 'Disabled auto-reply below:\n\n' + str(self.autoreply_tmpfile['reply_text'])
                elif message.text == '/ar e':
                    with open(self.autoreply_tmpfile_path, 'w') as f:
                        f.write("x\n\n" + str(self.autoreply_tmpfile['reply_text']))
                    tx = 'Successfully Enabled auto-reply with:\n\n' + str(self.autoreply_tmpfile['reply_text'])
                elif message.text == '/ar p':
                    tx = f"You have {len(self.config['autoreply_presets'])} presets in total.\n\n" + \
                         get_presets_with_num()
                elif message.text.startswith('/ar p '):
                    index = int(message.text[-1])
                    with open(self.autoreply_tmpfile_path, 'w') as f:
                        f.write("x\n\n" + self.config['autoreply_presets'][index - 1])
                    tx = 'Successfully Enabled auto-reply with:\n\n' + self.config['autoreply_presets'][index - 1]
                else:
                    if self.autoreply_tmpfile['timestamp'] == 0.0:
                        tx = f"No auto-reply is in effect right now. You can use `/ar p [num]` to specify one of your {len(self.config['autoreply_presets'])} presets below:\n\n" + \
                             get_presets_with_num()
                    else:
                        tx = "Current auto-reply:\n\n" + \
                             self.autoreply_tmpfile['reply_text']

                author = message.chat.make_system_member(
                    uid="__rileysoong.msg_filter__",
                    name="Auto Relply Manager",
                    middleware=self
                )
                reply = Message(
                    uid=f"__middleware_example_{uuid.uuid4()}__",
                    text=tx,
                    chat=message.chat,
                    # author=author,  # Using the new chat we created before
                    author=message.chat.other,
                    type=MsgType.Text,
                    deliver_to=coordinator.master  # message is to be delivered to master
                )
                coordinator.send_message(reply)
                return None
        if message.chat.module_name == 'QQ Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if message.text == '收到':
                    return None
                elif message.uid[0:16] == '__group_notice__' and ') joined the group(' in message.text:
                    return None
                elif message.uid[0:16] == '__group_notice__' and ') quited the group(' in message.text:
                    return None
                elif message.uid[0:16] == '__group_notice__' and ') uploaded a file to group(' in message.text:
                    return None
        elif message.chat.module_name == 'WeChat Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if message.text == '收到':
                    return None
        elif message.chat.module_name == 'Wechat Pc Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if message.text == '收到':
                    return None
            elif str(message.chat).split(':')[0][1:] == 'PrivateChat':
                # Auto Reply
                def wxid_extra_match(wxid):
                    for i in self.config['autoreply_wxid_extra']:
                        if i == wxid:
                            return True
                    return False

                def wechatpc_send_msg(text, to_wxid):
                    msg = text
                    emojiList = Emoji.get_emoji_regexp().findall(text)
                    for emoji in emojiList:
                        msg = text.replace(emoji, '[@emoji=' + json.dumps(emoji).strip("\"") + ']')
                    param = {
                        'msg': msg,
                        'to_wxid': to_wxid,
                        'event': 'SendTextMsg',
                        'robot_wxid': self.config['robot_wxid'],
                    }
                    post('http://192.168.31.132:8090', headers={}, json=param, timeout=30)

                def too_frequently(current_ts, wxid):
                    rt = False
                    if self.autoreply["last_wxid"] == wxid:
                        if current_ts - self.autoreply["last_ts"] < 0.3:
                            # means too frequent
                            rt = True
                    self.autoreply["last_ts"] = current_ts
                    self.autoreply["last_wxid"] = wxid
                    return rt

                wxid = message.chat.uid
                # Match wxid
                if wxid.startswith('wxid_') or wxid_extra_match(wxid):
                    self.load_autoreply_tmpfile()
                    autoreply_tmpfile_til_ts = self.autoreply_tmpfile['timestamp']
                    current_ts = time.time()

                    # Match timestamp
                    if current_ts < autoreply_tmpfile_til_ts:
                        delay = self.config['autoreply_delay']
                        autoreply_content = self.autoreply_tmpfile['reply_text']
                        if not too_frequently(current_ts=current_ts, wxid=wxid):
                            Timer(delay, wechatpc_send_msg(autoreply_content, wxid))

                        # Modify the original message
                        message.text += '\n  - - - - - - Auto Replied - - - - - - \n' + autoreply_content
                        return message
        return message
