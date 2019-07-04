import json
import logging
import os
import string
import time
import re

import coloredlogs
import requests

logger = logging.getLogger("Aweme")#__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("chardet.charsetprober").setLevel(logging.ERROR)
FORMAT = "%(asctime)s %(name)s(%(process)d) %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s"
#fh = logging.FileHandler(os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs/aweme-{}.log'.format(int(time.time()*1000)))))
formatter = logging.Formatter(FORMAT)
#fh.setFormatter(formatter)
#logger.addHandler(fh)

#coloredlogs.install(level='DEBUG')
#coloredlogs.install(level='INFO', logger=logger)

import urllib3
import uuid
import random
from random import Random
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import base64
import os
import hashlib
from subprocess import Popen, PIPE
from retry import retry
import time
import toml


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#API = "http://127.0.0.1:5000"
API = "https://ttl.appsign.vip:2790"

APPINFO = {
    "version_code": "6.7.0",
    "channel": "App Store",
    "app_name": "aweme",
    "build_number": "67016",
    "app_version": "6.7.0",
    "aid": "1128",
    "ac": "WIFI",
    "xlog_ver": "0.8.13.5.2",
    "tz_name": "Asia/Shanghai",
    "js_sdk_version": "1.17.2.0"
}

def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFf0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

class utiles:
    @staticmethod
    def getToken():
        """获取Token       有效期60分钟"""
        return "b5a9cddd9d464f24a84f03791a4c5196"
        resp = requests.get(API + "/token/douyin", headers={'Connection': 'close'}).json()
        token = resp['token']
        logger.debug("Token: " + token)
        return token

    # @staticmethod
    # def getUdid():
    #     resp = requests.get(API + "/token/openudid", headers={'Connection': 'close'}).json()
    #     token = resp['token']
    #     logger.debug("Token: " + token)
    #     return token

    @staticmethod
    @retry(tries=10, delay=2)
    def getUdid():
        resp = requests.get(API + "/douyin/openudid", headers={'Connection': 'close'}).json()
        logger.debug("OpenUDID 返回 : " + json.dumps(resp))
        if 'openudid' in resp['data'].keys():
            return resp['data']['openudid']
        else:
            raise Exception('OpenUDID接口错误')

    @staticmethod
    def random_device_model():
        ds = [
            {
                'device_type': "iPhone11,2",
                'os_version': "12.2",
                'screen_width': "1125",
                'screen_height': "2436",
                'device_model': "iPhone XS",
                "hwn": "D321AP"
            },
            {
                'device_type': "iPhone11,8",
                'os_version': "12.2",
                'screen_width': "828",
                'screen_height': "1792",
                'device_model': "iPhone XR",
                "hwn": "N841AP"
            },
            {
                'device_type': "iPhone10,6",
                'os_version': "12.2",
                'screen_width': "1125",
                'screen_height': "2436",
                'device_model': "iPhone X",
                "hwn": "D221AP"
            },
            {
                'device_type': "iPhone10,3",
                'os_version': "12.2",
                'screen_width': "1125",
                'screen_height': "2436",
                'device_model': "iPhone X",
                "hwn": "D22AP"
            },
            {
                'device_type': "iPhone10,5",
                'os_version': "12.2",
                'screen_width': "1080",
                'screen_height': "1920",
                'device_model': "iPhone 8 Plus",
                "hwn": "D211AP"
            },
            {
                'device_type': "iPhone10,2",
                'os_version': "12.2",
                'screen_width': "1080",
                'screen_height': "1920",
                'device_model': "iPhone 8 Plus",
                "hwn": "D21AP"
            },
            {
                'device_type': "iPhone10,4",
                'os_version': "12.2",
                'screen_width': "750",
                'screen_height': "1334",
                'device_model': "iPhone 8",
                "hwn": "D201AP"
            },
            {
                'device_type': "iPhone10,1",
                'os_version': "12.2",
                'screen_width': "750",
                'screen_height': "1334",
                'device_model': "iPhone 8",
                "hwn": "D20AP"
            }
        ]
        #return random.sample(ds, 1)[0]
        return {
            'device_type': "iPhone8,1",
            'os_version': "10.2",
            'screen_width': "750",
            'screen_height': "1334",
            'device_model': "iPhone 6S",
            "hwn": "D321AP"
        }

        # return {
        #     'device_type': "iPhone11,2",
        #     'os_version': "12.2",
        #     'screen_width': "1125",
        #     'screen_height': "2436",
        #     'device_model': "iPhone XS",
        #     "hwn": "D321AP"
        # }
        # return device

    @staticmethod
    def getDevice():
        openudid = utiles.getUdid()
        idfa = str(uuid.uuid4()).upper()
        vid = str(uuid.uuid4()).upper()
        device = utiles.random_device_model()
        device_info = {
            'openudid': openudid,
            'idfa': idfa,
            'vid': vid,
            'install_id': '',
            'iid': '',
            'device_id': '',
            'device_type': device['device_type'],
            'os_version': utiles.random_osversion(), #device['os_version'],
            "os_api": "18",
            "screen_width": device['screen_width'],
            "screen_height": device['screen_height'],
            "device_platform": "iphone",
            "device_model": device['device_model'],
            "hwm": device["hwn"]
        }
        return device_info

    @staticmethod
    def params2str(params):
        """拼装参数"""
        query = ""
        for k, v in params.items():
            query += "%s=%s&" % (k, v)
        query = query.strip("&")
        logger.debug("签名字符串: " + query)
        return query

    @staticmethod
    @retry(tries=10, delay=2)
    def getSign(token, query):
        if isinstance(query, dict):
            query = utiles.params2str(query)
        resp = requests.post(API + "/sign", json={"token": token, "query": query}, headers={'Connection': 'close'}).json()
        logger.debug("签名返回: " + json.dumps(resp))
        sign = resp['data']
        if 'error' in resp['data'].keys():
            logger.warning("getSign Error")
            raise Exception('Sign接口错误')
        return sign

    @staticmethod
    @retry(tries=10, delay=2)
    def getXlogData(scene, did, iid, sid="", idfv="", idfa="", expansion={}):
        resp = requests.post(API + "/douyin/xlog", json={
            "scene": scene,
            "device_id": did,
            "install_id": iid,
            "session_id": sid,
            "idfv": idfv,
            "idfa": idfa,
            "expansion": expansion
        }, headers={'Connection': 'close'}).json()
        #logger.debug("xlog data: " + json.dumps(resp))
        if 'error' in resp['data'].keys():
            logger.warning("getXlogData Error")
            raise Exception('xlog接口错误')
        return resp['data']

    @staticmethod
    @retry(tries=10, delay=2)
    def encryptXlogData(xlog):
        resp = requests.post(API + "/douyin/xlog-encrypt", json={
            "xlog": xlog
        }, headers={'Connection': 'close'}).json()
        #logger.debug("xlog data: " + json.dumps(resp))
        if 'data' in resp['data'].keys():
            return resp['data']
        else:
            logger.warning("encryptXlogData Error")
            raise Exception('xlog接口错误')

    @staticmethod
    @retry(tries=10, delay=2)
    def decryptXlogData(data):
        resp = requests.post(API + "/douyin/xlog-decrypt", json={
            "data": data
        }, headers={'Connection': 'close'}).json()
        #logger.debug("xlog data: " + json.dumps(resp))
        if 'xlog' in resp['data'].keys():
            return resp['data']['xlog']
        else:
            logger.warning("encryptXlogData Error")
            raise Exception('xlog接口错误')

    @staticmethod
    @retry(tries=10, delay=2)
    def encryptLogData(log):
        resp = requests.post(API + "/douyin/log-encrypt", json={
            "log": log
        }, headers={'Connection': 'close'}).json()
        logger.debug("log data: " + json.dumps(resp))
        if 'data' in resp['data'].keys():
            return base64.b64decode(resp['data']['data'])
        else:
            logger.warning("encryptlogData Error")
            raise Exception('log接口错误')

    @staticmethod
    @retry(tries=10, delay=2)
    def getXHeaders(url, headers):
        url = url.replace("%20", "+")
        #logger.info("url: {}".format(url))
        #logger.info(headers)
        resp = requests.post(API + "/douyin/x-headers", json={
            "url": url,
            "headers": headers
        }, headers={'Connection': 'close'}).json()
        logger.debug("xheaders: " + json.dumps(resp))
        if 'error' in resp['data'].keys():
            logger.warning("getXlogData Error")
            raise Exception('xlog接口错误')
        return resp['data']


    @staticmethod
    def mixString(pwd):
        """混淆手机号码和密码"""
        #return "2e3d3334303436333d3031373033"
        password = ""
        for i in range(len(pwd)):
            password += hex(ord(pwd[i]) ^ 5)[-2:]
        return password


    @staticmethod
    def genOrigXlog(brand="iPhone 6",
                    os_version = "12.2",
                    session_id="",
                    device_id="67611989389",
                    install_id="70993774391",
                    scene="timer",
                    ext_info = None):

        wifi_mac =  ext_info['wifi_mac']
        wifi_name = ext_info['wifi_name']
        wifiip = ext_info['wifiip']
        device_name = ext_info['device_name']
        aweme_path = ext_info['aweme_path']
        dyuid = ext_info['dyuid']
        tt = ext_info['tt']
        hwm = ext_info['hwm']# "D321AP"
        #dyuid = "8C280345-0164-3B82-A228-124B23CA0E9F"
        #wifi_mac = utiles.randomMAC().lower()
        #wifi_name = "TP-LINK"
        #wifiip = "192.168.100.103"
        #tt = random.randint(100, 10000)
        ta = str(1552643338 - tt)
        tb = str(1552643173 - tt)
        xlog = {
            "wifibssid":wifi_mac,
            "ML":"zh-Hans-CN",
            "host":1,
            "brand":brand,# "iPhone 6",
            "channel":"pp",
            "vpn":0,
            "proxyip":"",
            "MN":"{}的 iPhone".format(device_name),
            "os":"iOS {}".format(os_version),
            "dns":["192.168.100.1"],
            "sid":session_id,
            "wifissid":wifi_name,
            "bundleID":"com.ss.iphone.ugc.Aweme",
            #"sec":"{\"dbg\":{\"ctl\":0,\"sys_ctl\":0,\"tty\":0,\"oppid\":0,\"wp\":0,\"ntf\":0},\"jb\":{\"dylb\":0,\"file\":0,\"file_sys\":0,\"env\":\"\",\"mods\":[\"/private/var/containers/Bundle/Application/E80F4FFB-C292-45FE-A9EC-E4B01582FD38/Aweme.app/Frameworks/AgoraRtcEngineKit.framework/AgoraRtcEngineKit\",\"/private/var/containers/Bundle/Application/E80F4FFB-C292-45FE-A9EC-E4B01582FD38/Aweme.app/Frameworks/LiveStreamFramework.framework/LiveStreamFramework\",\"/private/var/containers/Bundle/Application/E80F4FFB-C292-45FE-A9EC-E4B01582FD38/Aweme.app/Frameworks/AwemeDylib.framework/AwemeDylib\",\"/usr/lib/libobjc-trampolines.dylib\"]},\"rebuild\":{\"sci\":0,\"entitlement\":\"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y29tLmFwcGxlLmRldmVsb3Blci5uZXR3b3JraW5nLndpZmktaW5mbzwva2V5PgoJPHRydWUvPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLnRlYW0taWRlbnRpZmllcjwva2V5PgoJPHN0cmluZz4zSlRQRUE0VVU3PC9zdHJpbmc+Cgk8a2V5PmFwcGxpY2F0aW9uLWlkZW50aWZpZXI8L2tleT4KCTxzdHJpbmc+M0pUUEVBNFVVNy5jb20uc3MuaXBob25lLnVnYy5Bd2VtZTwvc3RyaW5nPgoJPGtleT5hcHMtZW52aXJvbm1lbnQ8L2tleT4KCTxzdHJpbmc+cHJvZHVjdGlvbjwvc3RyaW5nPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLmFzc29jaWF0ZWQtZG9tYWluczwva2V5PgoJPGFycmF5PgoJCTxzdHJpbmc+YXBwbGlua3M6ZG91eWluLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6d3d3LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmFwaS1zcGUtZC5zbnNzZGsuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczphcGktc3BlLWUuc25zc2RrLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6YW1lbXYuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp3d3cuYW1lbXYuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp2LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmllc2RvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOnd3dy5pZXNkb3V5aW4uY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp0ZXN0LXd3dy5kb3V5aW4uY29tPC9zdHJpbmc+Cgk8L2FycmF5PgoJPGtleT5jb20uYXBwbGUuc2VjdXJpdHkuYXBwbGljYXRpb24tZ3JvdXBzPC9rZXk+Cgk8YXJyYXk+CgkJPHN0cmluZz5ncm91cC5jb20uc3MuaXBob25lLnVnYy5Bd2VtZS5leHRlbnNpb248L3N0cmluZz4KCTwvYXJyYXk+CjwvZGljdD4KPC9wbGlzdD4=\",\"mflag\":257},\"hook\":{\"ker\":[],\"fr\":{},\"fish\":[]},\"wda\":0,\"time\":{\"a\":1552643348,\"m\":1552643348,\"c\":1552643348,\"b\":1552643183},\"extension\":{\"pbv\":\"16E227\",\"pv\":\"12.2\",\"dyuid\":\"8C280345-0164-3B82-A228-224B23CA0E9F\",\"ntfadd\":\"3596551104\",\"obID\":\"com.ss.iphone.ugc.Aweme\",\"otID\":\"3JTPEA4UU7\",\"sjd\":\"0\",\"ivc\":[],\"dsc\":\"dyld_v1 arm64\",\"sch\":\"3058109338\",\"hwm\":\"D321AP\"}}",
            "sec": "{\"dbg\":{\"ctl\":0,\"sys_ctl\":0,\"tty\":0,\"oppid\":0,\"wp\":0,\"ntf\":0},\"jb\":{\"dylb\":0,\"file\":0,\"file_sys\":0,\"env\":\"\",\"mods\":[\"/private/var/containers/Bundle/Application/" + aweme_path + "/Aweme.app/Frameworks/AgoraRtcEngineKit.framework/AgoraRtcEngineKit\",\"/private/var/containers/Bundle/Application/" + aweme_path + "/Aweme.app/Frameworks/LiveStreamFramework.framework/LiveStreamFramework\",\"/private/var/containers/Bundle/Application/" + aweme_path + "/Aweme.app/Frameworks/AwemeDylib.framework/AwemeDylib\",\"/usr/lib/libobjc-trampolines.dylib\"]},\"rebuild\":{\"sci\":0,\"entitlement\":\"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y29tLmFwcGxlLmRldmVsb3Blci5uZXR3b3JraW5nLndpZmktaW5mbzwva2V5PgoJPHRydWUvPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLnRlYW0taWRlbnRpZmllcjwva2V5PgoJPHN0cmluZz4zSlRQRUE0VVU3PC9zdHJpbmc+Cgk8a2V5PmFwcGxpY2F0aW9uLWlkZW50aWZpZXI8L2tleT4KCTxzdHJpbmc+M0pUUEVBNFVVNy5jb20uc3MuaXBob25lLnVnYy5Bd2VtZTwvc3RyaW5nPgoJPGtleT5hcHMtZW52aXJvbm1lbnQ8L2tleT4KCTxzdHJpbmc+cHJvZHVjdGlvbjwvc3RyaW5nPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLmFzc29jaWF0ZWQtZG9tYWluczwva2V5PgoJPGFycmF5PgoJCTxzdHJpbmc+YXBwbGlua3M6ZG91eWluLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6d3d3LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmFwaS1zcGUtZC5zbnNzZGsuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczphcGktc3BlLWUuc25zc2RrLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6YW1lbXYuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp3d3cuYW1lbXYuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp2LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmllc2RvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOnd3dy5pZXNkb3V5aW4uY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp0ZXN0LXd3dy5kb3V5aW4uY29tPC9zdHJpbmc+Cgk8L2FycmF5PgoJPGtleT5jb20uYXBwbGUuc2VjdXJpdHkuYXBwbGljYXRpb24tZ3JvdXBzPC9rZXk+Cgk8YXJyYXk+CgkJPHN0cmluZz5ncm91cC5jb20uc3MuaXBob25lLnVnYy5Bd2VtZS5leHRlbnNpb248L3N0cmluZz4KCTwvYXJyYXk+CjwvZGljdD4KPC9wbGlzdD4=\",\"mflag\":257},\"hook\":{\"ker\":[],\"fr\":{},\"fish\":[]},\"wda\":0,\"time\":{\"a\":" + ta + ",\"m\":" + ta + ",\"c\":" + ta + ",\"b\":" + tb + "},\"extension\":{\"pbv\":\"" + utiles.get_osversion_code(os_version) + "\",\"pv\":\"" + os_version + "\",\"dyuid\":\"" + dyuid + "\",\"ntfadd\":\"3596551104\",\"obID\":\"com.ss.iphone.ugc.Aweme\",\"otID\":\"3JTPEA4UU7\",\"sjd\":\"0\",\"ivc\":[],\"dsc\":\"dyld_v1 arm64\",\"sch\":\"3058109338\",\"hwm\":\"" + hwm + "\"}}",
            "display":"{},{}".format(1125, 2436),
            "p1":device_id,
            "network":"wifi",
            "outerExInfo":{"STZone":"Asia/Shanghai"},
            "wifiip":wifiip,
            "p2":install_id,
            "proxyport":"-1",
            "dpod":{"pod":""},
            "scene":scene
        }
        return xlog

    @staticmethod
    def genXlogStr():
        xlog_str = '{"host":0,"cpu_percent":25,"charge":1,"display":"750,1334","sdused":13414432768,"p1":"68322498900","scene":"install","location":"","sid":"","sdtotal":27330084864,"wifiip":"192.168.42.128","acc":"029d8392809ff25899b3642b0475c34e4afba66426f394cfe76a69269b5784e8b4c0e2a0546e311f246b6a36e4fbf4116e0bb0174|02e89e38eae8b77edeea9ed7c5dc4eb0a16e1e2f2ae96e911191cddd668afa15d61378df5657593d9b1770431db9c6828130ca0174|02d8350fcc2911c40ae67ff9cdc35296e14c3d17936df31c75082518bd79b32a0b53b02011440161ccd6f20df002e4f2c9405a217","p2":"75631617591","network":"wifi","proxyport":"-1","first":"1560784539","proxyip":"","bundleID":"com.ss.iphone.ugc.Aweme","brand":"iPhone 6s","imsi":"","channel":"App Store","outerExInfo":{"STZone":"Asia\\/Shanghai"},"wifibssid":"a4:56:8b:96:22:39","battery":100,"mem:2102919168,"gyro":"028a7ec4618f9b6d1d0a788304925402ebdc1e13e799b0784993ce2ccb25ace8cf8f4433e89ee70da6741db39424741b73604c2070|027b194634473854785d399c024bc62471b1353a521ce62b967ed5fad72a778e8d71ffee579402d47845e66cdef5549db970c20174|02429d2ba2e2a4ac1b6075df314de9c403e066ee282691a286439fb1fc1f446b89ecb6b48e054e3447a6efdf62e5ddd86d05f2074","active":1560352536.120358,"idfa":"C3B7D373-C20B-4D81-9E64-B5F3A2A12C72","ML":"zh-Hans-CN","idfv":"83B1BF48-94AB-4330-8E99-305888C589F6","os":"iOS 10.2","vpn":0,"sec":"{\\"dbg\\":{\\"ctl\\":0,\\"sys_ct\\":0,\\"tty\\":0,\\"oppid\\":0,\\"wp\\":0,\\"ntf\\":0},\\"jb\\":{},\\"rebuild\\":{\\"sci\\":0,\\"entitlement\\":\\"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFRcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y29tLmFwcGxlLmRldmVsb3Blci5uZXR3b3JraW5nLndpZmktaW5mbzwva2V5PgoJPHRydWUvPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLnRlYW0taWRlbnRpZmllcjwva2V5PgoJPHN0cmluZz4zSlRQRUE0VVU3PC9zdHJpbmc+Cgk8a2V5PmFwcGxY2F0aW9uLWlkZW50aWZpZXI8L2tleT4KCTxzdHJpbmc+M0pUUEVBNFVVNy5jb20uc3MuaXBob25lLnVnYy5Bd2VtZTwvc3RyaW5nPgoJPGtleT5hcHMtZW52aXJvbm1lbnQ8L2tleT4KCTxzdHJpbmc+cHJvZHVjdGlvbjwvc3RyaW5nPgoJPGtleT5jb20uYXBwbGUuZGV2ZWxvcGVyLmFzc29jaWF0ZWQtZG9tYWluczwva2V5PgoJPGFycmF5PgoJCTxzdHJpbmcYXBwbGlua3M6ZG91eWluLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6d3d3LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmFwaS1zcGUtZC5zbnNzZGsuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczphcGktc3BlLWUuc25zc2RrLmNvbTwvc3RyaW5nPgoJCTxzdHJpbmc+YXBwbGlua3M6YW1lbXYuY29tPC9zdHJbmc+CgkJPHN0cmluZz5hcHBsaW5rczp3d3cuYW1lbXYuY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp2LmRvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOmllc2RvdXlpbi5jb208L3N0cmluZz4KCQk8c3RyaW5nPmFwcGxpbmtzOnd3dy5pZXNkb3V5aW4uY29tPC9zdHJpbmc+CgkJPHN0cmluZz5hcHBsaW5rczp0ZXN0LXd3dy5b3V5aW4uY29tPC9zdHJpbmc+Cgk8L2FycmF5PgoJPGtleT5jb20uYXBwbGUuc2VjdXJpdHkuYXBwbGljYXRpb24tZ3JvdXBzPC9rZXk+Cgk8YXJyYXk+CgkJPHN0cmluZz5ncm91cC5jb20uc3MuaXBob25lLnVnYy5Bd2VtZS5leHRlbnNpb248L3N0cmluZz4KCTwvYXJyYXk+CjwvZGljdD4KPC9wbGlzdD4=\\",\\"mflag\\":257},\\"hook\\":{\\"ker\":[],\\"fish\\":[]},\\"wda\\":0,\\"time\\":{\\"a\\":1515988865,\\"m\\":1480990540,\\"c\\":1481007199,\\"b\\":1480990540},\\"extension\\":{\\"pbv\\":\\"14C92\\",\\"pv\\":\\"10.2\\",\\"dyuid\\":\\"F54ED85A-9425-3887-886A-8028E20ED8BA\\",\\"ntfadd\\":\\"3596551104\\",\\"skc\\":\\"\\",\\"obID\\":\\"com.ss.iphone.ugc.Aweme\\",\\"otID\\":\\"3JTPEA4UU7\\",\\"sjd\\":\\"0\\",\\"ivc\\":[],\\"dsc\\":\\"dyld_v1   arm64\\",\\"sch\\":\\"3058109338\\",\\"hwm\\":\\"N71AP\\",\\"glb\\":\\"TMPDIR=\\/private\\/var\\/mobile\\/Containers\\/Data\\/Applicatio\\/38AD57CE-3A7D-4CB6-A922-BBF765645179\\/tmp|__CF_USER_TEXT_ENCODING=0x1F5:0:0|HOME=\\/private\\/var\\/mobile\\/Containers\\/Data\\/Application\\/38AD57CE-3A7D-4CB6-A922-BBF765645179|SHELL=\\/bin\\/sh|CFFIXED_USER_HOME=\\/private\\/var\\/mobile\\/Containers\\/Data\\/Appication\\/38AD57CE-3A7D-4CB6-A922-BBF765645179|PATH=\\/usr\\/bin:\\/bin:\\/usr\\/sbin:\\/sbin|LOGNAME=mobile|XPC_SERVICE_NAME=UIKitApplication:com.ss.iphone.ugc.Aweme[0xe778]|CLASSIC=0|_MSSafeMode=0|USER=mobile|XPC_FLAGS=0x0|\\",\\"obv\\":\\"\\",\\"ldp\\":\\"\\"}}","MN":Li Tang\'s iPhone","cpu":"arm64 v8","dns":["192.168.42.1"],"dpod":{"pod":""},"time":1560784553.904264,"wifissid":"dengli","timestamp":"021fe60ab1f121fe17d2e996087031b35d4ee38c2adf90c34460c90174|02b772e6b717d3dc1a521067cd7acfaeae66bd0f8239ae9a73c0770174|02fe2b5dc70d3be216c280a6c2636ea5b5fcfad3390d3715050d52070"}'
        return xlog_str

    @staticmethod
    @retry(tries=10, delay=2)
    def get_proxy():
         #return "127.0.0.1:8081"
         logger.info("获取代理地址:")
         while True:
            url = "http://ip.11jsq.com/index.php/api/entry?method=proxyServer.generate_api_url&packid=0&fa=0&fetch_key=&groupid=0&qty=1&time=3&pro=&city=&port=1&format=txt&ss=1&css=&dt=1&specialTxt=3&specialJson="
            ret = requests.get(url)
            if str(ret.content, encoding='utf-8').find("登录IP不是白名单IP"):
                break
            logger.warning(str(ret.content, encoding='utf-8'))
            res = json.loads(str(ret.content, encoding='utf-8'))
            reg = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
            item = re.findall(reg, res["msg"])
            whiteip = item[0]
            url = '''http://www.jinglingdaili.com/Users-whiteIpAddNew.html?appid=137&appkey=42913b5622a4208366574daef1906aa7&whiteip=%s&index=0''' % whiteip
            con = requests.get(url).content
            time.sleep(3)

         return str(ret.content, encoding='utf-8')

    @staticmethod
    @retry(tries=10, delay=2)
    def get_byte(url):
        # return "127.0.0.1:8081"
        logger.info("获取内容:{}".format(url))
        ret = requests.get(url)
        return ret.content


    @staticmethod
    def delete_proxy(proxy):
        pass

    @staticmethod
    def uuid():
        return str(uuid.uuid4())

    @staticmethod
    def mosaic_picture(pic1, pic2, ques=""):

        resp2 = requests.get(pic1)
        image2 = Image.open(BytesIO(resp2.content))
        w2, h2 = image2.size
        scale = w2 / 268.0
        w2 = int(w2 / scale)
        h2 = int(h2 / scale)
        image2 = image2.resize((w2, h2), Image.ANTIALIAS)
        if (pic2 == "" or pic2 == None) and ques != "":
            logger.debug("准备创建文字图片")
            image1 = Image.new(image2.mode, (w2, 40))
            logger.debug("创建image1结束")
            font_path = os.path.dirname(os.path.realpath(__file__)) + "/simsun.ttc"
            font = ImageFont.truetype(font_path, size=20, encoding="utf-8")
            logger.debug("创建font结束")
            draw = ImageDraw.Draw(image1)
            logger.debug("创建draw结束")
            draw.text((100, 10), ques, font=font, fill=(255, 255, 255))
            logger.debug("绘制文字图片")
        else:
            resp1 = requests.get(pic2)
            image1 = Image.open(BytesIO(resp1.content))

        w1, h1 = image1.size
        w1 = int(w1/scale)
        h1 = int(h1/scale)
        image1 = image1.resize((w1, h1), Image.ANTIALIAS)
        result = Image.new(image1.mode, (w2, h1 + h2))
        result.paste(image2, (0, 0))
        result.paste(image1, (0, h2))
        result.save("/tmp/1.png")
        return result

    @staticmethod
    def mosaic_picture_base64(pic1, pic2, ques=""):
        result = utiles.mosaic_picture(pic1, pic2, ques=ques)
        output_buffer = BytesIO()
        try:
            result.save(output_buffer, format='JPEG')
        except:
            result.save(output_buffer, format='PNG')
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data)
        return base64_str  # .decode('utf-8')

    @staticmethod
    def reset_pppoe():
        #os.system('killall -9 ssh')
        os.system('ssh root@61.142.75.30 -p 20004 pppoe-stop')
        os.system('ssh root@61.142.75.30 -p 20004 pppoe-start')
        #pid = os.fork()
        #if pid == 0:
        #    os.system('nohup ssh -N -D 1081 root@61.142.75.30 -p 20004 &')
        #    exit()

    @staticmethod
    def md5(src):
        md = hashlib.md5()
        if type(src) == str:
            md.update(src.encode('utf-8'))
        elif type(src) == bytes:
            md.update(src)
        else:
            logging.error("md5加密类型不支持 {} {}".format(type(src), src))
            exit(-1)
        return md.hexdigest()

    @staticmethod
    def numberToVarint(n):
        # little-endian
        value = int(n)
        if value == 0:
            return bytearray([0x00])
        result = bytearray()
        round = 0
        while value > 0:
            result.append(value & 0b1111111 | 0b10000000 if value > 127 else value & 127)
            value >>= 7
            round += 1
        return (bytes(result), round - 1)

    @staticmethod
    def protobuf_decode_raw(protoc_buff):
        p = Popen(["protoc", "--decode_raw"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        result = p.communicate(protoc_buff)[0].decode('utf-8', errors='replace')
        return result

    @staticmethod
    def video_to_id(url):
        resp = requests.get(url, allow_redirects=False)
        location = resp.headers['Location']
        return location.split("/video/")[1].split("/")[0]

    @staticmethod
    def get_project_conf():
        conf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../conf/conf.ini'))
        return toml.load(conf_path)

    @staticmethod
    def append_garbage_data(file_bytes):
        data = utiles.md5(str(uuid.uuid4())).encode()
        return file_bytes + data

    @staticmethod
    def get_image_size(img_bytes):
        image = Image.open(BytesIO(img_bytes))
        w, h = image.size
        return w, h

    @staticmethod
    def loop_sleep(timeout=100, msg=""):
        while timeout > 0:
            logger.info(msg.format(timeout))
            time.sleep(1)
            timeout -= 1

    @staticmethod
    def random_emoji():
        random.sample()


    @staticmethod
    def random_str(len):
        ran_str = ''.join(random.sample(string.hexdigits, len))
        return ran_str

    @staticmethod
    def randomMAC():
        mac = [0xa4, 0x52, 0x00,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return (':'.join(map(lambda x: "%x" % x, mac))).upper()

    @staticmethod
    def all_osversion():
        version = {
            "12.2": "16E227",
            "12.1.4": "16D57",
            "12.1.3": "16D40",
            "12.1.2": "16C104",
            "12.1.1": "16C50",
            "12.1": "16B92",
            "12.0.1": "16A405",
            "12.0": "16A366"
        }
        return version

    @staticmethod
    def random_osversion():
        return "10.2"
        #return random.sample(utiles.all_osversion().keys(), 1)[0]

    @staticmethod
    def get_osversion_code(version):
        return utiles.all_osversion()[version]

    @staticmethod
    def get_aweme_headers(osversion="9.2", app_version="6.7.0", version_code="62006"):
        version_code = APPINFO['build_number']
        aweme_header = {
            "sdk-version": "1",
            "User-Agent": "Aweme {} (iPhone; iOS {}; Scale/2.00)".format(app_version, osversion)
        }
        return aweme_header



FORMAT = "%(asctime)s %(name)s(%(process)d) %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s"

coloredlogs.install(level="INFO", logger=logger, fmt=FORMAT)

USE_PROXY = True
if __name__ == '__main__':
    print(utiles.mosaic_picture_base64("http://sf3-dycdn-tos.pstatp.com/obj/security-captcha/text_d95dac3e96310a95d28fbc7b12f3ad0175b64b81_2_1.jpg",
                          "http://sf3-dycdn-tos.pstatp.com/obj/security-captcha/text_d95dac3e96310a95d28fbc7b12f3ad0175b64b81_1_1.jpg"))
