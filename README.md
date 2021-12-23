# efb-msg-filter

Filter Shoudao message for both [EWS](https://github.com/ehforwarderbot/efb-wechat-slave) and [EQS](https://github.com/milkice233/efb-qq-slave).  

# Purpose

- Block "收到" message from group chats in EQS and EWS. Messages from private chats won't be effected at all.  
- Also, it blocks some group system messages from cqhttp (an EQS client) like " joined the group ".  

# Notice

If you wish to block other messages, see this as a template. I didn't bother to write a conf file. Feel free to fork.  

# Installation

```
# pip3 install git+https://github.com/1ndeed/efb-msg-filter
```
