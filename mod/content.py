from urllib.parse import urlparse, quote
from sqlalchemy import Column, String, Integer, VARCHAR, ForeignKey, Float, BOOLEAN, DateTime, VARBINARY
from sqlalchemy.orm import relationship, backref

from datetime import datetime
from libs.utils import *
import gzip, requests, pickle, json, base64
from libs.tracker_server import TrackerService
from mod.device import Device

from urllib.parse import quote
import time
from urllib.parse import unquote, quote
from retry import retry
import re

try:
    import thread
except ImportError:
    import _thread as thread
DEBUG = False


class Content():
    device = Device()
    http =  requests.session()
    proxy = ""

    def save_session(self):
        """保持session对象到数据库"""
        self.session_pick = base64.b64encode(gzip.compress(pickle.dumps(self.http)))

    def get_http(self, use_proxy=True):

        if self.device:
            self.set_tracker()
        if use_proxy and (self.proxy == None or self.proxy == ""):
            self.proxy = utiles.get_proxy()
            print(self.proxy)
        self.proxy_fail_num = 0

    def set_tracker(self):
        # 初始化日志
        self.tracker = TrackerService(iid=self.device.install_id)


    @retry(tries=10, delay=2)
    def orig_get(self, url, params=None, **kwargs):
        """原始http get请求"""

        # 设置代理
        if 'headers' in kwargs.keys():
            headers = kwargs['headers']
            headers['Connection'] = 'close'
        else:
            headers = {'Connection': 'close'}
        if "X-SS-STUB" in headers:
            del (headers['X-SS-STUB'])
        kwargs['headers'] = headers
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 10)

        # 增加 x-headers
        uri = urlparse(url)
        if uri.hostname.find("snssdk.com") >= 0:
            cookie_dict = self.http.cookies.get_dict()
            cookie_string = ""
            for k, v in cookie_dict.items():
                cookie_string += "{}={}; ".format(k, v)
            cookie_string = cookie_string.strip("; ")
            info = {
                "cookie": cookie_string,
                "aid": APPINFO['aid']
            }
            if "accept-language" in headers.keys():
                info["accept-language"] = headers["accept-language"]
            if "user-agent" in headers.keys():
                info["user-agent"] = headers["user-agent"]
            if "sdk-version" in headers.keys():
                info["sdk-version"] = headers["sdk-version"]

            if cookie_string == "":
                del (info['cookie'])
            x_headers = utiles.getXHeaders(url, info)
            for k, v in x_headers.items():
                headers[k] = v
            kwargs['headers'] = headers

        logger.debug("URL: {}".format(url))
        if DEBUG:
            kwargs.setdefault('proxies', {"https": "127.0.0.1:8080"})
        elif USE_PROXY:
            kwargs.setdefault('proxies', {'http': 'http://' + self.proxy, 'https': 'https://' + self.proxy})
        else:
            kwargs.setdefault('proxies', None)
        try:
            logger.debug("kwargs: {}".format(kwargs))
            if params == None:
                resp = self.http.get(url, **kwargs)
            else:
                resp = self.http.get(url, params=params, **kwargs)
            time.sleep(0.01)
            self.proxy_fail_num = 0
        except Exception as e:
            logger.warning("请求错误: {}".format(e))
            utiles.delete_proxy(self.proxy)
            time.sleep(0.01)
            self.proxy_fail_num += 1
            if self.proxy_fail_num >= 3:
                self.proxy = utiles.get_proxy()
                self.proxy_fail_num = 0
            # self.app_start()
            time.sleep(0.5)
            raise
        return resp

    @retry(tries=10, delay=2)
    def orig_post(self, url, params=None, data=None, files=None, jjson=None, **kwargs):
        """原始http post请求"""
        # 设置代理
        if 'headers' in kwargs.keys():
            headers = kwargs['headers']
            headers['Connection'] = 'close'
        else:
            headers = {'Connection': 'close'}
        kwargs['headers'] = headers
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 10)

        # 增加 x-headers
        uri = urlparse(url)
        if uri.hostname.find("snssdk.com") >= 0:
            # 增加 X-SS-STUB 头部
            body_str = ""
            if data != None:
                if type(data) == dict:
                    body_str = utiles.params2str(data)
                elif type(data) == str:
                    body_str = data
                elif type(data) == bytes:
                    body_str = data
            if jjson != None:
                body_str = json.dumps(jjson)

            md5_str = utiles.md5(body_str)

            headers['X-SS-STUB'] = md5_str.upper()
            cookie_dict = self.http.cookies.get_dict()
            cookie_string = ""
            for k, v in cookie_dict.items():
                cookie_string += "{}={}; ".format(k, v)
            cookie_string = cookie_string.strip("; ")
            info = {
                "cookie": cookie_string,
                "aid": APPINFO['aid']
            }
            if "accept-language" in headers.keys():
                info["accept-language"] = headers["accept-language"]
            if "user-agent" in headers.keys():
                info["user-agent"] = headers["user-agent"]
            if "sdk-version" in headers.keys():
                info["sdk-version"] = headers["sdk-version"]

            if cookie_string == "":
                del (info['cookie'])

            if "xlog.snssdk.com" not in url:
                x_headers = utiles.getXHeaders(url, info)
                for k, v in x_headers.items():
                    headers[k] = v
                kwargs['headers'] = headers

        logger.debug("URL: {}".format(url))
        if DEBUG:
            kwargs.setdefault('proxies', {"https": "127.0.0.1:8080"})
        elif USE_PROXY:
            kwargs.setdefault('proxies', {'http': 'http://' + self.proxy, 'https': 'https://' + self.proxy})
        else:
            kwargs.setdefault('proxies', None)
        try:
            resp = self.http.post(url, params=params, data=data, json=jjson, files=files, **kwargs)
            time.sleep(0.01)
            self.proxy_fail_num = 0
        except Exception as e:
            logger.warning("请求错误: {}".format(e))
            utiles.delete_proxy(self.proxy)
            time.sleep(0.01)
            self.proxy_fail_num += 1
            if self.proxy_fail_num >= 3:
                self.proxy = utiles.get_proxy()
                self.proxy_fail_num = 0
            time.sleep(0.5)
            raise
        return resp

    def get(self, host="", path="", params={}, headers=None, sign=True, has_iid=True):
        """发送get请求"""
        common_params = {
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO['ac'],
            "pass-region": "1",
            "pass-route": "1",
            "js_sdk_version": APPINFO["js_sdk_version"],
        }
        if self.device.device_id != None and self.device.device_id != '':
            common_params['iid'] = self.device.install_id
            common_params['device_id'] = self.device.device_id
        params.update(common_params.copy())

        # 转换params quote
        # for k in params.keys():
        #    params[k] = quote(str(params[k]))

        if False:
            sign = utiles.getSign(self.token, params)
            params['mas'] = sign['mas']
            params['as'] = sign['as']
            params['ts'] = sign['ts']
        logger.debug("URL: https://" + host + path)
        logger.debug("请求参数: " + json.dumps(params))
        query = ""
        for i in params.keys():
            query += "{}={}&".format(i, params[i])
        query = query.strip("&")
        if len(query):
            url = "https://{}{}?{}".format(host, path, query)
        if headers == None:
            headers = utiles.get_aweme_headers(self.device.os_version)  # aweme_header
        resp = self.orig_get(url, params=None, headers=headers,
                             verify=False)
        logger.debug(resp.text)
        return resp

    def post(self, host="", path="", params={}, postParams={}, files=None, headers=None, sign=True):
        """发送post请求"""
        common_params = {
            "iid": self.device.install_id,
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "device_id": self.device.device_id,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO['ac'],
            "pass-region": "1",
            "js_sdk_version": APPINFO["js_sdk_version"],
            "pass-route": "1",
            "mcc_mnc": "46001"
        }
        params.update(common_params.copy())

        # 转换params quote
        # for k in params.keys():
        #    params[k] = quote(str(params[k]))

        if False:
            signParams = {}
            signParams.update(params)
            signParams.update(postParams)
            sign = utiles.getSign(self.token, signParams)
            params['mas'] = sign['mas']
            params['as'] = sign['as']
            params['ts'] = sign['ts']
            logger.debug("URL: https://" + host + path)
            logger.debug("请求参数: " + json.dumps(signParams))

        query = ""
        for i in params.keys():
            query += "{}={}&".format(i, params[i])
        query = query.strip("&")
        if len(query):
            url = "https://{}{}?{}".format(host, path, query)

        if headers == None:
            headers = utiles.get_aweme_headers(self.device.os_version)  # aweme_header
        if files == None:
            resp = self.orig_post(url, params=None, data=postParams, headers=headers, verify=False)
        else:
            resp = self.orig_post(url, params=None, files=files, headers=headers, verify=False)
        logger.debug(resp.text)
        return resp

    def get_common_params(self):
        common_params = {
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO['ac'],
            "pass-region": "1",
            # "js_sdk_version": "1.3.0.1"
        }
        if self.device.device_id != None and self.device.device_id != '':
            common_params['iid'] = self.device.install_id
            common_params['device_id'] = self.device.device_id
        return common_params

    # def upload_file(self, filename='file', data=b'', sign=True):
    #     common_params = self.get_common_params()
    #     params = {}
    #     params.update(common_params.copy())
    #     if sign:
    #         sign = utiles.getSign(self.token, params)
    #         params['mas'] = sign['mas']
    #         params['as'] = sign['as']
    #         params['ts'] = sign['ts']
    #     logger.debug("URL: https://" + host + path)
    #     logger.debug("请求参数: " + json.dumps(params))

    # """

    def replace_device(self, rstr):
        ORIG_IDFA = "06E5F3B1-0535-4097-B801-DD87EFF18C01"
        ORIG_VID = "F50BD7DD-40A1-43E4-988A-1BCAD2579101"
        ORIG_UDID = "47c4a697b78935ffae919fe44b648456f8f64688"
        ORIG_IID = "75953563126"
        ORIG_DID = "68352625710"
        ORIG_OSVERSION = "10.2"
        ORIG_DEVICE_TYPE = "iPhone8,1"
        ORIG_DEVICE_MODEL = "iPhone 6S"
        ORIG_WIDTH = "750"
        ORIG_HEIGHT = "1334"

        rstr = re.sub(ORIG_IDFA, self.device.idfa, rstr)
        #print("替换IDFA: {} -> {}".format(ORIG_IDFA, self.device.idfa))

        rstr = re.sub(ORIG_VID, self.device.vid, rstr)
        #print("替换VID: {} -> {}".format(ORIG_VID, self.device.vid))

        rstr = re.sub(ORIG_UDID, self.device.openudid, rstr)
        #print("替换UDID: {} -> {}".format(ORIG_UDID, self.device.openudid))

        if self.device.device_id != None:
            rstr = re.sub(ORIG_IID, str(self.device.install_id), rstr)
            #print("替换IID: {} -> {}".format(ORIG_IID, self.device.install_id))

            rstr = re.sub(ORIG_DID, str(self.device.device_id), rstr)
            #print("替换DID: {} -> {}".format(ORIG_DID, self.device.device_id))

        # if self.device.device_id != None:
        #     rstr = re.sub(ORIG_IID, str(73848041349), rstr)
        #     print("替换IID: {} -> {}".format(ORIG_IID, 73848041349))
        #
        #     rstr = re.sub(ORIG_DID, str(67760173999), rstr)
        #     print("替换DID: {} -> {}".format(ORIG_DID, 67760173999))

        rstr = re.sub(ORIG_OSVERSION, self.device.os_version, rstr)
        #print("替换OSVERSION: {} -> {}".format(ORIG_OSVERSION, self.device.os_version))

        rstr = re.sub(ORIG_DEVICE_TYPE, self.device.device_type, rstr)
        #print("替换 DEVICE_TYPE: {} -> {}".format(ORIG_DEVICE_TYPE, self.device.device_type))

        rstr = re.sub(ORIG_DEVICE_MODEL, self.device.device_model, rstr)
        #print("替换 DEVICE_MODEL: {} -> {}".format(ORIG_DEVICE_MODEL, self.device.device_model))

        rstr = re.sub(ORIG_WIDTH, self.device.screen_width, rstr)
        #print("替换 WIDTH: {} -> {}".format(ORIG_WIDTH, self.device.screen_width))

        rstr = re.sub(ORIG_HEIGHT, self.device.screen_height, rstr)
        #print("替换 HEIGHT: {} -> {}".format(ORIG_HEIGHT, self.device.screen_height))

        return rstr


    def app_start(self):
        # self.device.screen_height = "1334"
        try:
            self.tracker
        except:
            self.set_tracker()

        common_params = {
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO["ac"],
            "pass-region": "1",
            # "js_sdk_version": "1.3.0.1"
            "mcc_mnc": "",
            "pass-route": "1"
        }
        # try:
        #     resp = self.get(host="dm.toutiao.com", path="/ies/network/aweme/", params=common_params, sign=False)
        # except:
        #     utiles.delete_proxy(self.proxy['http'])
        #     self.proxy = utiles.get_proxy()
        #     return self.app_start()
        #     #exit()

        # resp = self.get(host="security.snssdk.com", path="/passport/token/change/", params=common_params, sign=False)

        # resp = self.get(host="aweme.snssdk.com", path="/aweme/v1/user/", params=common_params).json()
        # # 日志类设置用户ID
        # if resp['status_code'] == 0 and 'uid' in resp['user'].keys():
        #     user_id = resp['user']['uid']
        # else:
        user_id = ''
        self.tracker.set_userid(user_id)
        self.tracker.faker_startlog()

        xlog_url = "https://xlog.snssdk.com/v.s?os_ver=iOS {}&os=1&app_ver={}&ver={}&m=1&channel=pp&aid=1128&region=CN".format(
            self.device.os_version, APPINFO['app_version'], APPINFO['xlog_ver'])
        if self.device.device_id != None and self.device.device_id != "":
            xlog_url += "&did={}".format(self.device.device_id)
        resp = self.orig_get(xlog_url, verify=False, headers={
            "User-Agent": "Aweme/{} CFNetwork/978.0.7 Darwin/18.5.0".format(APPINFO['build_number'])
        })
        logger.debug(resp.content)

        # https://verify.snssdk.com/view
        resp = self.orig_get("https://verify.snssdk.com/view", headers={
            "User-Agent": "Aweme/{} CFNetwork/978.0.7 Darwin/18.5.0".format(APPINFO['build_number'])
        }, verify=False)
        logger.debug(resp.content)

        # https://aweme.snssdk.com/aweme/v1/settings/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&oid=0
        self.get(host="aweme.snssdk.com", path="/aweme/v1/settings/", params={"old": '0'}, sign=False)

        # https://aweme.snssdk.com/aweme/v2/platform/share/settings/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079
        self.get(host="aweme.snssdk.com", path="/aweme/v2/platform/share/settings/", params={}, has_iid=False,
                 sign=False)

        # https://aweme.snssdk.com/2/user/info/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=0158641e52c3503e9e503ebdaa8111d6d66793684ca8d2162e6ebe&as=a1d51adc1bd1abd4411005&ts=1539417115
        self.get(host="aweme.snssdk.com", path="/2/user/info/", params={}, has_iid=False)

        xlog_params = {
            "os_ver": "iOS {}".format(self.device.os_version),
            "os": 1,
            "app_ver": APPINFO['version_code'],
            "ver": APPINFO['xlog_ver'],
            "m": 1,
            "channel": "pp",
            "aid": APPINFO["aid"],
            "region": "CN"
        }
        if self.device.device_id != None and self.device.device_id != "":
            xlog_params['did'] = self.device.device_id
        resp = self.get(host="xlog.snssdk.com", path="/v2/s", params=xlog_params, headers={
            "User-Agent": "Aweme/{} CFNetwork/978.0.7 Darwin/18.5.0".format(APPINFO['build_number'])
        }, sign=False)

        # resp = self.get(host="xlog.snssdk.com", path="/v2/s", params={
        #     "os_ver": "iPhone OS {}".format(self.device.os_version),
        #     "os": 1,
        #     "app_ver": APPINFO['version_code'],
        #     "ver": "0.8.8.6-fix1",
        #     "m": 1,
        #     "channel": APPINFO["channel"],
        #     "aid": "1128",
        #     "region": "CN"
        # }, headers={
        #     "User-Agent": "Aweme/{} CFNetwork/758.0.2 Darwin/15.0.0".format(APPINFO['build_number'])
        # }, sign=False)

        # https://aweme.snssdk.com/api/ad/splash/aweme/v15/?resolution=640*1136&carrier=%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A&vid=482F446D-760E-485D-B2BA-E6BA6FC74A56&app_name=aweme&access=none&channel=App%20Store&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&display_density=640*1136&device_type=iPhone%205C&update_version_code=27014&aid=1128&idfv=482F446D-760E-485D-B2BA-E6BA6FC74A56&os_version=9.0.1&device_platform=iphone&ac=none&language=zh-Hans-HK&version_code=2.7.0&idfa=B28DF862-3488-43E2-8AE2-E319A8875B03&sdk_version=0.2.12&sys_region=HK&sim_region=&user_id=&mas=01cbe4faf0f3fd83033542c13580f0d3a06eb816c06ac953bf8287&as=a1f55a8cf9d1cb94913332&ts=1539417113
        self.get(host="lf.snssdk.com", path="/api/ad/splash/aweme/v15/", params={
            "resolution": "{}*{}".format(self.device.screen_width, self.device.screen_height),
            "carrier": "中国联通",
            "sys_region": "CN",
            "sim_region": "",
            "user_id": "",
            "sdk_version": "0.4.7.3",
            "device_type": self.device.device_model,
            "language": "zh-Hans-CN",
            "mac_address": "02:00:00:00:00:00",
            "bh": "252",
            "is_cold_start": "1",
            "user_period": 0,
        }, has_iid=False)

        self.app_xlog(scene="timer")

        self.orig_post("https://mon.snssdk.com/monitor/collect/?sdk_version=1.0.0&aid={}".format(APPINFO["aid"]),
                       jjson=common_params, headers=utiles.get_aweme_headers(self.device.os_version))

        self.get(host="security.snssdk.com", path="/passport/token/beat/", params={}, has_iid=False)

        self.device_register()

        # https://aweme.snssdk.com/aweme/v1/rate/settings/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=015842598a3f3fdd88860453e59239a3f197d39d4e54a85881d8d8&as=a185ca1c5cd12b54819568&ts=1539417116
        self.get(host="aweme.snssdk.com", path="/aweme/v1/rate/settings/", params={})

        # https://aweme.snssdk.com/aweme/v1/crawl/sdk/log/
        params = {
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO["ac"],
            "operator_type": "cloud_control",
            "pass-region": "1",
            "js_sdk_version": APPINFO["js_sdk_version"]
        }
        resp = self.orig_post("https://aweme.snssdk.com/aweme/v1/crawl/sdk/log/", data=params,
                              headers=utiles.get_aweme_headers(self.device.os_version), verify=False)
        logger.debug(resp.text)

        # https://aweme.snssdk.com/api/2/article/city/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=01614011b60310873e978907ec93fec5dbcf3c1068a2f6c5e8ceb1&as=a1554a4c59316bb4a16600&ts=1539417113
        self.get(host="aweme.snssdk.com", path="/api/2/article/city/", params={}, has_iid=False)

        # https://aweme.snssdk.com/aweme/v1/abtest/param/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&new_user_tab_change_switch=70&mas=014fd57045110b24cb7d93de3c4b81538b0545bf18544ae47fa4e1&as=a1d5aa4cfac13bc4d10556&ts=1539417114
        self.get(host='aweme.snssdk.com', path='/aweme/v1/abtest/param/', params={
            'new_user_tab_change_switch': 70
        }, has_iid=False)

        self.app_log(path="/service/2/log_settings/")

        # https://security.snssdk.com/passport/token/beat/?channel=App%20Store&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=mobile&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=015f2735de0120321059f47b90bd41699e4f25b0a79ddab0ffd6a8&as=a1054acc59f17b74516818&ts=1539417113
        self.get(host="security.snssdk.com", path="/passport/token/beat/", params={}, has_iid=False)

        # https://aweme.snssdk.com/aweme/v1/crawl/sdk/log/
        resp = self.orig_post("https://aweme.snssdk.com/aweme/v1/crawl/sdk/log/", data=params,
                              headers=utiles.get_aweme_headers(self.device.os_version), verify=False)
        # logger.debug(resp.text)
        feed_ret = self.get(host="aweme.snssdk.com", path="/aweme/v1/feed/", params={
            "count": 6,
            "feed_style": 0,
            "filter_warn": 0,
            "max_cursor": 0,
            "min_cursor": 0,
            "pull_type": 4,
            "type": 0,
            "volume": 0.00
        }).json()

        if feed_ret['status_code'] == 0:
            request_id = feed_ret['log_pb']['impr_id']
            aweme_id = feed_ret['aweme_list'][0]['aweme_id']
            # print('aweme_id: ', aweme_id)
            music_id = feed_ret['aweme_list'][0]['music']['mid']
            # print('music_id: ', music_id)
            author_id = feed_ret['aweme_list'][0]['author']['uid']
            # print('author_id: ', author_id)
            self.tracker.set_requestid(request_id)
            logger.info("feed request id: {}".format(request_id))
        else:
            aweme_id = ''
            music_id = ''
            author_id = ''

        data = {
            "aid": APPINFO["aid"],
            "app_language": "",
            "app_name": APPINFO["app_name"],
            "app_region": "",
            "channel": APPINFO["channel"],
            "device_id": self.device.device_id,
            "install_id": self.device.install_id,
            "language": "zh",
            "notice": "0",
            "os": "iOS",
            "os_version": self.device.os_version,
            "package": "com.ss.iphone.ugc.Aweme",
            "push_sdk": "[13]",
            "region": "CN",
            "system_notify_status": 1,
            "tz_name": "Asia/Shanghai",
            "tz_offset": "28800",
            "version_code": APPINFO['version_code']
        }
        self.post(host="ib.snssdk.com", path="/cloudpush/update_sender/", params={}, postParams=data, sign=False)

        self.app_log()

        # https://aweme.snssdk.com/aweme/v1/abtest/param/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&new_user_tab_change_switch=70&mas=01e91716632ab0c3cf91cdf19f742aa21bde84c0610b8aa4a904ee&as=a1850aecdbe12b54813753&ts=1539417115
        self.get(host="aweme.snssdk.com", path="/aweme/v1/abtest/param/", params={"new_user_tab_change_switch": 19})

        # https://ib.snssdk.com/service/settings/v2/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&app=1&mas=01b0cfd081839d6d9a5290667f2a1cdb1a652511c61f340e88d8d8&as=a125baacab512b74816368&ts=1539417115
        # self.get(host="ib.snssdk.com", path="/service/settings/v2/", params={"app": 1})

        # https://aweme.snssdk.com/aweme/v1/aweme/stats/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=011e3bf9ab3df3fb48347d9d31529cc6d8210b3a7ddf7bed2bd6a8&as=a1456a5c5cf18bf4113418&ts=1539417116
        self.post(host="aweme.snssdk.com", path="/aweme/v1/aweme/stats/", params={}, postParams={
            "aweme_type": 0,
            "item_id": "6608817376785861900",
            "play_delta": 1,
            "tab_type": 0
        })

        # https://aweme.snssdk.com/aweme/v1/check/in/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=012af3370952be70dd9b7c0828c9a85d36ba99ed2680a279ac028e&as=a1c58a3c8c41eb74517633&ts=1539417116
        self.get(host="aweme.snssdk.com", path="/aweme/v1/check/in/", params={})

        self.post(host="aweme.snssdk.com", path="/aweme/v1/check/in/", params={}, postParams={
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'device_id': '56780280194'
        })

        self.get(host="aweme.snssdk.com", path="/aweme/v2/activity/evening/info/", params={}).json()

        # https://lf.snssdk.com/service/2/app_alert/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=01768ca2d91b5536ec5e0cfb5281f4d17522729b47e305468d86a7&as=a1d58a2cfc314b54611812&ts=1539417116
        self.get(host='lf.snssdk.com', path='/service/2/app_alert/', params={})

        self.get(host="ib.snssdk.com", path="/user/privacy_mobile/v1/control_auth/", params={}).json()

        self.get(host="lf.snssdk.com", path="/feedback/2/list/", params={"appkey": "aweme-ios"}).json()

        # https://aweme.snssdk.com/aweme/v1/im/resources/?resource_type=STICKER&iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=011868cf90e1c7d10d89f742d2221b3b717c188536489d0325cf31&as=a1850a7c3c719bc4216780&ts=1539417116
        self.get(host="aweme.snssdk.com", path="/aweme/v1/im/resources/", params={'resource_type': 'STICKER'})

        # https://aweme.snssdk.com/aweme/v1/rate/settings/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=01a8d3971f24f6e0dc554d65bd95319209437cebb69df7131de6a7&as=a1e56abc3c61bbc4714614&ts=1539417116
        self.get(host='aweme.snssdk.com', path='/aweme/v1/rate/settings/', params={})

        # https://aweme.snssdk.com/aweme/v1/app/promotion/item/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&device_id=58130340877&mas=01823ea640ba5cbaf951562cd1c58bbd2344070ce63fbb20fbe0c7&as=a1d53a7cfc31ebd4f14674&ts=1539417116
        self.get(host='aweme.snssdk.com', path='/aweme/v1/app/promotion/item/', params={})

        self.post(host='ib.snssdk.com', path='/service/1/update_token/', params={}, postParams={
            'aid': APPINFO["aid"],
            'app_name': APPINFO["app_name"],
            'device_id': self.device.device_id,
            'install_id': self.device.install_id
        }).json()

        self.post(host='lf.snssdk.com', path='/service/1/app_logout/', params={}, postParams={
            'token': '736329736b2d50ab52070e6107fc188032f32b5d66c0f4e8409e1b9694566af9'
        })

        # http://ib.snssdk.com/user/privacy_mobile/v1/control_auth/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&carrier=%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A&mas=0130a6eeb301b83f17d9862614d7925b5fd1dc132d19f5954148d8&as=a1459a0ccc010b64319461&ts=1539417116
        self.get(host='ib.snssdk.com', path='/user/privacy_mobile/v1/control_auth/', params={'carrier': '中国联通'})

        # https://aweme.snssdk.com/aweme/v1/theme/package/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&mas=019f18638d83f953efe60c19a7164013aaa56d38b47919deaad6a8&as=a1256a8c6dc13b94710918&ts=1539417117
        self.get(host='aweme.snssdk.com', path='/aweme/v1/theme/package/', params={})

        # http://ib.snssdk.com/user/privacy_mobile/v1/get_mobile/?iid=46128094488&idfa=490AABE2-30CF-4D9A-A9A0-525E7627435B&version_code=2.7.0&device_type=iPhone5,3&channel=App%20Store&os_version=9.0.1&screen_width=640&vid=4B47C28B-3A9E-4238-A382-ABBA3574F5D1&device_id=58130340877&os_api=18&app_name=aweme&build_number=27014&device_platform=iphone&app_version=2.7.0&ac=WIFI&aid=1128&openudid=a7c647a6923d8959896db6ccc7c8b3a4a1ad4079&carrier=%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A&carrier_type=2&cellular=4g&error_description=Network%20is%20unreachable&need_mobile=1&retry_time=1&sdk_response=%7B%0A%20%20%22NSLocalizedFailureReason%22%20%3A%20%22Error%20in%20connect%28%29%20function%22%2C%0A%20%20%22NSLocalizedDescription%22%20%3A%20%22Network%20is%20unreachable%22%2C%0A%20%20%22error%22%20%3A%20%22Error%20Domain%3DTTTelecomGetPhoneErrorDomain%20Code%3D51%20%5C%22Network%20is%20unreachable%5C%22%20UserInfo%3D%7Berror_code%3D51%2C%20http_error_code%3D51%2C%20client_error_code%3D-302%2C%20NSLocalizedFailureReason%3DError%20in%20connect%28%29%20function%2C%20message%3DNetwork%20is%20unreachable%2C%20NSLocalizedDescription%3DNetwork%20is%20unreachable%7D%22%0A%7D&wifi_env=1&mas=01970ef2c4b0b85bb7de711ae35f778d5d791c87dfa895c0d864ee&as=a185dabcee211b74815455&ts=1539417118
        self.get(host='ib.snssdk.com', path='/user/privacy_mobile/v1/get_mobile/', params={'carrier': '中国联通',
                                                                                           'carrier_type': 2,
                                                                                           'cellular': '4g',
                                                                                           'error_description': 'Network is unreachable',
                                                                                           'need_mobile': 1,
                                                                                           'retry_time': 1,
                                                                                           'sdk_response': '{}',
                                                                                           'wifi_env': 1})

        # https://gecko.snssdk.com/gecko/server/device/checkin
        self.orig_post('https://gecko.snssdk.com/gecko/server/device/checkin', data={
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'device_id': self.device.device_id
        }, verify=False, headers=utiles.get_aweme_headers(self.device.os_version))

        self.orig_get('https://gecko.snssdk.com/gecko/server/package', params={
            'app_version': APPINFO['app_version'],
            'channel': 'wallet,douyin_falcon,falcon_dyfe',
            'os': 'ios',
            'did': self.device.device_id,
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'package_version': '0,0,0'
        }, headers=utiles.get_aweme_headers(self.device.os_version))

        self.orig_get('https://gecko.snssdk.com/gecko/server/package', params={
            'app_version': APPINFO['app_version'],
            'channel': 'rn_base_ios,rn_patch_ios',
            'os': 'ios',
            'did': self.device.device_id,
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'package_version': '0,0'
        }, headers=utiles.get_aweme_headers(self.device.os_version))

        # self.app_xlog(scene="install")
        self.app_xlog(scene="cold_start")

        self.tracker.faker_startlog_next(aweme_id, music_id)
        self.app_log()

    # """

    def get_isp(self):
        # isp = self.proxy_isp
        isp = "移动"
        return "中国{}".format(isp)

    """
    def app_start(self):
        logger.info("开始执行app_start")
        aweme_header_2 = {
            #"User-Agent": "Aweme/{} CFNetwork/758.0.2 Darwin/15.0.0".format(APPINFO['build_number'])
            "User-Agent": "Aweme {} rv:{} (iPhone; iOS 10.2; zh_CN) Cronet".format(APPINFO['version_code'], APPINFO['build_number'])
        }
        try:
            self.tracker
        except:
            self.set_tracker()

        self.get(host="dm.toutiao.com", path="/ies/network/aweme/", sign=False)

        resp = self.get(host="aweme.snssdk.com", path="/aweme/v1/user/", params={"ac": "mobile"}).json()
        # 日志类设置用户ID
        if resp['status_code'] == 0 and "user" in resp and 'uid' in resp['user'].keys():
            user_id = resp['user']['uid']
        else:
            user_id = ''
        self.tracker.set_userid(user_id)
        self.tracker.faker_startlog()

        self.orig_get(url="https://xlog.snssdk.com/v.s", params={
            "os_ver": "iPhone OS {}".format(self.device.os_version),
            "os": 1,
            "app_ver": APPINFO['version_code'],
            "channel": APPINFO["channel"],
            "ver": APPINFO["app_version"],
            "region": "CN",
            "m": 1,
            "aid": APPINFO["aid"],
            "did": self.device.device_id
        }, headers=aweme_header_2)

        self.orig_get(url="https://xlog.snssdk.com/v2/s", params={
            "os_ver": "iPhone OS {}".format(self.device.os_version),
            "os": 1,
            "app_ver": APPINFO['version_code'],
            "channel": APPINFO["channel"],
            "ver": APPINFO["app_version"],
            "region": "CN",
            "m": 1,
            "aid": APPINFO["aid"],
            "did": self.device.device_id
        }, headers=aweme_header_2)

        self.get(host="aweme.snssdk.com", path="/2/user/info/", params={"ac": "mobile"})

        self.get(host="security.snssdk.com", path="/passport/token/change/", params={"ac": "mobile"}, sign=False)

        self.get(host="aweme.snssdk.com", path="/aweme/v1/settings/", params={"ac": "mobile", "oid": 0}, sign=False)

        #self.app_xlog(scene="timer")

        self.device_register()

        self.app_xlog(scene="time")
        self.app_xlog(scene="Marionette")
        # todo ... xlog post data   v2/r
        # todo ... xlog post data   v2/r
        # todo ... xlog post data   v2/r


        self.get(host="aweme.snssdk.com", path="/aweme/v2/platform/share/settings/", params={"ac": "mobile"}, sign=False)

        logger.info("第一次/v1/rate/settings")
        self.get(host="aweme.snssdk.com", path="/aweme/v1/rate/settings/")

        self.get(host="aweme.snssdk.com", path="/api/2/article/city/", params={"ac": "mobile"})

        self.get(host="aweme.snssdk.com", path="/api/ad/splash/aweme/v15/", params={
            "sdk_version": "0.3.5",
            "language": "zh-Hans",
            "display_density": "{}*{}".format(self.device.screen_width, self.device.screen_height),
            "resolution": "{}*{}".format(self.device.screen_width, self.device.screen_height),
            "update_version_code": APPINFO["version_code"],
            "access": "none",
            "carrier": self.get_isp(),
            "ac": "none",
            "idfv": self.device.vid,
            "bh": 215,
            "sys_region": "CN",
            "sim_region": "",
            "user_id": "",
        })

        feed_ret = self.get(host="aweme.snssdk.com", path="/aweme/v1/feed/", params={
            "ac": "mobile",
            "count": 6,
            "feed_style": 0,
            "filter_warn": 0,
            "max_cursor": 0,
            "min_cursor": 0,
            "pull_type": 4,
            "type": 0,
            "volume": 0.50
        }).json()

        try:
            if feed_ret['status_code'] == 0:
                request_id = feed_ret['log_pb']['impr_id']
                aweme_id = feed_ret['aweme_list'][0]['aweme_id']
                music_id = feed_ret['aweme_list'][0]['music']['mid']
                author_id = feed_ret['aweme_list'][0]['author']['uid']
                self.tracker.set_requestid(request_id)
                logger.info("feed request id: {}".format(request_id))
            else:
                aweme_id = ''
                music_id = ''
                author_id = ''
        except:
            logger.error("app_start启动，调用feed接口出错")

        self.get(host='aweme.snssdk.com', path='/aweme/v1/abtest/param/', params={'new_user_tab_change_switch': 75})

        self.app_log(path="/service/2/log_settings/")

        self.app_log()

        data = {
            "aid": APPINFO["aid"],
            "app_language": "",
            "app_name": APPINFO["app_name"],
            "app_region": "",
            "channel": APPINFO["channel"],
            "device_id": self.device.device_id,
            "install_id": self.device.install_id,
            "language": "zh",
            "notice": "0",
            "os": "iOS",
            "os_version": self.device.os_version,
            "package": "com.ss.iphone.ugc.Aweme",
            "push_sdk": "[13]",
            "region": "CN",
            "system_notify_status": 0,
            "tz_name": APPINFO["tz_name"],
            "tz_offset": "28800",
            "version_code": APPINFO['version_code']
        }
        self.post(host="ib.snssdk.com", path="/cloudpush/update_sender/", postParams=data, sign=False)

        self.get(host="security.snssdk.com", path="/passport/token/beat/")

        self.get(host="aweme.snssdk.com", path="/aweme/v2/activity/evening/info/")

        self.get(host="ib.snssdk.com", path="/service/settings/v2/", params={"app": 1})

        # todo ... post data ?
        # todo ... post data ?
        # todo ... post data ?
        self.orig_post("https://mon.snssdk.com/monitor/collect/?sdk_version=1.0.0&", json=self.get_common_params(),
                       headers=aweme_header_2)

        # 第二次调用
        self.get(host="ib.snssdk.com", path="/service/settings/v2/", params={"app": 1})

        feed_ret = self.get(host="aweme-eagle.snssdk.com", path="/aweme/v1/feed/", params={
            "count": 6,
            "feed_style": 0,
            "filter_warn": 0,
            "max_cursor": 0,
            "min_cursor": 0,
            "pull_type": 4,
            "type": 0,
            "volume": 0.50
        }).json()

        try:
            if feed_ret['status_code'] == 0:
                request_id = feed_ret['log_pb']['impr_id']
                aweme_id = feed_ret['aweme_list'][0]['aweme_id']
                music_id = feed_ret['aweme_list'][0]['music']['mid']
                author_id = feed_ret['aweme_list'][0]['author']['uid']
                self.tracker.set_requestid(request_id)
                logger.info("feed request id: {}".format(request_id))
            else:
                aweme_id = ''
                music_id = ''
                author_id = ''
        except:
            logger.error("app_start启动，调用feed接口出错")

        # 第二次调用
        self.get(host="aweme.snssdk.com", path="/aweme/v2/activity/evening/info/")

        self.get(host="aweme.snssdk.com", path="/aweme/v1/check/in/")

        # 第二次调用 rate/settings
        self.get(host='aweme.snssdk.com', path='/aweme/v1/rate/settings/')

        self.get(host='aweme.snssdk.com', path='/aweme/v1/app/promotion/item/')

        self.get(host='lf.snssdk.com', path='/service/2/app_alert/')

        self.get(host="aweme.snssdk.com", path="/aweme/v1/im/resources/", params={"resource_type": "STICKER"})

        self.get(host='aweme.snssdk.com', path='/aweme/v1/theme/package/')

        self.get(host="lf.snssdk.com", path="/feedback/2/list/", params={"appkey": "aweme-ios", "count": 100})

        self.get(host="ib.snssdk.com", path="/user/privacy_mobile/v1/control_auth/", params={
            "carrier": self.get_isp()
        })

        # TODO ... POST     location/sulite
        # TODO ... POST     location/sulite
        # TODO ... POST     location/sulite
        # data = self.get_common_params()
        # data["dwinfo"] = ""
        # self.post(host="lf.snssdk.com", path="/location/sulite/", postParams=data)

        self.get(host="effect.snssdk.com", path="/effect/api/v3/effects", params={
            "sdk_version": APPINFO["version_code"],
            "language": "zh",
            "region": "CN",
            "panel": "colorfilterexperiment",
            "app_language": "zh",
            "access_key": "142710f02c3a11e8b42429f14557854a"
        }, headers=aweme_header_2, sign=False)

        self.orig_post(url="https://gecko.snssdk.com/gecko/server/device/checkin", data={
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'device_id': self.device.device_id
        }, headers=aweme_header_2, verify=False)

        # 第一次调用
        self.orig_get('https://gecko.snssdk.com/gecko/server/package', params={
            'app_version': APPINFO['app_version'],
            'os': 'ios',
            'channel': 'wallet,douyin_falcon,falcon_dyfe',
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'package_version': '0,0,0,0',
            'device_id': self.device.device_id
        }, headers=aweme_header_2)

        # 第二次调用
        self.orig_get('https://gecko.snssdk.com/gecko/server/package', params={
            'app_version': APPINFO['app_version'],
            'channel': 'rn_base_ios,rn_patch_ios',
            'os': 'ios',
            'access_key': '2373bbcf94c1b893dad48961d0a2d086',
            'package_version': '0,0',
            'device_id': self.device.device_id
        }, headers=aweme_header_2)

        # todo ... xlog    v2/r
        # todo ... xlog    v2/r
        # todo ... xlog    v2/r

        self.app_log()

        self.get(host="mon.snssdk.com", path="/monitor/appmonitor/v2/settings", params={
            "language": "zh-Hans",
            "user_agent": "Aweme {} rv:{} (iPhone; iPhone OS {}; zh_CN)".format(APPINFO["app_version"],
                                                                                APPINFO["build_number"],
                                                                                self.device.os_version),
            "vendor_id": self.device.vid,
            "resolution": "{}*{}".format(self.device.screen_width, self.device.screen_height),
            "os": "iOS",
            "encrypt": "close",
            "access": "wifi",
            "update_version_code": APPINFO["build_number"],
            "timezone": 8,
            "is_jailbroken": 0,
            "display_name": "抖音短视频",
            "package": "com.ss.iphone.ugc.Aweme",
            "appkey": APPINFO["aid"],
            "device_model": "iPhone X"
        })

        # self.app_xlog(scene="install")
        self.app_xlog(scene="cold_start")

        logger.debug("app_start faker_startlog_next")
        self.tracker.faker_startlog_next(aweme_id, music_id)
        logger.debug("app_start app_log")
        self.app_log()
        logger.debug("app_start  结束")
    """

    def device_register(self, url=None, headers=None):
        # """
        # info = {
        #     "magic_tag":"ss_app_log",
        #     "fingerprint":"",
        #     "header":{
        #         "sdk_version":1132,
        #         "language":"zh",
        #         "user_agent":"Aweme {} rv:{} (iPhone; iOS {}; zh_CN)".format(APPINFO['app_version'], APPINFO['build_number'], self.device.os_version),
        #         "app_name": APPINFO["app_name"],
        #         "app_version": APPINFO['app_version'],
        #         "vendor_id": self.device.vid,
        #         "is_upgrade_user":True,
        #         "region":"CN",
        #         "channel":APPINFO['channel'],
        #         "mcc_mnc":"46001",
        #         "tz_offset":28800,
        #         "app_region":"CN",
        #         "resolution": "{}*{}".format(self.device.screen_width, self.device.screen_height),
        #         "aid": APPINFO['aid'],
        #         "os":"iOS",
        #         "custom":{
        #             "earphone_status":"off",
        #             "app_language":"zh",
        #             "app_region":"CN",
        #             "build_number": APPINFO['build_number']
        #         },
        #         "access": APPINFO['ac'],
        #         "openudid": self.device.openudid,
        #         "carrier":"中国联通",
        #         "timezone":8,
        #         "is_jailbroken":False,
        #         "device_model": self.device.device_model,
        #         "os_version": self.device.os_version,
        #         "mc":"02:00:00:00:00:00",
        #         "display_name":"抖音短视频",
        #         "package":"com.ss.iphone.ugc.Aweme",
        #         "tz_name":"Asia/Shanghai",
        #         "app_language":"zh",
        #         "idfa": self.device.idfa
        #     }
        # }
        # info = '{"magic_tag":"ss_app_log","fingerprint":"","header":{"sdk_version":1132,"language":"zh","user_agent":"Aweme 6.7.0 rv:67016 (iPhone; iOS 10.2; zh_CN)","app_name":"aweme","app_version":"6.7.0","vendor_id":"{}","is_upgrade_user":false,"region":"CN","channel":"App Store","mcc_mnc":"","tz_offset":28800,"app_region":"CN","resolution":"750*1334","aid":"1128","os":"iOS","custom":{"earphone_status":"off","app_language":"zh","app_region":"CN","build_number":"67016"},"access":"WIFI","openudid":"16167598a605ce82cc4d261fc13606efe456f403","carrier":"\xe4\xb8\xad\xe5\x9b\xbd\xe8\x81\x94\xe9\x80\x9a","timezone":8,"is_jailbroken":false,"device_model":"iPhone 6S","os_version":"10.2","mc":"02:00:00:00:00:00","display_name":"\xe6\x8a\x96\xe9\x9f\xb3\xe7\x9f\xad\xe8\xa7\x86\xe9\xa2\x91","package":"com.ss.iphone.ugc.Aweme","tz_name":"Asia\\/Shanghai","app_language":"zh","idfa":"46637BF2-48BF-4B3E-9C7D-F9CB7A74827F"}}'
        # info = '{"magic_tag":"ss_app_log","fingerprint":"","header":{"sdk_version":1132,"language":"zh","user_agent":"Aweme 6.7.0 rv:67016 (iPhone; iOS 10.2; zh_CN) Cronet","app_name":"aweme","app_version":"6.7.0","vendor_id":{},"is_upgrade_user":false,"region":"CN","channel":"App Store","mcc_mnc":"","tz_offset":28800,"app_region":"CN","resolution":"750*1334","aid":"1128","os":"iOS","device_id":"68323161902","custom":{"earphone_status":"off","app_language":"zh","app_region":"CN","build_number":"67016"},"access":"WIFI","openudid":"d2dc80367fa853f8f3cf715eb0b13072e5c8931d","carrier":"\xe4\xb8\xad\xe5\x9b\xbd\xe8\x81\x94\xe9\x80\x9a","install_id":"75638142908","timezone":8,"is_jailbroken":false,"device_model":"iPhone 6S","os_version":"10.2","mc":"02:00:00:00:00:00","display_name":"\xe6\x8a\x96\xe9\x9f\xb3\xe7\x9f\xad\xe8\xa7\x86\xe9\xa2\x91","package":"com.ss.iphone.ugc.Aweme","tz_name":"Asia\\/Shanghai","app_language":"zh","idfa":"4AF08DC2-5495-4561-A9B8-AB221C901697"}}'
        openudid = self.device.openudid
        idfa = self.device.idfa
        info = '{"magic_tag":"ss_app_log","fingerprint":"","header":{"sdk_version":1132,"language":"zh","user_agent":"Aweme 6.7.0 rv:67016 (iPhone; iOS 10.2; zh_CN)","app_name":"aweme","app_version":"6.7.0","vendor_id":"{}","is_upgrade_user":false,"region":"CN","channel":"App Store","mcc_mnc":"","tz_offset":28800,"app_region":"CN","resolution":"750*1334","aid":"1128","os":"iOS","custom":{"earphone_status":"off","app_language":"zh","app_region":"CN","build_number":"67016"},"access":"WIFI","openudid":"%s","carrier":"\xe4\xb8\xad\xe5\x9b\xbd\xe8\x81\x94\xe9\x80\x9a","timezone":8,"is_jailbroken":false,"device_model":"iPhone 6S","os_version":"10.2","mc":"02:00:00:00:00:00","display_name":"\xe6\x8a\x96\xe9\x9f\xb3\xe7\x9f\xad\xe8\xa7\x86\xe9\xa2\x91","package":"com.ss.iphone.ugc.Aweme","tz_name":"Asia/Shanghai","app_language":"zh","idfa":"%s"}}' % (
        openudid, idfa
        )
        #print(info)
        data = utiles.encryptLogData(info)

        #print(url)
        #print(headers)
        #print(data)

        if not DEBUG:
            resp = self.orig_post(url, params=None, data=data, headers=headers, verify=False).json()
        else:
            resp = self.orig_post(url, params=None, data=data, headers=headers,
                                  proxies={"https": "127.0.0.1:8080"}, verify=False).json()
        logger.info(resp)
        self.device.install_id = resp['install_id']
        self.device.device_id = resp['device_id']
        self.device.new_user = resp['new_user']
        return

        # print(info)
        common_params = {
            "tt_data": "a",
            "device_id": "",
            "is_activated": "0",
            "aid": APPINFO['aid'],
            "screen_width": self.device.screen_width,
            "pass-route": "1",
            "pass-region": "1",
            "os_api": self.device.os_api,
            "app_name": APPINFO['app_name'],
            "channel": APPINFO['channel'],
            "idfa": self.device.idfa,
            "device_platform": self.device.device_platform,
            "build_number": APPINFO['build_number'],
            "vid": self.device.vid,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "app_version": APPINFO['app_version'],
            "js_sdk_version": APPINFO["js_sdk_version"],
            "version_code": APPINFO['version_code'],
            "ac": APPINFO['ac'],
            "os_version": self.device.os_version,
            "aid": "1128",
            "mcc_mnc": "46007"
        }
        if self.device.install_id != None and self.device.install_id != '':
            info['header']['device_id'] = self.device.device_id
            info['header']['install_id'] = self.device.install_id
            common_params['iid'] = self.device.install_id,
            common_params['device_id'] = self.device.device_id
        # data = gzip.compress(json.dumps(info).encode('utf-8'))
        data = utiles.encryptLogData(info)
        headers = utiles.get_aweme_headers(self.device.os_version).copy()
        # headers['Content-Type'] = "application/json; encoding=utf-8"
        headers['Content-Type'] = "application/octet-stream;tt-data=a"
        headers['Accept'] = "application/json"
        # headers['Content-Encoding'] = "gzip"
        headers['sdk-version'] = "1"
        headers['aid'] = "1128"

        query = ""
        for i in common_params.keys():
            query += "{}={}&".format(i, common_params[i])
        query = query.strip("&")
        url = "https://log.snssdk.com/service/2/device_register/?{}".format(query)

        if not DEBUG:
            resp = self.orig_post(url, params=None, data=data, headers=headers, verify=False).json()
        else:
            resp = self.orig_post(url, params=None, data=data, headers=headers,
                                  proxies={"https": "127.0.0.1:8080"}, verify=False).json()
        # """
        # resp = utiles.getDevice()
        # print(resp)
        self.device.install_id = resp['install_id']
        self.device.device_id = resp['device_id']
        # self.device.new_user = resp['new_user']
        # if resp['new_user'] == 1:
        #   self.app_xlog(scene="install")
        logger.debug(resp)

    def app_log(self, path="/service/2/app_log/", log_info=None):
        return
        if log_info == None:
            log_info = {
                "header": {
                    "timezone": 8,
                    "resolution": "{}*{}".format(self.device.screen_width, self.device.screen_height),
                    "is_upgrade_user": False,
                    "vendor_id": self.device.vid,
                    "region": "CN",
                    "carrier": "中国联通",
                    "is_jailbroken": False,
                    "app_name": "aweme",
                    "access": APPINFO['ac'],
                    "channel": APPINFO['channel'],
                    "openudid": self.device.openudid,
                    "tz_offset": 28800,
                    "tz_name": "Asia/Shanghai",
                    "app_language": "zh",
                    "aid": "1128",
                    "os": "iOS",
                    "app_region": "CN",
                    "install_id": self.device.install_id,
                    "custom": {
                        "app_language": "zh",
                        "build_number": APPINFO['build_number'],
                        "app_region": "CN"
                    },
                    "display_name": "抖音短视频",
                    "os_version": self.device.os_version,
                    "device_model": self.device.device_model,
                    "user_agent": "Aweme {} rv:{} (iPhone; iPhone OS {}; zh_CN)".format(APPINFO['app_version'],
                                                                                        APPINFO['build_number'],
                                                                                        self.device.os_version),
                    "app_version": APPINFO['app_version'],
                    "language": "zh",
                    "idfa": self.device.idfa,
                    "sdk_version": 111,
                    "mc": "02:00:00:00:00:00",
                    "package": "com.ss.iphone.ugc.Aweme",
                    "device_id": self.device.device_id,
                    "mcc_mnc": ""
                },
                "magic_tag": "ss_app_log",
                "fingerprint": "",
                "time_sync": {
                    "server_time": int(time.time()),
                    "local_time": int(time.time())
                }
            }
        if path == '/service/2/app_log/':
            log_info.update(self.tracker.get_event())

        common_params = {
            "iid": self.device.install_id,
            "idfa": self.device.idfa,
            "vid": self.device.vid,
            "device_id": self.device.device_id,
            "openudid": self.device.openudid,
            "device_type": self.device.device_type,
            "os_version": self.device.os_version,
            "os_api": self.device.os_api,
            "screen_width": self.device.screen_width,
            "device_platform": self.device.device_platform,
            "version_code": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            "app_name": APPINFO['app_name'],
            "build_number": APPINFO['build_number'],
            "app_version": APPINFO['app_version'],
            "aid": APPINFO['aid'],
            "ac": APPINFO['ac'],
            "pass-region": "1",
            # "js_sdk_version": "1.3.0.1"
            "tt_data": "a"
        }
        # data = gzip.compress(json.dumps(log_info).encode('utf-8'))
        data = utiles.encryptLogData(log_info)
        headers = utiles.get_aweme_headers(self.device.os_version).copy()
        # headers['Content-Type'] = "application/json; encoding=utf-8"
        headers['Content-Type'] = "application/octet-stream;tt-data=a"
        headers['Accept'] = "application/json"
        # headers['Content-Encoding'] = "gzip"
        if not DEBUG:
            self.orig_post("https://log.snssdk.com" + path, params=common_params, data=data, headers=headers,
                           verify=False)
        else:
            self.orig_post("https://log.snssdk.com" + path, params=common_params, data=data, headers=headers,
                           proxies={"https": "127.0.0.1:8080"}, verify=False)

    def replace_xlog(self, rstr):
        ORIG_IDFA = "06E5F3B1-0535-4097-B801-DD87EFF18C01"
        ORIG_VID = "F50BD7DD-40A1-43E4-988A-1BCAD2579101"
        ORIG_UDID = "47c4a697b78935ffae919fe44b648456f8f64688"
        ORIG_IID = "75953563126"
        ORIG_DID = "68352625710"
        ORIG_OSVERSION = "10.2"
        ORIG_DEVICE_TYPE = "iPhone8,1"
        ORIG_DEVICE_MODEL = "iPhone 6S"
        ORIG_DISPLAY = "750,1334"
        ORIG_sdused = "13373538304"
        ORIG_sid = "203b63b5e9b797265446565f4c18e341"
        ORIG_sdtotal = "27498905600"
        ORIG_wifiip = "192.168.109.5"
        ORIG_network = "WIFI"
        ORIG_first = "1560952527"
        ORIG_brand = "iPhone 6s"
        ORIG_wifibssid = "a4:56:17:d5:1f:98"
        ORIG_mem = "2102919168"
        ORIG_active = "1560520509.485043"
        ORIG_timea = "1515988865"
        ORIG_timem = "1480990540"
        ORIG_timec = "1481007199"
        ORIG_timeb = "1480990540"
        ORIG_homeuuid = "2FD4A66B-C39D-478A-BD90-7A2C625B9CD4"
        ORIG_mn = "Xiulan Liao's iPhone"
        ORIG_dns = "192.168.109.1"
        ORIG_wifissid = "vtian"
        ORIG_timestamp = "0260c624b864c6c02faa75cda66a811f416ac4488bdce5db89f0cc0070|0217d47b6a42fc0f8cfb011e24ce80d56ac772d9b90579b0afd08b0170|"

        rstr = re.sub(ORIG_IDFA, self.device.idfa, rstr)
        #print("替换IDFA: {} -> {}".format(ORIG_IDFA, self.device.idfa))

        rstr = re.sub(ORIG_VID, self.device.vid, rstr)
        #print("替换VID: {} -> {}".format(ORIG_VID, self.device.vid))

        rstr = re.sub(ORIG_UDID, self.device.openudid, rstr)
        #print("替换UDID: {} -> {}".format(ORIG_UDID, self.device.openudid))

        if self.device.device_id != None:
            rstr = re.sub(ORIG_IID, str(self.device.install_id), rstr)
            #print("替换IID: {} -> {}".format(ORIG_IID, self.device.install_id))

            rstr = re.sub(ORIG_DID, str(self.device.device_id), rstr)
            #print("替换DID: {} -> {}".format(ORIG_DID, self.device.device_id))

        time_now = time.time()

        rstr = re.sub(ORIG_first, str(int(time_now)), rstr)
        #print("替换frist: {} -> {}".format(ORIG_first, int(time_now)))

        rstr = re.sub(ORIG_homeuuid, str(self.device.get_expansion()['aweme_path']), rstr)
        #print("替换homeuuid: {} -> {}".format(ORIG_homeuuid, self.device.get_expansion()['aweme_path']))

        rstr = re.sub(ORIG_timestamp, str(""), rstr)
        #print("替换timestamp: {} -> {}".format(ORIG_timestamp, ""))

        rstr = re.sub(ORIG_sid, str(self.http.cookies.get("sessionid")), rstr)
        #print("替换sid: {} -> {}".format(ORIG_sid, self.http.cookies.get("sessionid")))

        rstr = re.sub(ORIG_sdused, str(self.device.get_expansion()['sdused']), rstr)
        #print("替换sdused: {} -> {}".format(ORIG_sdused, self.device.get_expansion()['sdused']))

        rstr = re.sub(ORIG_sdtotal, str(self.device.get_expansion()['sdtotal']), rstr)
        #print("替换sdtotal: {} -> {}".format(ORIG_sdtotal, self.device.get_expansion()['sdtotal']))

        rstr = re.sub(ORIG_wifiip, str(self.device.get_expansion()['wifiip']), rstr)
        #print("替换wifiip: {} -> {}".format(ORIG_wifiip, self.device.get_expansion()['wifiip']))


        rstr = re.sub(ORIG_wifibssid, str(self.device.get_expansion()['wifibssid']), rstr)
        #print("替换wifibssid: {} -> {}".format(ORIG_wifibssid, self.device.get_expansion()['wifibssid']))


        rstr = re.sub(ORIG_active, str(self.device.get_expansion()['system_start_time']), rstr)
        #print("替换active: {} -> {}".format(ORIG_active, self.device.get_expansion()['system_start_time']))


        rstr = re.sub(ORIG_dns, str(self.device.get_expansion()['dns']), rstr)
        #print("替换dns: {} -> {}".format(ORIG_dns, self.device.get_expansion()['dns']))


        rstr = re.sub(ORIG_wifissid, str(self.device.get_expansion()['wifissid']), rstr)
        #print("替换wifissid: {} -> {}".format(ORIG_wifissid, self.device.get_expansion()['wifissid']))


        REPL_timea = str(int(ORIG_timea) + random.randint(0, 5000))
        rstr = re.sub(ORIG_timea, str(REPL_timea), rstr)
        #print("替换timea: {} -> {}".format(ORIG_timea, REPL_timea))

        REPL_timem = str(int(ORIG_timem) + random.randint(0, 5000))
        rstr = re.sub(ORIG_timem, str(REPL_timem), rstr)
        #print("替换timem: {} -> {}".format(ORIG_timem, REPL_timem))

        REPL_timec = str(int(ORIG_timec) + random.randint(0, 5000))
        rstr = re.sub(ORIG_timec, str(REPL_timec), rstr)
        #print("替换timec: {} -> {}".format(ORIG_timec, REPL_timec))

        rstr = re.sub(ORIG_mn, str(self.device.get_expansion()['mn']), rstr)
        #print("替换mn: {} -> {}".format(ORIG_mn, self.device.get_expansion()['mn']))

        rstr = re.sub("\|\|02923c6977206be491e2aa43e22f753ba6eaa605e02558d18ac06b0174", "", rstr)

        return rstr

    def app_xlog(self, url=None, headers=None, data=None):
        #print(url)
        #print(headers)
        data = data.decode().split("=")[1]
        #print(data)
        xlog_str = utiles.decryptXlogData(data)
        #print(xlog_str)
        xlog_str = self.replace_xlog(xlog_str)
        #print(xlog_str)
        data = utiles.encryptXlogData(xlog_str)
        #print(data)

        if not DEBUG:
            resp = self.orig_post(url=url, data={"data": data['data']},
                                  headers=headers, verify=False)
        else:
            resp = self.orig_post(url=url, data={"data": data['data']},
                                  headers=headers,
                                  proxies={"https": "127.0.0.1:8080"}, verify=False)
        logger.debug("xlog resp: " + resp.text)
        return resp
        #logger.info("xlog scene: " + scene)
        # expansion = {
        #     "aweme_path": self.device.get_expansion()['aweme_path'],
        #     "skmc": self.device.get_expansion()['skmc'],
        #     "sch": self.device.get_expansion()['sch'],
        #     "stime": self.device.get_expansion()['stime']
        # }

        # if self.device.install_id == None:
        #     data = utiles.getXlogData(scene, "", "", idfv=self.device.vid, idfa=self.device.idfa, expansion=self.device.get_expansion())
        # else:
        #     if self.user != None and self.user.is_login == True:
        #         sid = self.http.cookies.get("sessionid")
        #     else:
        #         sid = ""
        #     data = utiles.getXlogData(scene, self.device.device_id, self.device.install_id, sid=sid, idfv=self.device.vid, idfa=self.device.idfa, expansion=self.device.get_expansion())

        ext_info = self.device.get_expansion()

        if self.device.install_id == None:
            data = utiles.genOrigXlog(scene=scene,
                                      install_id="",
                                      device_id="",
                                      # brand="iPhone XS",
                                      brand=self.device.device_model,
                                      os_version=self.device.os_version,
                                      ext_info=ext_info)
        else:
            if self.user != None and self.user.is_login == True:
                sid = self.http.cookies.get("sessionid")
            else:
                sid = ""
            data = utiles.genOrigXlog(scene=scene,
                                      install_id=self.device.install_id,
                                      device_id=self.device.device_id,
                                      # brand="iPhone XS",
                                      brand=self.device.device_model,
                                      os_version=self.device.os_version,
                                      session_id=sid,
                                      ext_info=ext_info)
        # print(json.dumps(data))
        data = utiles.encryptXlogData(data)

        query = {
            "os_ver": "iOS {}".format(self.device.os_version),
            "os": "1",
            "app_ver": APPINFO['version_code'],
            "channel": APPINFO['channel'],
            # "ver": "0.8.8.6-fix1",
            "var": APPINFO["xlog_ver"],
            "region": "CN",
            "m": "1",
            "aid": APPINFO['aid'],
            "did": self.device.device_id
        }
        if not DEBUG:
            try:
                resp = self.orig_post("https://xlog.snssdk.com/v2/r", params=query, data={"data": data['data']},
                                      headers=utiles.get_aweme_headers(self.device.os_version), verify=False)
            except:
                self.app_xlog(scene=scene)
        else:
            resp = self.orig_post("https://xlog.snssdk.com/v2/r", params=query, data={"data": data['data']},
                                  headers=utiles.get_aweme_headers(self.device.os_version),
                                  proxies={"https": "127.0.0.1:8080"}, verify=False)
        logger.debug("xlog resp: " + resp.text)
