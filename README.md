# efb-msg-filter

Filter Only Shoudao Message Only for EQS.  

# Notice

- This script is very poorly written, works only with EQS. If you have EWS, it might NOT function normally!!!
- It blocks "收到" message from group chat. Messages from private chat won't be effected at all.
- If you wish to block other message from group chat, there isn't a conf file for now. Feel free to fork/copy this repository then rewrite it. Or you can simply add another if in the script.

# Installation

```
# pip3 install git+https://github.com/1ndeed/efb-msg-filter
```
