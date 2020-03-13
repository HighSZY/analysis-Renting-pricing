import logging

import pymysql as pq


class SelfMysql:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        logging.info('\t连接数据库--doing--\t')
        self.conn = pq.connect(**kwargs)
        logging.info('\t数据库连接--done--\t')

    def get_cursor(self, tpe=pq.cursors.DictCursor):
        return self.conn.cursor()

    def exec(self, order):
        logging.info('\tmysql、order--执行--doing\t')
        try:
            self.valid_conn()
            with self.get_cursor() as cursor:
                res = cursor.execute(order)
            logging.info('\t{}--执行--Done\t'.format(order))
        except Exception as e:
            logging.info('\t{}--执行--Error--{}'.format(order, e))
        self.conn.commit()
        return res

    def valid_conn(self):
        try:
            self.conn.ping()
            logging.info('\t数据库活跃')
        except Exception as e:
            logging.info('\t数据库断开--{}'.format(e))