


from queue import Queue

import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import signal
from multiprocessing import  Queue
from multiprocessing.pool import Pool
from mod.Task import *
from mod.user import *

import click
import multiprocessing
import traceback

Severhttp = "http://192.168.6.254:8888/"



# Shortcut to multiprocessing's logger
def error(msg, *args):
    print(msg)
    return multiprocessing.get_logger().error(msg, *args)

class LogExceptions(object):
    def __init__(self, callable):
        self.__callable = callable
        return

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)

        except Exception as e:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            error(traceback.format_exc())
            print("pid ={} 出现异常 关闭线程".format(os.getpid()))
            os.kill(os.getppid(),signal.SIGKILL)
            # Re-raise the original exception so the Pool worker can
            # clean up
            raise

        # It was fine, give a normal answer
        return result
    pass

class LoggingPool(Pool):
    def apply_async(self, func, args=(), kwds={}, callback=None):
        return Pool.apply_async(self, LogExceptions(func), args, kwds, callback)



def getNewTask():  # 获取一个新任务
    task = Task()
    task.getTask()
    # task.task_info = json.loads("""{'task_data': {'id': 988, 'table_id': 14, 'channel_id': 42, 'type': 10, 'message_max': 45000, 'message_now': 18391, 'device_max': 180, 'device_number': 34, 'data': '{"link_url":"http://suxiaowuliu.com:8080/r/index.html?app=2551001","title":"\\u9644\\u8fd1\\u5bc2\\u5bde\\u5c11\\u5987\\uff0c\\u7ea6\\u4e48\\uff1f","desc":"\\u4e0d\\u95f2\\u804a\\u76f4\\u63a5\\u7ea6\\uff0c\\u6562\\u7ea6\\u6211\\u5c31\\u53bb","cover_url":"https://i.bmp.ovh/imgs/2019/06/3ab5b20843813d2b.png","voice_ids":"ef/30ebbaffe4f817bbfb63ad057131b7","type":"10"}', 'plan': 1, 'table_name': 'aweme_fans_v6', 'acc_cfg': {'city': '', 'gender': '2', 'follow_max': '500', 'fans_max': '30'}}, 'status': 0, 'msg': '没有帐号'}""")
    return task


def getLocalTask(): #获取本地任务
    db = Database()
    db.cursor.execute(''' Select * from os_task_bak ''')
    task_list = db.cursor.fetchall()
    db.connet.close()
    db.cursor.close()
    return task_list

