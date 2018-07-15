import msgpack

from .PickleRedisSessionInterface import RedisSessionInterface


class MsgpackRedisSessionInterface(RedisSessionInterface):
    serializer = msgpack