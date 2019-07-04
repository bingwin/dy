
from mod.user import *
from mod.Task import *
import json
import time
import requests
from queue import Queue

import os
from multiprocessing import Pool, Queue
import click



Severhttp = "http://192.168.6.254:8888/"



class IM(object):
    def getNewTask(self):  # 获取一个新任务
        task = Task()
        task.getTask()
        # task.task_info = json.loads("""{'task_data': {'id': 988, 'table_id': 14, 'channel_id': 42, 'type': 10, 'message_max': 45000, 'message_now': 18391, 'device_max': 180, 'device_number': 34, 'data': '{"link_url":"http://suxiaowuliu.com:8080/r/index.html?app=2551001","title":"\\u9644\\u8fd1\\u5bc2\\u5bde\\u5c11\\u5987\\uff0c\\u7ea6\\u4e48\\uff1f","desc":"\\u4e0d\\u95f2\\u804a\\u76f4\\u63a5\\u7ea6\\uff0c\\u6562\\u7ea6\\u6211\\u5c31\\u53bb","cover_url":"https://i.bmp.ovh/imgs/2019/06/3ab5b20843813d2b.png","voice_ids":"ef/30ebbaffe4f817bbfb63ad057131b7","type":"10"}', 'plan': 1, 'table_name': 'aweme_fans_v6', 'acc_cfg': {'city': '', 'gender': '2', 'follow_max': '500', 'fans_max': '30'}}, 'status': 0, 'msg': '没有帐号'}""")
        return task


    def getLocalTask(self): #获取本地任务
        db = Database()
        db.cursor.execute(''' Select * from os_task_bak''')
        task_list = db.cursor.fetchall()
        db.connet.close()
        db.cursor.close()
        return task_list

    def run(self,task):
        print("子进程开始执行>>> pid={},ppid={} args={}".format(os.getpid(), os.getppid(),type(task)))
        if task == None:
            print("开始获取新任务:")
            task = self.getNewTask()
            print("已经获取到任务:")
            if task.status == 1:
                db = Database()
                db.execute(['''
                   INSERT IGNORE INTO os_task_bak(uid,task_info,user_info) values('{}','{}','{}')
               '''.format(task.user_info.get("user_id"), json.dumps(task.task_info, ensure_ascii=False), json.dumps(task.user_info))])
        if task.status == 1:
            dinfo_b64= task.user_info.get("dinfo")
            #dinfo_b64 = "eyJpZGZhIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiZGV2aWNlX2lkIjoiNjgzOTI4MjgzOTEiLCJvc192ZXJzaW9uIjoiMTAuMiIsImRldmljZV90eXBlIjoiaVBob25lIDYiLCJvcGVudWRpZCI6IjRhMzhlNjY1OTA1MWU4MGRlYTAzYjExNDQwNTYzNzlkZjUzNWVkYmMiLCJpaWQiOiI3NjY2MjU2ODczNSIsInZpZCI6IjREMzM3MUJBLTk2RjgtNENERS05RkZGLTJGRjVCNTYyMUIyQSIsImNvb2tpZSI6InNpZF90dD1iOTFmODA0YWUwNmJkNmU2N2U2OTAyMjliZmE4YWM5YjtzZXNzaW9uaWQ9YjkxZjgwNGFlMDZiZDZlNjdlNjkwMjI5YmZhOGFjOWI7dWlkX3R0PTA4MTZmOTQzMzQzOTkzYzQ5NTFlMDIyMjYwODFhNWI2O2luc3RhbGxfaWQ9NzYyNzYyMzAyMDI7dHRyZXE9MSQ5OGZkMTg0MjI3NzkwZjdiZDUwYTUxMzMyOTllN2ZjNzVlZWFhMzllO29kaW5fdHQ9MTc5MzlkMDg1MWVlYzI5ZmI4MTJjMWQyMjdjZmYwNzQwZTA0N2UyYzY0YjdhNDM1MzYzNzE3N2YwYzdhMjE5YzUzZWM1MzlmMmRmNzA1N2NkMDAzZGYwZjU5MjIyYjRmO3NpZF9ndWFyZD1iOTFmODA0YWUwNmJkNmU2N2U2OTAyMjliZmE4YWM5YiU3QzE1NjIwNzY3MzklN0M0MzY3NjE1JTdDVGh1JTJDKzIyLUF1Zy0yMDE5KzAzJTNBMjUlM0E1NCtHTVQ7In0="
            dinfo = json.loads(base64.b64decode(dinfo_b64))
            user = User()
            user.content.get_http()
            cookie = requests.utils.cookiejar_from_dict(dict(p.split('=') for p in dinfo["cookie"].split(';') if p))
            user.content.device.openudid = dinfo["openudid"]
            user.content.device.idfa = dinfo["idfa"]
            user.content.device.vid = dinfo["vid"]
            user.content.device.install_id = dinfo["iid"]
            user.content.device.device_id = dinfo["device_id"]
            user.content.device.expansion = "{}"
            user.content.device.os_version = "10.2"
            user.content.device.screen_width = "750"
            user.content.device.device_type = "iPhone8,1"
            user.content.http.cookies = cookie
            user.userinfo()
            user.im_cloud_token()
            user.im_online()
            user.wss_start()
            tid = None
            if tid != None:
                target_userids = [tid]
            else:
                target_userids = user.follower_list()
            task_data = task.task_info.get("data")
            text = task_data.get("message_list")
            img_url = task_data.get("img_url")
            voice_url = task_data.get("voice_ids")
            img_bytes =None
            audio_bytes = None
            link_info = None
            if task.uids == None:
                task.uids = user.uids
            if img_url:
                voice_url = Severhttp + img_url
                img_bytes = utiles.get_byte(img_url)
            if voice_url:
                voice_url = Severhttp +"public/static/voice/"+ voice_url +".m4a"
                audio_bytes = utiles.get_byte(voice_url)
            if task_data["type"] == "10":
                link_info = dict()
                link_info["link_url"] = task_data["link_url"]
                link_info["cover_url"] = task_data["cover_url"]
                link_info["title"] = task_data["title"]
                link_info["desc"] = task_data["desc"]
            for target_userid in target_userids:
                print(task.uids)
                print("{} state : {}".format(target_userid,task.uids[str(target_userid)]["state"]))

                if str(task.uids[str(target_userid)]["state"]) == "0":
                    if text:
                        ret = user.wss_im_send(target_userid=target_userid, text=text)
                    if img_url:
                        ret = user.wss_im_send(target_userid=target_userid, img_bytes=img_bytes)
                    if voice_url:
                        ret = user.wss_im_send(target_userid=target_userid, audio_bytes=audio_bytes)
                    if link_info:
                        ret = user.wss_im_send(target_userid=target_userid, link_info=link_info)
                    if ret == True:
                        logger.info("{} 私信发送成功: {} -> {} {}".format(id, user.uid, target_userid, text))
                        user.im_success += 1
                        task.uids[str(target_userid)]["state"] =1
                        print(user.uids)
                        db= Database()
                        db.execute(['''UPDATE os_task set message_now = message_now +1 where id = {}'''.format(task.task_info.get("id")),
                                    '''UPDATE os_ch_pro_rel SET send_num = send_num + 1 WHERE channel_id = {} AND profile_id = {}'''.format(task.task_info.get("channel_id"),task.user_info.get("id")),
                                    """UPDATE os_task_bak SET uids = '{}' WHERE uid='{}'""".format(json.dumps(task.uids),task.user_info.get("user_id"))])
                    else:
                        logger.warning("{} 私信发送失败: {} -> {} {} -- {}".format(id, user.uid, target_userid, text, ret))
                        #user.content.get_http()
                else:
                    print("uid={} 已经私信过了 Pass".format(target_userid))
                time.sleep(1)
            else:
                print("task err:")


    def im(self,num):
        global _FUNC
        _FUNC = self.run
        self.poolMangaer(int(num))



    def poolMangaer(self,num): #进程池管理
        task_list = self.getLocalTask()
        queue = Queue()
        for task in task_list:
            queue.put(task)
        print('Parent process %s.' % os.getpid())
        start_time = time.time() * 1000
        p = Pool(num)
        while True:
            if queue.empty():
                print("备份队列为空")
                task = None
            else:
                print("取备份任务")
                bak_info = queue.get_nowait()
                task = Task()
                task.task_info = json.loads(bak_info.get("task_info"))
                task.user_info = json.loads(bak_info.get("user_info"))
                task.uids = json.loads(bak_info.get("uids")) if bak_info.get("uids") else None
                task.status = 1
            #添加任务到进城池
            time.sleep(5)
            p.apply_async(self.run, args=(task,))
        print('All subprocesses done.')
        p.close()
        p.join()




