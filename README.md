# efb-msg-filter

Advanced Features For [EQS](https://github.com/milkice233/efb-qq-slave), [EWCS](https://github.com/0honus0/efb-wechat-cutecat-slave), [EWS](https://github.com/ehforwarderbot/efb-wechat-slave).

# Features

- In group messages. Mute the first "收到" and merge the rest.  
- Also, it blocks some group system messages from EQS and EWCS like "... joined the group ...".  
- Configure Auto-reply feature for EWCS.

# Installation

```
# pip3 install git+https://github.com/iaurman/efb-msg-filter
```

# Configuration

`~/.ehforwarderbot/profiles/default/rileysoong.msg_filter/config.yaml`

```
robot_wxid: wxid_qwericc1cbcfgh      # 可爱猫的robot_wxid也就是你的wxid
autoreply_delay: 1.5                 # 收到消息后和发送自动回复之间的延迟
autoreply_freq: 0.3                  # 多少秒后开始下一次自动回复（防止同时多条消息回复刷屏）
autoreply_wxid_extra:              # 本项目只匹配wxid开头为wxid_的好友
  - somecoolname                   # 目的是防止回复一些公众号或微信官方服务
  - nobiesaster69                  # 但一些老微信号的wxid不以wxid_开头
  - gonnadothis                    # 你需要手动获取这些账号的wxid，并在此文件贴出
autoreply_presets:
  - 少爷正在度假⛱️⛱️，QQ、微信消息提醒均已关闭，有重要事情请直接打电话:-)
  - 少爷正在睡觉💤💤，手机已静音，无法收到消息，你打电话他都听不到的:-)
```

# Commands in Telegram

Auto-Reply Feature
```
/ar d    Disable auto-reply
/ar e    Enable auto-reply
/ar p    Print all presets
/ar -h   Print this info
/ar      Current status
```

Merge "收到" Feature
```
/sdc     Expire the last "Shoudao" merge immediately.
         (default expire time is 12 hours)
```
