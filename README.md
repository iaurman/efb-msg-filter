# efb-msg-filter

Advanced Features For [EQS](https://github.com/milkice233/efb-qq-slave), [EWCS](https://github.com/0honus0/efb-wechat-cutecat-slave), [EWS](https://github.com/ehforwarderbot/efb-wechat-slave).

# Features

- In group messages. Mute the first "收到" and merge the rest.  
- Also, it blocks some group system messages from EQS and EWCS like "... joined the group ...".  
- Configure Auto-reply feature for EWCS.

# Installation

```
# pip3 install git+https://github.com/1ndeed/efb-msg-filter
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
