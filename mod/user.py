from sqlalchemy import Column, String, Integer, VARCHAR, ForeignKey, Float, BOOLEAN, DateTime, VARBINARY
from sqlalchemy.orm import relationship,backref
from datetime import datetime

import time
import uuid
import re
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import threading
from proto.message.pb_pb2 import *
from mod.content import *
AREA_CODE = "+86"

class User():
    """
    抖音用户上下文
    """
    content = Content()
    im_send_count = 0
    im_success = 0
    im_fail = 0
    uids = dict()
    is_locked = False
    im_send_status = 0
    def __init__(self):
        self.im_send_count = 0
        self.uids = dict()
    #def send_sms_reply(self, ):


    def userinfo(self, is_register=False):
        logger.info("准备开始获取用户个人资料")
        self.call_user_api()
        self.content.get(host="aweme.snssdk.com", path="/aweme/v1/im/resources/sticker/list/")

        self.content.get(host="aweme.snssdk.com", path="/aweme/v1/user/settings/")



    def call_user_api(self, host="aweme.snssdk.com"):
        resp = self.content.get(host=host, path="/aweme/v1/user/").json()
        self.user_status_code = resp["status_code"]

        if resp["status_code"] in [8, 9]:
            logger.error(resp)
            self.is_locked = True
        else:
            if "user" in resp:
                self.nickname = resp['user']['nickname']
                self.uid = resp['user']['uid']
                self.short_id = resp['user']['short_id']
                self.gender = resp['user']['gender']
                self.signature = resp['user']['signature']
                self.birthday = resp['user']['birthday']
                self.attention = resp['user']['following_count']
                self.follow = resp['user']['follower_count']
                self.avatar = resp['user']['avatar_thumb']['url_list'][0]
                print("用户信息: %s ID=%s short_id=%s 生日%s 性别%s 关注%s 粉丝%s 私信%s 头像%s " % (self.nickname,
                                                                                     self.uid,
                                                                                     self.short_id, self.birthday,
                                                                                     self.gender, self.attention,
                                                                                     self.follow,
                                                                                     0,  # self.message_times,
                                                                                     self.avatar,
                                                                                     ))
            else:
                logger.error(resp)


    def upload_image(self, img_bytes):
        files = {'file': img_bytes}
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/upload/image/", params={}, postParams={},
                                 files=files).json()

        if resp["status_code"] != 0:
            return False
        else:
            return resp["data"]
        return resp

    def upload_file(self, file_bytes, file_type="mpeg"):
        files = {'file': file_bytes, "file_type": file_type}
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/upload/file/", params={}, postParams={},
                                 files=files).json()
        if resp["status_code"] != 0:
            return False
        else:
            return resp["data"]
        return resp

    def commit_user(self, img_bytes, nickname="雪球啦啦啦", birthday='1998-11-23', gender=2, show_gender_strategy=0):
        """更新用户头像，性别，昵称，年龄"""
        self.content.app_xlog(scene="camera")
        files = {'file': img_bytes}
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/upload/image/", params={}, postParams={}, files=files).json()
        avatar_uri = resp['data']['uri']
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/commit/user/", params={}, postParams={
            "avatar_uri": avatar_uri,
            "birthday": birthday,
            "gender": gender,
            "nickname": nickname,
            "show_gender_strategy": show_gender_strategy
        }).json()
        # 判断下是否修改成功是否需要审核
        if resp['status_code'] == 0:
            return True
        else:
            return False

    # 功能代码
    def item_digg(self, aweme_id, type=1):
        """
        视频点赞
        :param aweme_id:
        :param type:
        :return:
        """
        logger.info("点赞抖音视频ID: " + aweme_id)
        ret = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/commit/item/digg/", params={}, postParams={
            "aweme_id": aweme_id,
            "type": "{}".format(type)
        }).json()

        if ret['status_code'] == 0 and ret['is_digg'] == 0:
            return True
        else:
            logger.warning("{} 点赞视频: {} 失败 {}".format(self.uid, aweme_id, ret['status_code']))
            return False

    def follow_user(self, user_id, type=1, ffrom=2):
        """
        用户关注
        :param user_id:
        :param type:
        :return:
        """
        self.try_following_count += 1
        logger.info("{}开始关注用户: {}".format(self.uid, user_id))
        try_count = 1
        try_index = 0
        follow_status = 0
        status_code = 0
        while try_index < try_count:
            resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v1/commit/follow/user/", params={
                "user_id": user_id,
                "type": str(type),
                "from": ffrom,
                "channel_id": 23,
                "mcc_mnc": "46001"
            }).json()
            status_code = resp['status_code']
            resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v1/user/", params={
                "user_id": user_id
            }).json()
            try:
                if resp['user']['follow_status'] == 1:
                    follow_status = resp['user']['follow_status']
                    break
                try_index += 1
                time.sleep(1)
            except:
                return False
        if follow_status == 1:
            logger.info("{} 关注用户: {} 成功".format(self.uid, user_id))
            time.sleep(1)
            return True
        else:
            logger.warning("{} 关注用户: {} 失败 {}".format(self.uid, user_id, status_code))
            time.sleep(1)
            return False

    def follower_list(self):
        logger.info("{}开始获取粉丝列表".format(self.uid))
        count = 40
        user_id = self.uid
        max_time = int(time.time())
        follower_list = []
        while True:
            resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v1/user/follower/list/", params={
                'count': count,
                'user_id': user_id,
                'max_time': max_time
            }).json()
            for item in resp['followers']:
                follower_list.append(item['uid'])
                self.uids[str(item['uid'])] = dict()
                self.uids[str(item['uid'])]["state"] = 0
            if resp['has_more'] == False:
                break
            else:
                max_time = resp['min_time']
                #print(max_time)
                #print(follower_list)
        logger.info("{} 粉丝列表({})".format(self.uid, resp['total']))
        return follower_list

    def aweme_stats(self, item_id, type="0", play_delta="1", tab_type=None):
        """
        视频播放
        :param item_id:
        :param type:
        :param play_delta:
        :param tab_type:
        :return:
        """
        logger.info("播放视频: {}".format(item_id))
        postParams = {
            "aweme_type": str(type),
            "item_id": item_id,
            "play_delta": str(play_delta)
        }
        if tab_type != None: postParams['tab_type'] = tab_type
        self.content.post(host="aweme.snssdk.com", path="/aweme/v1/aweme/stats/", params={}, postParams=postParams)

    def aweme_shared(self, item_id, type="0"):
        target = ""

    # def comment_publish(self, aweme_id, text):
    #     """视频评论"""
    #     logger.debug("视频评论: {} 内容: ".format(aweme_id, text))
    #     post_params = {
    #         "aweme_id": aweme_id,
    #         "text": text
    #     }
    #     resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/comment/publish/", params={}, postParams=post_params).json()
    #     if resp['status_code'] == 0:
    #         return True
    #     else:
    #         return False

    def update_signature(self, signature):
        """用户签名修改"""
        logger.debug("签名修改: {} : ".format(signature))
        post_params = {
            "signature": signature
        }
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/commit/user/", params={},
                                 postParams=post_params).json()
        if resp['status_code'] == 0:
            return True
        else:
            return False

    def recommend(self, target_user_id="85264891763"):
        logger.info("获取关注更多: " + str(target_user_id))
        ret = self.content.get(host="aweme.snssdk.com", path="/aweme/v2/user/recommend/", params={
            "cursor": 0,
            "address_book_access": 1,
            "push_user_id": "",
            "yellow_point_count": 0,
            "count": 30,
            "rec_impr_users": "",
            "recommend_type": 1,
            "target_user_id": target_user_id,
        }).json()
        return

    def update_gender(self, gender=0, show_gender_strategy=0):
        """修改用户性别
        gender: 0  男  1 女  2不限时
        """
        logger.debug("修改用户性别: {} : ".format(gender))
        post_params = {
            "gender": gender,
            "show_gender_strategy": show_gender_strategy
        }
        if show_gender_strategy == 1:
            post_params = {
                "show_gender_strategy": show_gender_strategy
            }
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/commit/user/", params={},
                                 postParams=post_params).json()
        if resp['status_code'] == 0:
            return True
        else:
            return False

    def update_gender(self, nickname):
        """修改用户昵称
        """
        logger.debug("修改用户昵称: {} : ".format(nickname))
        post_params = {
            "nickname": nickname
        }

        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/commit/user/", params={},
                                 postParams=post_params).json()
        if resp['status_code'] == 0:
            return True
        else:
            return False

    def comment_list(self, aweme_id, count=20, max_count=20, cursor=0):
        """获取评论列表"""
        comments = []
        resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v2/comment/list/", params={
            'aweme_id': aweme_id,
            'cursor': cursor,
            'count': count
        }).json()
        for comment in resp['comments']:
            comments.append({
                'cid': comment['cid'],
                'create_time': comment['create_time'],
                'text': comment['text'],
                'nickname': comment['user']['nickname'],
                'gender': comment['user']['gender']
            })
        if len(comments) < max_count and resp['has_more'] == 1:
            comments += self.comment_list(aweme_id, max_count=max_count, count=count, cursor=cursor+count)
        return comments[0:max_count]

    def comment_publish(self, aweme_id, text, channel_id=0, reply_id=None):
        """回复评论"""
        logger.info("视频: {} 回复: {} 内容: {}".format(aweme_id, reply_id, text))
        resp = self.content.post(host="aweme.snssdk.com", path="/aweme/v1/comment/publish/", params={}, postParams={
            "aweme_id": aweme_id,
            "channel_id": channel_id,
            "reply_id": reply_id,
            "text": text
        })
        if resp['status_code'] == 0:
            return True
        else:
            return False

    def dyid_to_uid(self, dyid):
        """抖音ID转换用户id"""
        resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v1/general/search/single/", params={
            'hot_search': 0,
            'count': 12,
            'offset': 0,
            'is_pull_refresh': 0,
            'keyword': dyid
        }).json()
        uid = resp['data'][0]['user_list'][0]['user_info']['uid']
        return uid

    def im_init(self):
        self.wss_status = "closed"
        self.message_token_status_code = 1
        self.im_cloud_token()
        if self.message_token_status_code:
            logger.warning("im_init() | {}".format(self.message_token_status_code))
            return False
        else:

            self.im_online()
            self.wss_start()
            utiles.loop_sleep(timeout=5, msg="开启私信成功，{}秒后发送私信")
            return True

    @retry(tries=2, delay=2)
    def im_cloud_token(self):
        """获取私信token"""
        self.im_token = ""
        try:
            uid = self.uid
        except:
            self.userinfo()
        logger.debug("userid:" + str(self.uid))
        resp = self.content.get(host="aweme.snssdk.com", path="/aweme/v1/im/cloud/token/", params={
            "client_uid": self.uid,
            "im_auth": "20180420",
        }).json()

        self.message_token_status_code = resp['status_code']

        if resp['status_code'] == 0:
            self.im_token = resp['data']['token']
        else:
            logger.info("获取im token: {}".format(resp))
            self.message_token_status_code = resp['status_code']
        # {'status_code': 8, 'log_pb': {'impr_id': '20181212214011010016021047411ED3'}, 'extra': {'logid': '20181212214011010016021047411ED3', 'now': 1544622011436, 'fatal_item_ids': []}}

        logger.info("获取到的im token: {}".format(self.im_token))
        return self.im_token

    # def im_msg_ticket(self, target_uid="104918402940"):
    #     """获取私信ticket"""
    #     self.msg_ticket = ""
    #     if self.im_token == "":
    #         return self.msg_token
    #     headers = aweme_header.copy()
    #     headers['Content-Type'] = 'application/x-protobuf'
    #     headers['Accept'] = 'application/json'
    #     im_token = chr(len(self.im_token)).encode() + self.im_token.encode()
    #     channel = b'\x09App Store' # \x02pp
    #     device_type = chr(len(self.content.device.device_type)).encode() + self.content.device.device_type.encode()     #\tiPhone5,3
    #     os_version = chr(len(self.content.device.os_version)).encode() + self.content.device.os_version.encode()     #\x059.0.1
    #     app_version = b"\x03340"
    #     both_sides = '0:1:{}:{}'.format(self.uid, target_uid)   # 0:1:101537718211:104918402940
    #     both_sides_bytes = chr(len(both_sides)).encode() + both_sides.encode()
    #     payload = b'\x08\xd8\x04\x10\xb7\xa9\xed\xe5\xba\x04\x1a\x0c0.5.0-beta39"' + im_token + b'(\x020\x00:\x0c201807262202B-\xc2%*\n' + both_sides_bytes + b'\x10\x84\xc8\xac\xe2\xd4\xcf\xef\x02\x18\x01J\x0b56778539878R' + channel + b'Z\x06iphoneb' + device_type + b'j' + os_version + b'r' + app_version
    #
    #     payload = b'\x08\xc9\x01\x10\xaf\xd0\x87\xa1\xba\x04\x1a\x0c0.5.0-beta39"' + im_token + b'(\x020\x00:\x0c201807262202B\x05\xca\x0c\x02\x08\x00J\x0b56778539878R' + channel + b'Z\x06iphoneb' + device_type + b'j' + os_version + b'r' + app_version
    #     # resp = self.content.http.post("https://imapi.snssdk.com/v1/conversation/get_info",
    #     #                        data=payload,
    #     #                        headers=headers).json()
    #     resp = self.content.http.post("https://imapi.snssdk.com/v1/message/get_by_user_init",
    #                                     data=payload,
    #                                     headers=headers).json()
    #     print(json.dumps(resp))
    #     self.msg_ticket = resp['body']['get_conversation_info_body']['conversation_info']['ticket']
    #     logger.debug("im ticket: " + self.msg_ticket)
    #     return self.msg_ticket

    def im_online(self):
        headers = utiles.get_aweme_headers(self.content.device.os_version).copy()
        headers['Content-Type'] = 'application/x-protobuf'
        headers['Accept'] = 'application/json'
        payload = b'\x08\x90\x03\x10\xab\xab\xbf\xf0\xd0\x04\x1a\x0c0.5.0-beta39"6' + self.im_token.encode() + b'(\x02:\x0c201807262202J\x0b59826057140R\tApp StoreZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03310'
        resp = self.content.orig_post("https://imapi.snssdk.com/v1/account/online",
                                             data=payload,
                                             headers=headers).json()
        print(json.dumps(resp))

    def __wss_on_message(self, message):
        """私信收到消息"""
        # logger.info("__wss_on_message接受到: ")
        # logger.debug(message)
        resp = utiles.protobuf_decode_raw(message)
        if re.search(r'1: 602', resp):
            # logger.debug("获取聊天ticket消息")
            m = re.search(r'1: "0:1:(\d+):{}"'.format(self.uid), resp)
            if m:
                target_user = m.group(1)
            else:
                target_user = self.target_userid
            # logger.debug("target user: " + str(target_user))
            m = re.search(r'11: "(\w{100,})"', resp)
            if m:
                ticket = m.group(1)
                # logger.debug("ticket: " + ticket)
                f12 = re.search(r'12: (\d+)', resp).group(1)
                self.im_tickets[int(target_user)] = {
                    't': ticket,
                    'f12': f12
                }

        # 获取发送消息返回结果
        if re.search(r'1: 100', resp):
            if re.search(r'{}'.format(self.im_curr_msgid), resp):
                if re.search(r'4: "OK"', resp):
                    if re.search(r'status_code', resp):
                        if re.search(r'7177', resp):
                            # 私信功能已被封禁，详情见消息通知
                            self.im_send_status = "7177"
                        elif re.search(r'7178', resp):
                            # 发送失败
                            self.im_send_status = "7178"
                        elif re.search(r'7173', resp):
                            # 由于对方的隐私设置，你无法发送消息
                            self.im_send_status = "7173"
                        elif re.search(r'7174', resp):
                            # 陌生人发送成功
                            self.im_send_status = "7174"
                            self.im_send_status = True
                        elif re.search(r'7185', resp):
                            # 该用户关闭了私信功能，无法接收到你的消息
                            self.im_send_status = "7185"
                        elif re.search(r'7182', resp):
                            # 没有相互关注 不能发送图片
                            self.im_send_status = "7185"
                        elif re.search(r'7190', resp):
                            # 没有相互关注 不能使用语音
                            self.im_send_status = "7190"
                        elif re.search(r'status_code\\":0,', resp):
                            self.im_send_status = True
                        else:
                            # 其他情况，等待确认
                            searchObj = re.search(r'status_code\\":(\d+)', resp)

                            logger.warning("status_code--{}".format(searchObj.group(1)))
                            self.im_send_status = False
                    else:
                        self.im_send_status = True
                else:
                    logger.warning("b--{}".format(resp))
                    self.im_send_status = False
            self.im_is_send = True

    def __wss_on_error(self, error):
        logger.warning("__wss_on_error - {}".format(error))

    def __wss_on_close(self):
        logger.warning("__wss_on_close - closed ###")
        self.wss_stop()
        logger.warning("关闭WSS连接")
        self.im_init()
        logger.info("重新连接WSS结束")

    def __wss_on_open(self):
        def run(*args):
            #logger.warning("thread terminating...")
            pass

        thread.start_new_thread(run, ())

    def wss_start_thread(self):
        """私信WSS线程"""
        access_key = utiles.md5("9e1bd35ec9db7b8d846de66ed140b1ad9" + str(self.content.device.device_id) + "f8a69f1719916z")
        wsurl = "wss://frontier.snssdk.com/ws/v2?aid=1128&device_id={}&access_key={}&fpid=9&sdk_version=1&iid={}&sid={}&pl=1&ne=1&version_code={}".format(
            self.content.device.device_id,
            access_key,
            self.content.device.install_id,
            self.content.http.cookies.get("sessionid"),
            APPINFO['version_code']
        )
        logger.debug(wsurl)
        print("wsurl:"+wsurl)
        websocket.enableTrace(False)
        self.im = websocket.WebSocketApp(wsurl,
                                         on_message=self.__wss_on_message,
                                         on_error=self.__wss_on_error,
                                         on_close=self.__wss_on_close)
        self.im.on_open = self.__wss_on_open
        if self.content.proxy == None:
            self.content.proxy = utiles.get_proxy()
        if self.content.proxy != None:
            #ph, pp = self.content.proxy['http'].split(":")
            #ph = ph.strip("http://")
            #print(self.content.proxy)
            if self.content.proxy.find("@") <= 0:
                ret = self.content.proxy.split(":")
                ph = ret[0]
                pp = ret[1]
            else:
                ret = self.content.proxy.split("@")[1].split(":")
                ph = ret[0]
                pp = ret[1]

            logger.info("wss proxy: {}:{}".format(ph, pp))
            self.im.run_forever(http_proxy_host=ph, http_proxy_port=pp)


        else:
            logger.info("未使用wss proxy")
            self.im.run_forever()

    def wss_start(self):
        """开启私信WSS链接"""
        logger.info("开启私信WSS链接****************************************************************** 开始")
        self.im_thread = threading.Thread(target=self.wss_start_thread)
        self.im_thread.setDaemon(True)
        self.im_thread.start()
        time.sleep(1)

        if hasattr(self, 'im_tickets'):
            logger.info(self.im_tickets.keys())
        else:
            self.im_tickets = {}
        self.wss_status = "open"
        self.im_is_send = True
        self.im_send_status = "closed"

        logger.info("开启私信WSS链接****************************************************************** 结束")

    def wss_stop(self):
        self.im.close()

    def wss_im_send(self, target_userid=101537718211, text=None, img_bytes=None, audio_bytes=None,link_info=None,vedio_info=None):
        send_content = {"text": 6666}
        send_type = 7
        if text:
            send_content = {"text": text}
            send_type = 7
        if img_bytes:
            img_bytes = utiles.append_garbage_data(img_bytes)
            w, h = utiles.get_image_size(img_bytes)
            resp = self.upload_image(img_bytes)
            if not resp:
                logger.error("图片上传失败...")
                return "图片上传失败"
            resource_info = {"resource_url": resp}
            resource_info["cover_height"] = h
            resource_info["cover_width"] = w
            resource_info["md5"] = utiles.md5(img_bytes)
            send_content = resource_info
            send_type = 2
        if audio_bytes:
            audio_bytes = utiles.append_garbage_data(audio_bytes)
            resp = self.upload_file(audio_bytes)
            if not resp:
                logger.error("音频文件上传失败...")
                return "音频文件上传失败"
            resource_info = {"resource_url": resp}
            resource_info["md5"] = utiles.md5(audio_bytes)
            resource_info["duration"] = random.randint(5001, 13000)
            send_content = resource_info
            send_type = 17

        if link_info:
            send_content = {}
            if "cover_url" not in link_info or "link_url" not in link_info or "title" not in link_info or "desc" not in link_info:
                logger.error("链接参数错误.")
                return "链接参数错误."
            send_content["cover_url"] = link_info["cover_url"]
            send_content["push_detail"] = link_info["title"]
            send_content["link_url"] = link_info["link_url"]
            send_content["title"] = link_info["title"]
            send_content["prev_id"] = "6706699485969385000"
            send_content["root_id"] = "6684536658127227000"
            send_content["desc"] = link_info["desc"]
            send_type = 26
        if vedio_info:
            send_content = {}
            if "content_title" not in vedio_info or "itemId" not in vedio_info or "uid" not in vedio_info or "url_list" not in vedio_info:
                logger.error("链接参数错误.")
                return "链接参数错误."
            send_content["content_thumb"] = {}
            send_content["cover_url"] = {}
            send_content["cover_url"]["url_list"] = [vedio_info["url_list"]]
            send_content["content_title"] = vedio_info["content_title"]
            send_content["itemId"] = vedio_info["itemId"]
            send_content["uid"] = vedio_info["uid"]
            send_content["cover_height"] = 640
            send_content["cover_width"] = 720
            send_content["aweType"] = 800
            send_type = 8
        try:
            self.im_send_count += 1
            is_send = False
            #target_userid = 101751905840
            target_userid = int(target_userid)
            self.target_userid =  target_userid
            target_userid_bytes = utiles.numberToVarint(target_userid)[0]
            userid = utiles.numberToVarint(int(self.uid))[0]
            im_token = chr(len(self.im_token)).encode() + self.im_token.encode()
            channel = b'\x09App Store'  # \x02pp
            device_type = chr(len(self.content.device.device_type)).encode() + self.content.device.device_type.encode()  # \tiPhone5,3
            os_version = chr(len(self.content.device.os_version)).encode() + self.content.device.os_version.encode()  # \x059.0.1
            app_version = b"\x03340"
            #paylaod = b'\x08\xa8\xcb\xaf\xfa\xe8\n\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\xa7\x01\x08\xda\x04\x10\xa8\xcb\xaf\xfa\xe8\n\x1a\x0c0.5.0-beta39"' + im_token + b'(\x020\x00:\x0c201807262202B\x13\xd2%\x10\x08\x01\x10' + target_userid_bytes + b'\x10' + userid + b'J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340'     #R' + channel + b'Z\x06iphoneb' + device_type + b'j' + os_version + b'r' + app_version
            payload_8 = b'\x08\xda\x04\x10\xa8\xcb\xaf\xfa\xe8\n\x1a\x0c0.5.0-beta39"' + im_token + b'(\x020\x00:\x0c201807262202B\x13\xd2%\x10\x08\x01\x10' + userid + b'\x10' + target_userid_bytes + b'J\x0b56778539878R' + channel + b'Z\x06iphoneb' + device_type + b'j' + os_version + b'r' + app_version
            payload_len = len(payload_8)
            paylaod = b'\x08\xa8\xcb\xaf\xfa\xe8\n\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB' + utiles.numberToVarint(payload_len)[0] + payload_8
            # print(paylaod)
            #self.im.send(paylaod, opcode=websocket.ABNF.OPCODE_BINARY)

            message = Message()
            #message.f1 = 371771303336
            message.f1 = int(time.time()*100)      # 随机字符串
            message.f2 = 12345678
            message.f3 = 5
            message.f4 = 1
            message.f6 = "pb"
            message.f7 = "pb"

            msg_payload = message.f8.add()
            msg_payload.f1 = 602
            msg_payload.f2 = message.f1
            msg_payload.f3 = "0.5.0-beta39"
            msg_payload.f4 = self.im_token
            msg_payload.f5 = 2
            msg_payload.f6 = 0
            msg_payload.f7 = "201807262202"

            msgs = msg_payload.f8.add()
            msg602 = msgs.f602.add()
            msg602.f1 = 1
            msg602.f2.append(int(self.uid))
            msg602.f2.append(int(target_userid))

            msg_payload.f9 = ""
            msg_payload.f10 = APPINFO['channel']
            msg_payload.f11 = "iphone"
            msg_payload.f12 = self.content.device.device_type
            msg_payload.f13 = self.content.device.os_version
            msg_payload.f14 = "310"

            #print("---------")
            #print(msg_payload.SerializeToString())
            #print(message.SerializeToString())
            paylaod = message.SerializeToString()
            #print("---------")
            self.im.send(paylaod, opcode=websocket.ABNF.OPCODE_BINARY)

            message = Message()
            #message.f1 = 371771303335
            message.f1 = int(time.time()*100)
            message.f2 = 12345678
            message.f3 = 5
            message.f4 = 1
            message.f6 = "pb"
            message.f7 = "pb"

            msg_payload = message.f8.add()
            msg_payload.f1 = 602
            msg_payload.f2 = message.f1
            msg_payload.f3 = "0.5.0-beta39"
            msg_payload.f4 = self.im_token
            msg_payload.f5 = 2
            msg_payload.f6 = 0
            msg_payload.f7 = "201807262202"

            msgs = msg_payload.f8.add()
            msg602 = msgs.f602.add()
            msg602.f1 = 1
            msg602.f2.append(int(target_userid))
            msg602.f2.append(int(self.uid))

            msg_payload.f9 = "06778539878"
            msg_payload.f10 = APPINFO['channel']
            msg_payload.f11 = "iphone"
            msg_payload.f12 = self.content.device.device_type
            msg_payload.f13 = self.content.device.os_version
            msg_payload.f14 = "310"

            #print("---------")
            #print(msg_payload.SerializeToString())
            #print(message.SerializeToString())
            paylaod = message.SerializeToString()
            #print("---------")
            self.im.send(paylaod, opcode=websocket.ABNF.OPCODE_BINARY)
            retry1 = 0
            while True:
                retry1 += 1
                if target_userid in self.im_tickets.keys():
                    time.sleep(0.2)
                    break
                else:
                    time.sleep(0.02)
                    # if retry1 > 1000:
                    #     logger.info("第{}次循环，im_tickets.keys()={}".format(retry1, self.im_tickets.keys()))
                    #     logger.info("第{}次循环，target_userid={}".format(retry1, target_userid))
                    retry_max_times = 1000
                    if retry1 > retry_max_times:
                        utiles.loop_sleep(timeout=5, msg="超过" + str(retry_max_times) + "次，还是没有获取到，{}秒后继续")

                        return False

            message = Message()
            #message.f1 = 840112092412
            message.f1 = int(time.time()*100)
            message.f2 = 12345678
            message.f3 = 5
            message.f4 = 1
            message.f6 = "pb"
            message.f7 = "pb"

            msg_payload = message.f8.add()
            msg_payload.f1 = 600
            msg_payload.f2 = message.f1
            msg_payload.f3 = "0.5.0-beta39"
            msg_payload.f4 = self.im_token
            msg_payload.f5 = 2
            msg_payload.f6 = 0
            msg_payload.f7 = "201807262202"

            msgs = msg_payload.f8.add()
            msg600 = msgs.f600.add()

            msg600.f1 = "0:1:{}:{}".format(target_userid, self.uid) if int(target_userid)<int(self.uid) else  "0:1:{}:{}".format(self.uid,target_userid)
            #msg600.f1 = "0:1:{}:{}".format(target_userid, self.uid)
            msg600.f2 = int(self.im_tickets[target_userid]['f12'])
            msg600.f3 = 1

            msg_payload.f9 = "06778539878"
            msg_payload.f10 = APPINFO['channel']
            msg_payload.f11 = "iphone"
            msg_payload.f12 = self.content.device.device_type
            msg_payload.f13 = self.content.device.os_version
            msg_payload.f14 = "310"

            #print("---------")
            #print(msg_payload.SerializeToString())
            #print(message.SerializeToString())
            paylaod = message.SerializeToString()
            #print("---------")
            #self.im.send(paylaod, opcode=websocket.ABNF.OPCODE_BINARY)

            start_time = int(time.time()*1000)
            while int(time.time()*1000) - start_time < 3*1000:
                if target_userid in self.im_tickets.keys():
                    logger.debug("开发发送消息")
                    time.sleep(2)
                    message = Message()
                    #message.f1 = 569602838081
                    message.f1 = int(time.time()*100)
                    message.f2 = 12345678
                    message.f3 = 5
                    message.f4 = 1
                    message.f6 = "pb"
                    message.f7 = "pb"

                    msg_payload = message.f8.add()
                    msg_payload.f1 = 100
                    msg_payload.f2 = message.f1
                    msg_payload.f3 = "0.5.0-beta39"
                    msg_payload.f4 = self.im_token
                    msg_payload.f5 = 2
                    msg_payload.f6 = 0
                    msg_payload.f7 = "201807262202"

                    msgs = msg_payload.f8.add()
                    msg = msgs.f100.add()
                    msg.f1 = "0:1:{}:{}".format(target_userid, self.uid) if int(target_userid) < int(self.uid) else "0:1:{}:{}".format(self.uid, target_userid)
                    #msg.f1 = "0:1:{}:{}".format(target_userid, self.uid)
                    msg.f2 = 1
                    msg.f3 = int(self.im_tickets[target_userid]['f12'])
                    msg.f4 = json.dumps(send_content)   #"{\"text\":\"{}\"}"
                    old_msg = msg.f5.add()
                    old_msg.f1 = "old_client_message_id"
                    old_msg.f2 = str(int(time.time()*1000))     #时间戳
                    msg.f6 = send_type
                    msg.f7 = self.im_tickets[target_userid]['t']
                    msg.f8 = str(uuid.uuid4())
                    self.im_curr_msgid = msg.f8
                    logger.debug("Msg ID: {}".format(msg.f8))

                    msg_payload.f9 = "06778539878"
                    msg_payload.f10 = APPINFO['channel']
                    msg_payload.f11 = "iphone"
                    msg_payload.f12 = self.content.device.device_type
                    msg_payload.f13 = self.content.device.os_version
                    msg_payload.f14 = "310"

                    info = msg_payload.f15.add()
                    info.f1 = "sim_mcc_mnc"
                    info.f2 = "0"

                    info = msg_payload.f15.add()
                    info.f1 = "aid"
                    info.f2 = "1128"

                    info = msg_payload.f15.add()
                    info.f1 = "iid"
                    info.f2 = str(self.content.device.install_id)

                    info = msg_payload.f15.add()
                    info.f1 = "app_name"
                    info.f2 = "aweme"

                    #print(msg_payload.SerializeToString())
                    #print(message.SerializeToString())
                    paylaod = message.SerializeToString()
                    logger.debug(self.im_token.encode())
                    self.im_tickets[target_userid] = '1W8vrqPObuTWCfrG51z4kNylMCpKInQVcQ9kM50raGtZhKbGuYAvrRYtBnvgvlKTATQ2bD5UOWY9HO6vRYqGc9Vl7cx0HkTB0vC3Cgs96YKFNtQrPDERjFzhtNr4udtsRW7DcEI71UkssYy0tc3LPbDcY1cptOvslp'
                    logger.debug(self.im_tickets[target_userid].encode())
                    logger.debug(utiles.numberToVarint(len(self.im_tickets[target_userid]))[0])
                    f12 = utiles.numberToVarint(1616821727211523)[0]
                    #payload = b'\x08\xc1\x9c\xe6\xf7\xc9\x10\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x9d\x04\x08d\x10\xc1\x9c\xe6\xf7\xc9\x10\x1a\x0c0.5.0-beta39"68m7M76GVYgwWJmfi7ceuCEE0tih08S4xnlT5dqH3yYOD8qxESpBtgf(\x020\x00:\x0c201807262202B\xc4\x02\xa2\x06\xc0\x02\n\x1d0:1:101537718211:104918402940\x10\x01\x18\x84\xc8\xac\xe2\xd4\xcf\xef\x02" {"text":"111111111111111111111"}*&\n\x15old_client_message_id\x12\r15425432262710\x07:\xa1\x016l83ieHMU6yutu4I6hxHXm4FDatsEdTySGleu4vxcQEq8x1Ueh7IorOAr7oL7En5PpkOuM0gzn5FhicnM8owmYvh6FLarAYmcSLUCsUmY8ZSCTRV6R8mYNFxdolEnHLpD2usoc6eXcH5jWxG7gnVLPp8DLPJt94VsB$F564AD77-2B94-4377-8114-1471169D1949J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    #paylaod = b'\x08\xbd\x9a\x90\xe4\xb0\x17\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x93\x04\x08d\x10\xbd\x9a\x90\xe4\xb0\x17\x1a\x0c0.5.0-beta39"68m7M76GVYgwWJmfi7ceuCEE0tih08S4xnlT5dqH3yYOD8qxESpBtgf(\x020\x00:\x0c201807262202B\xba\x02\xa2\x06\xb6\x02\n\x1d0:1:101537718211:104918402940\x10\x01\x18\x84\xc8\xac\xe2\xd4\xcf\xef\x02"\x16{"text":"22266666666"}*&\n\x15old_client_message_id\x12\r15425529665250\x07:\xa1\x016l83ieHMU6yutu4I6hxHXm4FDatsEdTySGleu4vxcQEq8x1Ueh7IorOAr7oL7En5PpkOuM0gzn5FhicnM8owmYvh6FLarAYmcSLUCsUmY8ZSCTRV6R8mYNFxdolEnHLpD2usoc6eXcH5jWxG7gnVLPp8DLPJt94VsB$9E1A7740-2F11-49C9-89E4-503047C1FC16J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    #paylaod = b'\x08\xbd\x9a\x90\xe4\xb0\x17\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x93\x04\x08d\x10\xbd\x9a\x90\xe4\xb0\x17\x1a\x0c0.5.0-beta39"6' + self.im_token.encode() + b'(\x020\x00:\x0c201807262202B\xba\x02\xa2\x06\xb6\x02\n\x1d0:1:101537718211:104918402940\x10\x01\x18' + f12 + b'"\x16{"text":"22266666666"}*&\n\x15old_client_message_id\x12\r15425529665250\x07:' + utiles.numberToVarint(len(self.im_tickets[target_userid]))[0] + self.im_tickets[target_userid].encode() + b'B$' + str(uuid.uuid4()).encode() + b'J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    #paylaod = b'\x08\xbd\x9a\x90\xe4\xb0\x17\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x93\x04\x08d\x10\xbd\x9a\x90\xe4\xb0\x17\x1a\x0c0.5.0-beta39"6' + self.im_token.encode() + b'(\x020\x00:\x0c201807262202B\xba\x02\xa2\x06\xb6\x02\n\x1d0:1:101537718211:104918402940\x10\x01\x18\x84\xc8\xac\xe2\xd4\xcf\xef\x02"\x16{"text":"22266666666"}*&\n\x15old_client_message_id\x12\r15425529665250\x07:' + utiles.numberToVarint(len(self.im_tickets[target_userid]))[0] + self.im_tickets[target_userid].encode() + b'B$' + str(uuid.uuid4()).encode() + b'J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    #paylaod = b'\x08\xbd\x9a\x90\xe4\xb0\x17\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x93\x04\x08d\x10\xbd\x9a\x90\xe4\xb0\x17\x1a\x0c0.5.0-beta39"6' + self.im_token.encode() + b'(\x020\x00:\x0c201807262202B\xba\x02\xa2\x06\xb6\x02\n\x1d0:1:' + str(self.uid).encode() + b':' + str(self.target_userid).encode()  + b'\x10\x01\x18\x84\xc8\xac\xe2\xd4\xcf\xef\x02"\x16{"text":"22266666666"}*&\n\x15old_client_message_id\x12\r15425529665250\x07:\xa1\x01' + self.im_tickets[target_userid].encode() + b'B$' + str(uuid.uuid4()).encode() + b'J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    #payload = b'\x08\xcc\xea\xbb\x8c\x86\x19\x10\xce\xc2\xf1\x05\x18\x05 \x012\x02pb:\x02pbB\x92\x04\x08d\x10\xcc\xea\xbb\x8c\x86\x19\x1a\x0c0.5.0-beta39"6' + self.im_token.encode() + b'(\x020\x00:\x0c201807262202B\xb9\x02\xa2\x06\xb5\x02\n\x1d0:1:101537718211:104918402940\x10\x01\x18\x84\xc8\xac\xe2\xd4\xcf\xef\x02"\x15{"text":"1111111111"}*&\n\x15old_client_message_id\x12\r15425553524190\x07:\xa1\x01' + self.im_tickets[target_userid].encode() + b'B$' + str(uuid.uuid4()).encode() + b'J\x0b56778539878R\x02ppZ\x06iphoneb\tiPhone5,3j\x059.0.1r\x03340z\x0f\n\x0bsim_mcc_mnc\x12\x00z\x0b\n\x03aid\x12\x041128z\x12\n\x03iid\x12\x0b51512404624z\x11\n\x08app_name\x12\x05aweme'
                    self.im_is_send = False
                    self.im_send_status = False
                    self.im.send(paylaod, opcode=websocket.ABNF.OPCODE_BINARY)
                    break

                else:
                    logger.info("send_b")
                    time.sleep(0.1)

            retry = 0
            while not self.im_is_send:
                retry += 1
                if retry > 100:
                    self.im_send_status = False
                    break
                time.sleep(0.1)
            return self.im_send_status
        except Exception as ex:
            logger.warning("im_send---except  --  给用户发送私信的时候出错 {} ".format(ex))
            self.content.proxy = utiles.get_proxy()
            self.im_init()
            return "except"