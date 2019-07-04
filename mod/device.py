import json
from sqlalchemy import Column, String, Integer, VARCHAR, ForeignKey, Float, BOOLEAN, DateTime, VARBINARY
from sqlalchemy.orm import relationship,backref

from datetime import datetime
from libs.utils import *

"""
iPhone XS

iPhone11,2      D321AP
12.2            16E227
2436x1125

https://blog.csdn.net/a18339063397/article/details/81482073
"""
OSVERSION = "12.2" #""9.2"
import requests
class Device():
    """
    抖音设备Model
    """


    def iid(self):
        return self.install_id

    def did(self):
        return self.device_id

    def __init__(self):
        device_info = utiles.getDevice()
        self.openudid = device_info['openudid']
        self.idfa = device_info['idfa']
        self.vid = device_info['vid']
        self.install_id = device_info['install_id']
        self.device_id = device_info['device_id']
        self.device_type = device_info['device_type'] #"iPhone7,2" #
        self.device_model = device_info['device_model'] #"iPhone 6" #
        self.os_version = "10.2" # OSVERSION     #"12.2" #utiles.random_osversion() # device_info['os_version']
        self.os_api = device_info['os_api']
        self.screen_width = device_info['screen_width'] # "750" #
        self.screen_height = device_info['screen_height'] #"1334" #
        self.device_platform = 'iphone'
        self.install_id = None
        self.device_id = None
        resp = requests.get("http://ppp.elie.lol:6001/v1/new_device").json()["data"]
        self.expansion = json.dumps({
            "aweme_path": str(uuid.uuid4()).upper(),
            #"skmc": utiles.randomMAC(),
            #"sch": str(random.randint(3050109338, 3068109338)),
            #"stime": random.randint(1515508764, 1544954178),
            #"ntfadd": str(random.randint(3566551104, 3596551104)),
            "device_name": str(uuid.uuid4()).upper()[0:2],
            "wifi_mac": utiles.randomMAC().lower(),
            "wifi_name": "TP-LINK_{}".format(utiles.random_str(6).upper()),
            "dyuid": str(uuid.uuid4()).upper(),#"8C280345-0164-3B82-A228-224B23CA0E9F"
            "tt": random.randint(604800, 2592000),
            "hwm": device_info['hwm'],
            "system_start_time": time.time() - 60*60*24*3,

            "wifiip": resp['wifiip'],
            "dns": resp["dns"],
            "wifibssid": resp["wifibssid"],
            "wifissid": resp["wifissid"],
            "mn": resp["mn"],
            "sdtotal": resp["sdtotal"],
            "sdused": resp["sdused"],
        })

    def get_expansion(self):
        return json.loads(self.expansion)

    # def register(self):
    #     """设备注册"""
    #     if self.content == None:
    #         self.content = Content()
    #     self.content.device_register()