ims =IM()

from mod.user import *
from mod.Task import *
import json
import time
import requests
from queue import Queue

import os
from multiprocessing import Pool, Queue
import click



Severhttp = "http://192.168.6.254:8888/"



class IM(object):
    def getNewTask(self):  # 获取一个新任务
        task = Task()
        task.getTask()
        # task.task_info = json.loads("""{'task_data': {'id': 988, 'table_id': 14, 'channel_id': 42, 'type': 10, 'message_max': 45000, 'message_now': 18391, 'device_max': 180, 'device_number': 34, 'data': '{"link_url":"http://suxiaowuliu.com:8080/r/index.html?app=2551001","title":"\\u9644\\u8fd1\\u5bc2\\u5bde\\u5c11\\u5987\\uff0c\\u7ea6\\u4e48\\uff1f","desc":"\\u4e0d\\u95f2\\u804a\\u76f4\\u63a5\\u7ea6\\uff0c\\u6562\\u7ea6\\u6211\\u5c31\\u53bb","cover_url":"https://i.bmp.ovh/imgs/2019/06/3ab5b20843813d2b.png","voice_ids":"ef/30ebbaffe4f817bbfb63ad057131b7","type":"10"}', 'plan': 1, 'table_name': 'aweme_fans_v6', 'acc_cfg': {'city': '', 'gender': '2', 'follow_max': '500', 'fans_max': '30'}}, 'status': 0, 'msg': '没有帐号'}""")
        return task


    def getLocalTask(self): #获取本地任务
        db = Database()
        db.cursor.execute(''' Select * from os_task_bak''')
        task_list = db.cursor.fetchall()
        db.connet.close()
        db.cursor.close()
        return task_list

    def run(self,task):
        print("子进程开始执行>>> pid={},ppid={} args={}".format(os.getpid(), os.getppid(),type(task)))
        if task == None:
            print("开始获取新任务:")
            task = self.getNewTask()
            print("已经获取到任务:")
            if task.status == 1:
                db = Database()
                db.execute(['''
                   INSERT IGNORE INTO os_task_bak(uid,task_info,user_info) values('{}','{}','{}')
               '''.format(task.user_info.get("user_id"), json.dumps(task.task_info, ensure_ascii=False), json.dumps(task.user_info))])
        if task.status == 1:
            dinfo_b64= task.user_info.get("dinfo")
            #dinfo_b64 = "eyJpZGZhIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiZGV2aWNlX2lkIjoiNjgzOTI4MjgzOTEiLCJvc192ZXJzaW9uIjoiMTAuMiIsImRldmljZV90eXBlIjoiaVBob25lIDYiLCJvcGVudWRpZCI6IjRhMzhlNjY1OTA1MWU4MGRlYTAzYjExNDQwNTYzNzlkZjUzNWVkYmMiLCJpaWQiOiI3NjY2MjU2ODczNSIsInZpZCI6IjREMzM3MUJBLTk2RjgtNENERS05RkZGLTJGRjVCNTYyMUIyQSIsImNvb2tpZSI6InNpZF90dD1iOTFmODA0YWUwNmJkNmU2N2U2OTAyMjliZmE4YWM5YjtzZXNzaW9uaWQ9YjkxZjgwNGFlMDZiZDZlNjdlNjkwMjI5YmZhOGFjOWI7dWlkX3R0PTA4MTZmOTQzMzQzOTkzYzQ5NTFlMDIyMjYwODFhNWI2O2luc3RhbGxfaWQ9NzYyNzYyMzAyMDI7dHRyZXE9MSQ5OGZkMTg0MjI3NzkwZjdiZDUwYTUxMzMyOTllN2ZjNzVlZWFhMzllO29kaW5fdHQ9MTc5MzlkMDg1MWVlYzI5ZmI4MTJjMWQyMjdjZmYwNzQwZTA0N2UyYzY0YjdhNDM1MzYzNzE3N2YwYzdhMjE5YzUzZWM1MzlmMmRmNzA1N2NkMDAzZGYwZjU5MjIyYjRmO3NpZF9ndWFyZD1iOTFmODA0YWUwNmJkNmU2N2U2OTAyMjliZmE4YWM5YiU3QzE1NjIwNzY3MzklN0M0MzY3NjE1JTdDVGh1JTJDKzIyLUF1Zy0yMDE5KzAzJTNBMjUlM0E1NCtHTVQ7In0="
            dinfo = json.loads(base64.b64decode(dinfo_b64))
            user = User()
            user.content.get_http()
            cookie = requests.utils.cookiejar_from_dict(dict(p.split('=') for p in dinfo["cookie"].split(';') if p))
            user.content.device.openudid = dinfo["openudid"]
            user.content.device.idfa = dinfo["idfa"]
            user.content.device.vid = dinfo["vid"]
            user.content.device.install_id = dinfo["iid"]
            user.content.device.device_id = dinfo["device_id"]
            user.content.device.expansion = "{}"
            user.content.device.os_version = "10.2"
            user.content.device.screen_width = "750"
            user.content.device.device_type = "iPhone8,1"
            user.content.http.cookies = cookie
            user.userinfo()
            user.im_cloud_token()
            user.im_online()
            user.wss_start()
            tid = None
            if tid != None:
                target_userids = [tid]
            else:
                target_userids = user.follower_list()
            task_data = task.task_info.get("data")
            text = task_data.get("message_list")
            img_url = task_data.get("img_url")
            voice_url = task_data.get("voice_ids")
            img_bytes =None
            audio_bytes = None
            link_info = None
            if task.uids == None:
                task.uids = user.uids
            if img_url:
                voice_url = Severhttp + img_url
                img_bytes = utiles.get_byte(img_url)
            if voice_url:
                voice_url = Severhttp +"public/static/voice/"+ voice_url +".m4a"
                audio_bytes = utiles.get_byte(voice_url)
            if task_data["type"] == "10":
                link_info = dict()
                link_info["link_url"] = task_data["link_url"]
                link_info["cover_url"] = task_data["cover_url"]
                link_info["title"] = task_data["title"]
                link_info["desc"] = task_data["desc"]
            for target_userid in target_userids:
                print(task.uids)
                print("{} state : {}".format(target_userid,task.uids[str(target_userid)]["state"]))

                if str(task.uids[str(target_userid)]["state"]) == "0":
                    if text:
                        ret = user.wss_im_send(target_userid=target_userid, text=text)
                    if img_url:
                        ret = user.wss_im_send(target_userid=target_userid, img_bytes=img_bytes)
                    if voice_url:
                        ret = user.wss_im_send(target_userid=target_userid, audio_bytes=audio_bytes)
                    if link_info:
                        ret = user.wss_im_send(target_userid=target_userid, link_info=link_info)
                    if ret == True:
                        logger.info("{} 私信发送成功: {} -> {} {}".format(id, user.uid, target_userid, text))
                        user.im_success += 1
                        task.uids[str(target_userid)]["state"] =1
                        print(user.uids)
                        db= Database()
                        db.execute(['''UPDATE os_task set message_now = message_now +1 where id = {}'''.format(task.task_info.get("id")),
                                    '''UPDATE os_ch_pro_rel SET send_num = send_num + 1 WHERE channel_id = {} AND profile_id = {}'''.format(task.task_info.get("channel_id"),task.user_info.get("id")),
                                    """UPDATE os_task_bak SET uids = '{}' WHERE uid='{}'""".format(json.dumps(task.uids),task.user_info.get("user_id"))])
                    else:
                        logger.warning("{} 私信发送失败: {} -> {} {} -- {}".format(id, user.uid, target_userid, text, ret))
                        #user.content.get_http()
                else:
                    print("uid={} 已经私信过了 Pass".format(target_userid))
                time.sleep(1)
            else:
                print("task err:")


    def im(self,num):
        global _FUNC
        _FUNC = self.run
        self.poolMangaer(int(num))



    def poolMangaer(self,num): #进程池管理
        task_list = self.getLocalTask()
        queue = Queue()
        for task in task_list:
            queue.put(task)
        print('Parent process %s.' % os.getpid())
        start_time = time.time() * 1000
        p = Pool(num)
        while True:
            if queue.empty():
                print("备份队列为空")
                task = None
            else:
                print("取备份任务")
                bak_info = queue.get_nowait()
                task = Task()
                task.task_info = json.loads(bak_info.get("task_info"))
                task.user_info = json.loads(bak_info.get("user_info"))
                task.uids = json.loads(bak_info.get("uids")) if bak_info.get("uids") else None
                task.status = 1
            #添加任务到进城池
            time.sleep(5)
            p.apply_async(self.run, args=(task,))
        print('All subprocesses done.')
        p.close()
        p.join()




ims =IM()
ims.im(3)



