import random
import json
import time
import requests
from mod.db import *

class Task():
    task_info = None
    user_info = None
    status = 0
    msg = None
    task_list = []
    uids = None
    accid = None
    uploadFail = 0
    def __int__(self):
        self.task_info = None
        self.user_info = None
        self.uids = None

    def getTask(self):
        """

            Select t.id,t.table_id,t.channel_id,t.type,t.message_max,t.message_now,t.device_max,t.device_number,t.data,t.plan,ft.table_name as  table_name,ft.acc_cfg 
            from os_task as t left join os_aweme_fans_table as ft on ft.id = t.table_id 
            where t.status = 1

            Select t.id,t.table_id,t.channel_id,t.type,t.message_max,t.message_now,t.device_max,t.device_number,t.data,t.plan,ft.table_name as  table_name,ft.acc_cfg
           from os_task as t left join os_aweme_fans_table as ft on ft.id = t.table_id
           where t.status = 0 and t.id = 984
        ''')

        """
        db = Database()
        # 取可用任务列表
        task_list=db.checkAll('''
            Select t.id,t.table_id,t.channel_id,t.type,t.message_max,t.message_now,t.device_max,t.device_number,t.data,t.plan,ft.table_name as  table_name,ft.acc_cfg 
            from os_task as t left join os_aweme_fans_table as ft on ft.id = t.table_id 
            where t.status = 1 and t.send_type = 2 
        ''')
        random.shuffle(task_list)
        self.task_info = []
        for value in task_list:  # 遍历任务列表 取未完成任务 并关闭已完成任务
            if value["message_max"] <= value["message_now"]:
                db = Database()
                db.execute([''' update os_task set status = 0 where id = %i''' % value["id"]])
                continue
            if value["device_number"] >= value["device_max"]:
                continue
            self.task_info = value
            break
        if len(self.task_info) > 0:
            od = "send_at DESC" if self.task_info['plan'] == 2 else "send_at ASC"
            self.task_info['acc_cfg'] = json.loads(self.task_info['acc_cfg'])
            self.task_info['data'] = json.loads(self.task_info['data'])
            fans_max = "50" if self.task_info["acc_cfg"]['fans_max'] == "" else self.task_info["acc_cfg"]['fans_max']
            cd_time = int(time.time()) - 60 * 60 * 10
            db = Database()
            #取帐号 静默时间周期是 10小时
            result = db.checkOne('''
                   SELECT `id`,`group_id`,`user_id`,`username`,`password`,`fans_count`,`following_count`,`cookies`,`data63`,`dinfo` 
                   FROM os_aweme_profile 
                   WHERE NOT EXISTS 
                            (SELECT profile_id FROM os_ch_pro_rel 
                              WHERE channel_id = %s AND os_aweme_profile.id = os_ch_pro_rel.profile_id) AND  group_id = %s AND status = 1 AND fans_count >= %s AND send_at < %i AND dinfo != ""
                              ORDER BY %s LIMIT 1 FOR UPDATE 
            ''' % (self.task_info["channel_id"], self.task_info["table_id"], fans_max, cd_time, od))
            if result:

                self.user_info = result  # 一个base64后的json数据 包含cookies 和 设备信息
                self.status = 1
                db = Database()
                #插入帐号关系表 更新帐号使用时间
                db.execute(['''INSERT IGNORE INTO os_ch_pro_rel (channel_id,profile_id) VALUES ('{}','{}')'''.format(self.task_info["channel_id"], result["id"]),
                            ''' update os_aweme_profile set send_at = {} where id = {}'''.format(int(time.time()), result["id"]),
                            ''' update os_task set device_number = device_number +1 where id = {}'''.format(self.task_info["id"]),
                            ])
            else:
                self.status = 0
                self.msg = "没有帐号"
            """
         
                cursor.execute('''  
                    INSERT IGNORE INTO os_ch_pro_rel (channel_id,profile_id) VALUES ('%s','%s')
                ''' %(task["channel_id"],result["id"]))
                cursor.execute('''  
                    update os_aweme_profile set send_at = %i where id = %s  
                ''' % (int(time.time()), result["id"]))
            """
        else:
            self.status = 0
            self.msg = "没有任务"