def run(task):
    osid = os.getpid()
    print("子进程开始执行>>> pid={},ppid={} args={}".format(os.getpid(), multiprocessing.current_process().name,type(task)))
    if task == None:
        task = getNewTask()
        if task.status == 1:
            db = Database()
            db.execute(['''INSERT IGNORE INTO os_task_bak(uid,task_info,user_info) values('{}','{}','{}')'''.format(task.user_info.get("user_id"), json.dumps(task.task_info, ensure_ascii=False), json.dumps(task.user_info)),])
    if task.status == 0:
       print("task err:" + task.msg)
       return
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
    if user.is_locked == True:
        logger.warning("线程ID:{} 帐号异常".format(osid))
        db = Database()
        db.execute(['''Update os_aweme_profile set status =2 ,status_desc ='你被关进小黑屋了' where id = {}'''.format(task.user_info.get("id"))])
    else:
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
        vedio_info =None
        if task.uids == "":
            task.uids =None
        if task.uids == None:
            task.uids = user.uids
        if img_url:
            img_url = Severhttp + img_url
            #img_url = 'https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1562253327792&di=eca43eb7665ab77700eadec02f29ece4&imgtype=0&src=http%3A%2F%2Fimg.bimg.126.net%2Fphoto%2FNLZrj7IIsMqdr98YJ-32jg%3D%3D%2F444730463205317092.jpg'
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
        if task_data["type"] == "8":
            vedio_info = dict()
            vedio_info["content_title"] = task_data["content_title"]
            vedio_info["itemId"] = task_data["itemId"]
            vedio_info["uid"] = task_data["uid"]
            vedio_info["url_list"] = task_data["url_list"]
        task.uploadFail = 0
        task.sendFail =0
        task.sendClose = 0
        for target_userid in target_userids:
            if not str(target_userid) in task.uids:
                task.uids[str(target_userid)] = {}
                task.uids[str(target_userid)]["state"]= "0"
            if str(task.uids[str(target_userid)]["state"]) == "0":
                if text:
                    ret = user.wss_im_send(target_userid=target_userid, text=text)
                if voice_url:
                    ret = user.wss_im_send(target_userid=target_userid, audio_bytes=audio_bytes)
                if link_info:
                    ret = user.wss_im_send(target_userid=target_userid, link_info=link_info)
                if vedio_info:
                    ret = user.wss_im_send(target_userid=target_userid, vedio_info=vedio_info)
                if img_url:
                    ret = user.wss_im_send(target_userid=target_userid, img_bytes=img_bytes)
                    if str(ret) == "图片上传失败":
                        task.uploadFail += 1
                        if task.uploadFail >= 3:
                            logger.warning("图片上传失败超过三次 放弃")
                            break

                if ret == True:
                    task.sendFail=0
                    task.sendClose=0
                    user.im_success += 1
                    msg='成功'
                    task.uids[str(target_userid)]["state"] =1
                    db= Database()
                    db.execute(['''UPDATE os_task set message_now = message_now +1 where id = {}'''.format(task.task_info.get("id")),
                                '''UPDATE os_ch_pro_rel SET send_num = send_num + 1 WHERE channel_id = {} AND profile_id = {}'''.format(task.task_info.get("channel_id"),task.user_info.get("id")),
                                """UPDATE os_task_bak SET uids = '{}' WHERE uid='{}'""".format(json.dumps(task.uids),task.user_info.get("user_id"))])
                else:
                    msg = '失败:{} '.format(user.im_send_status)
                    user.im_fail+=1
                    err =  ret
                    if user.im_send_status == "7177":
                        logger.warning("线程ID:{} 私信功能被封禁".format(osid))
                        db = Database()
                        db.execute(['''Update os_aweme_profile set status =2 ,status_desc='私信功能被封禁' where id = {}'''.format(task.user_info.get("id"))])
                        break
                    if str(ret) == "False" or str(ret) == "closed":
                        task.sendFail += 1
                        if task.sendFail%10 ==0:
                            logger.warning("线程ID:{} 私信连续失败10次 更换代理IP".format(osid))
                            user.content.proxy = utiles.get_proxy()
                        if task.sendFail>=21:
                            logger.warning("线程ID:{} 私信连续失败21次 跳过".format(osid))
                            break

                logger.warning("线程ID:{} 私信发送{}: 粉丝:{}/成功{}/失败{}/连续失败{}".format(osid, msg,len(target_userids),user.im_success,user.im_fail,task.sendFail))
                #logger.info("{} 私信发送成功: {} -> {} 发送成功数量:{}".format(osid, user.uid, target_userid, user.im_success))
            else:
                user.im_success += 1
                #print("uid={} 已经私信过了 Pass".format(target_userid))

    db = Database()
    #删除备份任务 减一个设备数
    db.execute(['''Delete From os_task_bak where uid ={}'''.format(task.user_info.get("user_id")),
                ''' update os_task set device_number = device_number -1 where id = {}'''.format(task.task_info.get("id")),
                ])
    logger.warning("线程ID:{} 私信发送完毕:")



def im(num):
    global _FUNC
    _FUNC = run
    poolMangaer(int(num))

def oneMain():
    task_list = getLocalTask()
    task = None
    for task_info in task_list:
        print("有未完成任务")
        task = Task()
        task.task_info = json.loads(task_info.get("task_info"))
        task.user_info = json.loads(task_info.get("user_info"))
        task.uids = json.loads(task_info.get("uids")) if task_info.get("uids") else None
        task.status = 1

    run(task)


def poolMangaer(num): #进程池管理
    task_list = getLocalTask()
    queue = Queue()
    for task in task_list:
        queue.put(task)
    print('Parent process %s.' % os.getpid())
    start_time = time.time() * 1000
    multiprocessing.log_to_stderr()
    p = LoggingPool(processes=num)
    while True:

        if queue.empty():

            task = None
        else:

            bak_info = queue.get_nowait()
            task = Task()
            task.task_info = json.loads(bak_info.get("task_info"))
            task.user_info = json.loads(bak_info.get("user_info"))
            task.uids = json.loads(bak_info.get("uids")) if bak_info.get("uids") else None
            task.status = 1
        print("队列等待:进程数量:{}".format(num))
        time.sleep(5)
        p.apply_async(run, args=(task,)) #添加任务到进城池


    print('All subprocesses done.')
    p.close()
    p.join()



@click.command()
@click.option('-num',default=40, prompt='进程数量设置', help='进程数量设置:',type =int)
def main(num):
    im(num)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
    #oneMain()

