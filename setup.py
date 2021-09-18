from setuptools import setup

setup(
    name='efb-msg-filter',
    version='0.0.1',
    description='Filter Only Shoudao Message Only for EQS.'
    author='Riley Soong',
    auther_email='aurman@qq.com',
    url='https://github.com/1ndeed/efb-msg-filter',
    install_requires=[
        "ehforwarderbot"
    ],
    entry_points={
        "ehforwarderbot.middleware": "rileysoong.msg_filter = efb_msg_filter:FilterMiddleware"
    }
    )
