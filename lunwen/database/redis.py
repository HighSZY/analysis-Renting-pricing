import redis
import logging
from redis import ConnectionPool


class SelfRedis:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, host='134.175.16.232', port=6379, password='2168', db=0, **kwargs):
        self.dt = {
            'host': host,
            'port': port,
            'password': password,
            'db': db
        }
        self._reset_conn_pool()

    def _reset_conn_pool(self):
        self.conn_pool = ConnectionPool(**self.dt)

    def get_redis_conn(self):
        return redis.Redis(connection_pool=self.conn_pool)

    @staticmethod
    def valid_conn(redis_conn=None):
        try:
            is_or_not_right = redis_conn.ping()
        except Exception:
            return False
        return is_or_not_right

    def exec_rpush(self, key, content):
        with self.get_redis_conn() as conn:
            conn.rpush(key, content)
        logging.info('\t{} {} 写入完成'.format(key, content))