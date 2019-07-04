

import pymysql

from pymysql.cursors import DictCursor


class Database():
    config = {
        "host": "192.168.6.254",
        "user": "root",
        "password": "123123cp",
        "database": "aweme",
        "charset": "utf8"
    }

    connet = ''
    cursor = ''
    def __init__(self):
        self.connet = pymysql.connect(**self.config)
        self.cursor = self.connet.cursor(DictCursor)

    def execute(self,sqls):
        try:
            for sql in sqls:
                self.cursor.execute(sql)
        except:
            # 如果发生错误则回滚
            print("Error: execute"+sql)
            self.connet.rollback()
        else:
            self.connet.commit()
        self.connet.close()
        self.cursor.close()

    def checkAll(self,sql):
        fetchall = None
        try:
            self.cursor.execute(sql)
            fetchall = self.cursor.fetchall()
        except:
            # 如果发生错误则回滚
            print("Error: checkAll:"+sql)
            self.connet.rollback()

        self.connet.close()
        self.cursor.close()
        return fetchall

    def checkOne(self, sql):
        try:
            self.cursor.execute(sql)
            fetchone = self.cursor.fetchone()
        except:
            # 如果发生错误则回滚
            print("Error: checkOne:" + sql)
            self.connet.rollback()

        self.connet.close()
        self.cursor.close()
        return fetchone
