# coding=utf-8
from os.path import exists
import uuid
from typing import Optional
from ehforwarderbot import Middleware, Message, coordinator, MsgType
from ehforwarderbot.chat import ChatNotificationState
from typing import Any
from ehforwarderbot import utils as efb_utils
from ehforwarderbot.types import MessageID
from requests import post
from threading import Timer
import time
import emoji as Emoji
import json
import yaml


class FilterMiddleware(Middleware):
    middleware_id: str = "rileysoong.msg_filter"
    middleware_name: str = "EFB MsgFilter Middleware"
    __version__: str = "0.1.0"

    config = {}
    """
        robot_wxid: "wxid_xxxxxxxxxxxxx"
        autoreply_delay: 1.5
        autoreply_freq: 0.3
        autoreply_wxid_extra: [...]
        autoreply_presets: [...]
        access_token: "1234567890"
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
    sdb = {}
    gndb = {}
    """
        "[group_id]":
        {
            time: "1234567890",
            text: "abc",
            uid: "8908ds_sadjd_3dkajs"
        }
    """

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        self.load_config()
        self.load_autoreply_tmpfile()

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
            except StopIteration:
                self.autoreply_tmpfile["timestamp"] = 0.0
            try:
                next(f)
                self.autoreply_tmpfile["reply_text"] = f.read().rstrip('\n')
            except StopIteration:
                ...

    def command_handler_ar(self, message: Message):
        def get_presets_with_num():
            ret = ''
            for i in range(len(self.config['autoreply_presets'])):
                if i == 0:
                    ret += f"[{i + 1}]    {self.config['autoreply_presets'][i]}"
                else:
                    ret += f"\n[{i + 1}]    {self.config['autoreply_presets'][i]}"
            return ret

        self.load_autoreply_tmpfile()

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
        elif message.text.startswith('/ar -h') or message.text.startswith('/ar --help') or message.text.startswith(
                '/ar —help'):
            tx = "/ar d    Disable auto-reply\n" \
                 "/ar e    Enable auto-reply\n" \
                 "/ar p    Print all presets\n" \
                 "/ar -h   Print this info\n" \
                 "/ar      Current status"
        else:
            if self.autoreply_tmpfile['timestamp'] == 0.0:
                tx = f"No auto-reply is in effect right now. " \
                     f"You can use `/ar p [num]` to specify one of your " \
                     f"{len(self.config['autoreply_presets'])} presets below:\n\n" + \
                     get_presets_with_num()
            else:
                tx = "Current auto-reply:\n\n" + \
                     self.autoreply_tmpfile['reply_text']

        self.load_autoreply_tmpfile()

        reply = Message(
            uid=f"__middleware_example_{uuid.uuid4()}__",
            text=tx,
            chat=message.chat,
            author=message.chat.members[1],
            type=MsgType.Text,
            deliver_to=coordinator.master  # message is to be delivered to master
        )
        coordinator.send_message(reply)

    def command_handler_sd(self, message: Message):
        group_ip = message.chat.uid
        if group_ip not in self.sdb:
            return None
        msg_id = self.sdb[group_ip]["uid"]
        text = self.sdb[group_ip]["text"]
        self.sdb.pop(group_ip)

        author = message.chat.make_system_member(
            uid="__rileysoong.msg_filter__",
            name="EFB Console",
            middleware=self
        )
        editmsg = Message(
            edit=True,
            uid=msg_id,
            text='&' + text,
            chat=message.chat,
            # author=author,  # Using the new chat we created before
            author=author,
            type=MsgType.Text,
            deliver_to=coordinator.master  # message is to be delivered to master
        )
        coordinator.send_message(editmsg)

    def auto_reply(self, message: Message):
        def wxid_extra_match(iwxid):
            for i in self.config['autoreply_wxid_extra']:
                if i == iwxid:
                    return True
            return False

        def wechatpc_send_msg(text, to_wxid) -> Any:
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
            post('http://192.168.122.132:8090', headers={"Authorization": self.config['access_token']}, json=param, timeout=30)

        def too_frequently(icurrent_ts, iwxid):
            rt = False
            if self.autoreply["last_wxid"] == iwxid:
                if icurrent_ts - self.autoreply["last_ts"] < 0.3:
                    # means too frequent
                    rt = True
            self.autoreply["last_ts"] = icurrent_ts
            self.autoreply["last_wxid"] = iwxid
            return rt

        # If auto-reply is not enabled
        if self.autoreply_tmpfile['timestamp'] == 0.0:
            return message

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
                if not too_frequently(current_ts, wxid):
                    Timer(delay, wechatpc_send_msg(autoreply_content, wxid))

                # Modify the original message
                message.text += '\n  - - - - - - Auto Replied - - - - - - \n' + autoreply_content
        return message

    @staticmethod
    def matched_irr(text):
        mlist = ["0", "1", "2", "00", "000", "11", "111", "22", "222"]
        for i in mlist:
            if text == i:
                return True
        return False

    @staticmethod
    def matched_shoudao(text):
        mlist = ["收到", " 收到", "收到 ", "收到！", "收到!", "收到.", "收到。",
                 "收到啦", "收到啦！", "收到啦！", "shoudao", "瘦到"]
        for i in mlist:
            if text == i:
                return True
        return False

    def shoudao(self, message: Message):
        def get_name():
            if message.author.alias == '' or message.author.alias is None:
                return message.author.name
            else:
                return message.author.alias

        def implement():
            message.text = '收到: ' + get_name()
            # Record in Shoudao db
            self.sdb[message.chat.uid] = {
                'time': time.time(),
                'text': message.text,
                'uid': message.uid
            }
            message.author = sys_author
            message.chat.notification = ChatNotificationState.NONE
            return message

        sys_author = message.chat.make_system_member(
            uid="__rileysoong.msg_filter.shoudao__",
            name="EFB Console",
            middleware=self
        )
        # If it's the FIRST shoudao
        if message.chat.uid not in self.sdb:
            return implement()
        # It's a shoudao that needs to be appended to the last shoudao bubble
        else:
            # The original shoudao should be valid only within 12 hours
            if time.time() - self.sdb[message.chat.uid]["time"] < 43200.0:
                # Update Msg
                self.sdb[message.chat.uid]["text"] = self.sdb[message.chat.uid]["text"] + ', ' + get_name()

                message.edit = True
                message.uid = MessageID(self.sdb[message.chat.uid]["uid"])
                message.type = MsgType.Text
                message.text = self.sdb[message.chat.uid]["text"]
                message.author = sys_author
                message.chat.notification = ChatNotificationState.NONE

                return message
            # If not, implement a new one
            else:
                return implement()

    def groupNotice(self, message: Message):
        def implement():
            message.text = '群待办: ' +  "1" + " person"
            # Record in Shoudao db
            self.gndb[message.chat.uid] = {
                'time': time.time(),
                'text': message.text,
                'uid': message.uid,
                'count': 1
            }
            message.author = sys_author
            message.chat.notification = ChatNotificationState.NONE
            return message

        sys_author = message.chat.make_system_member(
            uid="__rileysoong.msg_filter.shoudao__",
            name="EFB Console",
            middleware=self
        )
        # If it's the FIRST shoudao
        if message.chat.uid not in self.gndb:
            return implement()
        # It's a shoudao that needs to be appended to the last shoudao bubble
        else:
            # The original shoudao should be valid only within 12 hours
            if time.time() - self.gndb[message.chat.uid]["time"] < 43200.0:
                # Update Msg
                self.gndb[message.chat.uid]["count"] += 1
                self.gndb[message.chat.uid]["text"] = '群待办: ' + str(self.gndb[message.chat.uid]["count"]) + ' persons'

                message.edit = True
                message.uid = MessageID(self.gndb[message.chat.uid]["uid"])
                message.type = MsgType.Text
                message.text = self.gndb[message.chat.uid]["text"]
                message.author = sys_author
                message.chat.notification = ChatNotificationState.NONE

                return message
            # If not, implement a new one
            else:
                return implement()

    def process_message(self, message: Message) -> Optional[Message]:
        debug = False
        if debug:
            with open('/zzz/log.efb', 'a') as fw:
                fw.write(str(message.__dict__) + '\n\n')

        if message.deliver_to != coordinator.master:  # Message From Master
            if message.text.startswith('/ar'):
                self.command_handler_ar(message)
                return None
            elif message.text.startswith('/sdc'):
                self.command_handler_sd(message)
                return None

        elif message.chat.module_name == 'QQ Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if self.matched_shoudao(message.text):
                    return self.shoudao(message)
                elif self.matched_irr(message.text):
                    message.chat.notification = ChatNotificationState.NONE
                elif message.substitutions is not None and message.chat.uid == 'group_106789751':
                    message.substitutions = None
                elif message.uid[0:16] == '__group_notice__' and ') joined the group(' in message.text:
                    return None
                elif message.uid[0:16] == '__group_notice__' and ') quited the group(' in message.text:
                    return None
                elif message.uid[0:16] == '__group_notice__' and ') uploaded a file to group(' in message.text:
                    return None

        elif message.chat.module_name == 'WeChat Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if self.matched_shoudao(message.text):
                    return self.shoudao(message)
                elif self.matched_irr(message.text):
                    message.chat.notification = ChatNotificationState.NONE

        elif message.chat.module_name == 'Wechat Pc Slave':
            if str(message.chat).split(':')[0][1:] == 'GroupChat':
                if self.matched_shoudao(message.text):
                    return self.shoudao(message)
                elif self.matched_irr(message.text):
                    message.chat.notification = ChatNotificationState.NONE
                elif message.text == "  - - - - - - - - - - - - - - - \n发布/完成 了一个群待办":
                    return self.groupNotice(message)
                elif message.text == None:
                    pass
                elif ' 邀请 ' in message.text and ' 加入了群聊' in message.text:
                    return None
                elif ' invited ' in message.text and ' to the group chat' in message.text:
                    return None
                elif ' joined the group chat via the QR Code shared by ' in message.text:
                    return None
                elif ' 离开了群聊' in message.text:
                    return None
            elif str(message.chat).split(':')[0][1:] == 'PrivateChat':
                # Auto-Reply Feature
                message = self.auto_reply(message)
        return message
