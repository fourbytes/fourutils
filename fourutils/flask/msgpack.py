import msgpack

from . import RedisSessionInterface


class MsgpackRedisSessionInterface(RedisSessionInterface):
    serializer = msgpack