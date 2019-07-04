#!/usr/bin/env python3
"""
抖音日志类
生成抖音log.aweme.com中的event和eventV3
"""
import time
import uuid
import json

class TrackerService:
    """
    抖音行为日志
    一个用户一个行为日志类
    tea_event_index 从0开始递增，每次打开app重置为0
    在上下文发送log的时候，调用getEvent，获取伪造的event和eventV3事件
    """
    def __init__(self, appid="1128", channel="pp", app_name="aweme", umeng_key="57bfa29e67e58e2fb8000c6b", user_id=None, iid=None):
        """
        初始化日志服务类
        :param appid: 抖音appid
        :param channel: APP下载源
        :param app_name: app名字
        :param umeng_key: 友盟key
        :param user_id: 用户 user_id，之后可以调用set_userid设置
        :param iid: install_id
        """
        self.appid = appid
        self.channel = channel
        self.app_name = app_name
        self.umeng_key = umeng_key
        self.user_id = user_id
        self.request_id = ""

        self.iid = iid
        self.session_id = str(uuid.uuid4()).upper()
        self.event = []
        self.eventV3 = []
        self.tea_event_index = 0
        self.frist_get_event = True

    def set_userid(self, uid):
        """
        设置用户 userid
        :param uid: 用户 userid
        :return: null
        """
        self.user_id = uid

    def set_requestid(self, rid):
        """
        设置请求logid
        一般情况下request为上一次feed的日志id
        :param rid: request_id
        :return: null
        """
        self.request_id = rid

    def get_event(self):
        """
        获取当前所有的事件
        获取之后，清空当前所有事件
        :return: dict, key: event, eventV3
        """
        #return {}
        ret = {
            'event': self.event.copy(),
            #'eventV3': self.eventV3.copy()
        }
        if self.frist_get_event:
            ret['launch'] = [
                {
                    "session_id": self.session_id,
                    "is_background":False,
                    "local_time_ms": int(time.time()*1000),
                    "tea_event_index":0,
                    "datetime":time.strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
            self.frist_get_event = False
        self.event.clear()
        self.eventV3.clear()
        return ret

    def track_event_attributes(self, event, attributes=""):
        #self._eventData()
        pass

    def track_event_label_value_extra_attributes(self, event, label, value="", extra="", attributes={}):
        """
        记录event日志
        :param event:
        :param label:
        :param value:
        :param extra:
        :param attributes:
        :return:
        """
        event_data = {
            'category': 'umeng',
            'label': label,
            'tag': event,
        }
        if value:
            event_data['value'] = str(value)
        for attr in attributes.keys():
            event_data[attr] = attributes[attr]

        self._event_data(event_data)

    def track_event_params(self, event, params, applog_only=1):
        """
        生成event日志
        :param event:
        :param params:
        :param applog_only:
        :return:
        """
        params['_staging_flag'] = 1
        data_event = {
            'event': event,
            'params': params
        }
        self.broadcast_event_data(data_event)

    def track_event_params_applogonly(self, event, params, applog_only):
        """
        暂时还没有用到
        :param event:
        :param params:
        :param applog_only:
        :return:
        """
        #return
        data_event = {
            'event': event,
            'params': params
        }
        self.broadcast_event_data(data_event)

    def track_event_params_needstagingflag(self, event, params, need_staging_flag):
        """
        生成event日志
        :param event:
        :param params:
        :param need_staging_flag:
        :return:
        """
        data_event = {
            'event': event,
            'params': params
        }
        self.broadcast_event_data(data_event)

    def _tea_event_index(self):
        """
        tea_event_index 日志索引，每次加一
        启动APP初始为0
        :return:
        """
        self.tea_event_index += 1
        return self.tea_event_index

    def _event_data(self, event_data):
        """
        生成event日志
        :param event_data:
        :return:
        """
        self.broadcast_event_data(event_data)

    def broadcast_event_data(self, event_data):
        """
        生成event日志
        :param event_data:
        :return:
        """
        if 'event' in event_data.keys():
            event_data['params']['tea_event_index'] = self._tea_event_index()
            event_data['params']['local_time_ms'] = str(int(time.time() * 1000))
            event_array = self.eventV3
        else:
            event_array = self.event
            event_data['tea_event_index'] = self._tea_event_index()
            event_data['local_time_ms'] = str(int(time.time() * 1000))
        event_data['user_id'] = self.user_id
        event_data['session_id'] = self.session_id
        event_data['datetime'] = time.strftime('%Y-%m-%d %H:%M:%S')
        event_data['nt'] = 4
        #print(event_data)

        event_array.append(event_data)

    def faker_startlog(self):
        """
        启动app发送的第一次日志
        :return:
        """
        self.track_event_label_value_extra_attributes("homepage", "click")
        self.track_event_label_value_extra_attributes("homepage", "show")
        self.track_event_label_value_extra_attributes("aweme_app_performance", "launch_time", attributes={
            'duration': '1834.276916742325'
        })

        self.track_event_params_needstagingflag("launch_log", {
            'enter_to': '',
            'is_cold_launch': 1,
            'launch_method': 'enter_launch',
            'red_badge_number': 0
        }, 0)

        self.track_event_label_value_extra_attributes("homepage_hot", "click")
        self.track_event_label_value_extra_attributes("homepage_hot", "show")
        self.track_event_label_value_extra_attributes("aweme_app_performance", "main_page_time", attributes={
            'duration': '2898.045958399773'
        })

        self.track_event_params_needstagingflag("location_status", {
            'is_open': 0
        }, 0)

    def faker_startlog_next(self, group_id, music_id):
        """
        启动app发送的第二次日志
        在发送feed之后，开始播放第一个视频
        :param group_id: 第一个视频的id
        :param music_id: 第一个视频的music id
        :return:
        """
        self.track_event_params('client_show', {
            'author_id': self.user_id,
            'category_id': '',
            'content': 'video',
            'display': 'full',
            'enter_from': 'homepage_hot',
            'group_id': group_id,
            'music_id': music_id,
            'request_id': self.request_id,
            'tag_id': '',
            'to_user_id': ''
        })

        self.track_event_label_value_extra_attributes('launch_app', 'enter_launch')

        self.track_event_label_value_extra_attributes('notice', 'allow_off')

        self.track_event_params_needstagingflag("follow_notice_show", {
            'notice_type': 'number_dot',
            'show_cnt': 1
        }, 0)

        self.track_event_label_value_extra_attributes('follow_notice_show', 'follow_bottom_tab', value=1, attributes={
            'notice_type': 'number_dot'
        })

        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display', attributes={
            'duration': '6636.285541653633',
            'playerType': 'AVPlayer'
        })

        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display_from_play', attributes={
            'duration': '6434.453833341599',
            'playerType': 'AVPlayer'
        })

        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time', attributes={
            'duration': '6938.710874915123',
            'playerType': 'AVPlayer',
            'enter_method': 'click'
        })

        self.track_event_params_needstagingflag('video_play', {
            'author_id': self.user_id,
            'country_name': 'CN',
            'enter_from': 'homepage_hot',
            "feed_count": 22,
            'group_id': group_id,
            'log_pb': {
                'impr_id': self.request_id
            },
            'order': 0,
            'player_type': 'AVPlayer',
            'previous_page': 'homepage_hot',
            'request_id': self.request_id
        }, 1)

    def faker_digg_log(self, group_id, author_id, enter_from='homepage_hot'):
        """
        伪造视频点赞日志
        :param group_id: 视频的id
        :param author_id: 视频的作者 userid
        :param enter_from: 点赞源
        :return:
        """
        self.track_event_params_needstagingflag('video_play', {
            'author_id': author_id,
            'city_info': '',
            'country_name': 'CN',
            'enter_from': enter_from,
            "feed_count": 22,
            'group_id': group_id,
            'log_pb': {
                'impr_id': self.request_id
            },
            'poi_id': '',
            'poi_type': '',
            'request_id': self.request_id,
            'to_user_id': author_id
        }, 1)

    def faker_follow_log(self, group_id, author_id, enter_from='token_link'):
        """
        伪造关注用户日志
        :param group_id: 当前用户id
        :param author_id: 给谁点赞
        :param enter_from:
        :return:
        """
        self.track_event_params_applogonly("follow", {
            'author_id': author_id,
            'country_name': 'CN',
            'enter_from': enter_from,
            'enter_method': 'follow_button',
            'group_id': group_id,
            'log_pb': {
                'impr_id': self.request_id
            },
            'previous_page': '',
            'previous_page_position': '',
            'request_id': self.request_id,
            'to_user_id': author_id
        }, 0)

    def faker_video_play_finish(self, group_id, author_id, enter_from='token_link'):
        """
        伪造视频播放完毕日志
        :param group_id: 视频id
        :param author_id: 视频作者id
        :param enter_from:
        :return:
        """
        self.track_event_params_needstagingflag("video_play_finish", {
            'author_id': author_id,
            'city_info': '',
            'country_name': 'CN',
            'distance_info': '',
            'enter_from': enter_from,
            'group_id': group_id,
            'is_photo': 0,
            'log_pb': {
                'impr_id': self.request_id
            },
            'player_type': 'AVPlayer',
            'poi_id': '',
            'poi_type': '',
            'request_id': self.request_id
        }, 1)

    def faker_scheme_to(self):
        """
        伪造短链接跳转日志
        :return:
        """
        self.track_event_params_needstagingflag("token_find", {
            'from_iid': self.iid,
            'from_user_id': self.user_id,
            'request_id': self.request_id,
            'token_form': 'link',
            'token_type': 'video'
        }, 0)
        self.track_event_label_value_extra_attributes('stay_time', 'homepage_hot', value=8620)
        self.track_event_params_needstagingflag('stay_time', {
            'duration': 8620,
            'enter_from': 'homepage_hot'
        }, 0)

    def faker_play_video(self, author_id=None, group_id=None, logid=None):
        """
        伪造播放视频日志
        :param author_id: 视频作者id
        :param group_id: 视频id
        :param logid: 视频方法链接的logid
        :return:
        """
        self.track_event_params_needstagingflag('play_time', {
            'author_id': author_id,
            'city_info': '',
            'country_name': 'CN',
            'distance_info': 'type_1_3',
            'duration': 8620,
            'enter_from': 'homepage_hot',
            'group_id': group_id,
            'log_pb': {
                'impr_id': self.request_id
            },
            'poi_id': '',
            'poi_type': ''
        }, 1)
        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display', attributes={
            'duration': '6362.328208208084',
            'playerType': 'AVPlayer'
        })
        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display_from_play', attributes={
            'duration': '6110.902416825294',
            'playerType': 'AVPlayer'
        })
        self.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time', attributes={
            'duration': '6403.900874853134',
            'playerType': 'AVPlayer'
        })
        self.track_event_params_needstagingflag('video_play', {
            'account_type': '',
            'author_id': author_id,
            'country_name': '',
            'enter_from': 'token_link',
            'group_id': group_id,
            'log_pb': {
                'impr_id': logid
            },
            'previous_page': '',
            'request_id': self.request_id
        }, 1)

    def faker_comment_publish(self, author_id=None, aweme_id=None, text=None):
        self.track_event_label_value_extra_attributes('click', 'comment', value=aweme_id, attributes={
            "country_name": "CN",
            "enter_from": "homepage_hot",
            "enter_method": "click",
            "is_photo": 0,
            "request_id": self.request_id
        })

        self.track_event_params("click_comment_button", params={
            "author_id": author_id,
            "country_name": 'CN',
            "enter_from": "homepage_hot",
            "group_id": aweme_id,
            "log_pb": {
                "impr_id": self.request_id
            },
            "outter_comment_cnt": 2207,
            "page_type": "",
            "poi_id": "B0FFHNSP2J"
        })

        self.track_event_params("keyboard_open", params={
            "comment_cnt": "2219",
            "keyboard_open": 0
        })

        self.track_event_params_needstagingflag("input_word_cut", params={
            "enter_from": "comment",
            "input_content": text,
            "input_content_cut": [c for c in text]
        }, need_staging_flag=0)

        self.track_event_label_value_extra_attributes("comment", "homepage_hot", label=aweme_id, attributes={
            "author_id": author_id,
            "city_info": "",
            "comment_category": "original",
            "country_name": "CN",
            "distance_info": "type_1_3",
            "emoji_times": 0,
            "enter_from": "homepage_hot",
            "enter_method": "click",
            "group_id": aweme_id,
            "is_photo": 0,
            "page_type": "list",
            "poi_id": "B0FFHNSP2J",
            "poi_type": 100000,
            "reply_comment_id": "",
            "reply_uid": "",
            "request_id": self.request_id
        })

        self.track_event_params_needstagingflag("post_comment", {
            "author_id": author_id,
            "comment_category": "original",
            "country_name": "CN",
            "emoji_times": 10,
            "enter_from": "homepage_hot",
            "group_id": aweme_id,
            "log_pb": {
                "impr_id": self.request_id
            },
            "page_type": "list",
            "poi_id": "B0FFHNSP2J",
            "poi_type": 100000,
            "reply_comment_id": "",
            "reply_uid": "",
            "request_id": self.request_id
        }, 1)

        self.track_event_label_value_extra_attributes("comment_duration", "homepage_hot", value=aweme_id, attributes={
            "duration": "22549.81716667116"
        })

        self.track_event_label_value_extra_attributes("close_comment", "click_button")
        self.track_event_params("close_comment", {
            "author_id": author_id,
            "country_name": "CN",
            "duration": 43381,
            "enter_from": "homepage_hot",
            "group_id": aweme_id,
            "page_type": "",
            "poi_id": "B0FFHNSP2J"
        }, 0)



if __name__ == '__main__':
    tracker = TrackerService(user_id="11111111")

    tracker.track_event_label_value_extra_attributes("homepage", "click")
    tracker.track_event_label_value_extra_attributes("homepage", "show")
    tracker.track_event_label_value_extra_attributes("aweme_app_performance", "launch_time", attributes={
        'duration': '1834.276916742325'
    })

    tracker.track_event_params_needstagingflag("launch_log", {
        'enter_to': '',
        'is_cold_launch': 1,
        'launch_method': 'enter_launch',
        'red_badge_number': 0
    }, 0)

    tracker.track_event_label_value_extra_attributes("homepage_hot", "click")
    tracker.track_event_label_value_extra_attributes("homepage_hot", "show")
    tracker.track_event_label_value_extra_attributes("aweme_app_performance", "main_page_time", attributes={
        'duration': '2898.045958399773'
    })

    tracker.track_event_params_needstagingflag("location_status", {
        'is_open': 0
    }, 0)

    # 上传一次 Log

    tracker.track_event_params('client_show', {
        'author_id': tracker.user_id,
        'category_id': '',
        'content': 'video',
        'display': 'full',
        'enter_from': 'homepage_hot',
        'group_id': '6613532961339870467',
        'music_id': '6566914167545006855',
        'request_id': '20181018214245010012020131019DEA',
        'tag_id': '',
        'to_user_id': ''
    })

    tracker.track_event_label_value_extra_attributes('launch_app', 'enter_launch')

    tracker.track_event_label_value_extra_attributes('notice', 'allow_off')

    tracker.track_event_params_needstagingflag("follow_notice_show", {
        'notice_type': 'number_dot',
        'show_cnt': 1
    }, 0)

    tracker.track_event_label_value_extra_attributes('follow_notice_show', 'follow_bottom_tab', value=1, attributes={
        'notice_type': 'number_dot'
    })

    tracker.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display', attributes={
        'duration': '6636.285541653633',
        'playerType': 'AVPlayer'
    })

    tracker.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time_display_from_play', attributes={
        'duration': '6434.453833341599',
        'playerType': 'AVPlayer'
    })

    tracker.track_event_label_value_extra_attributes('aweme_movie_play', 'prepare_time', attributes={
        'duration': '6938.710874915123',
        'playerType': 'AVPlayer',
        'enter_method': 'click'
    })

    # tracker.trackEventLabelValueExtraAttributes('video_play', 'homepage_hot', value="666666666666666", attributes={
    #     'author_id': tracker.user_id,
    #     'country_name': 'CN',
    #     'enter_from': 'homepage_hot',
    #     'enter_method': 'click',
    #     'feed_count': 1,
    #     'order': 0,
    #     'player_type': 'AVPlayer',
    #     'request_id': '20181018214245010012020131019DEA'
    # })
    tracker.track_event_params_needstagingflag('video_play', {
        'author_id': tracker.user_id,
        'country_name': 'CN',
        'enter_from': 'homepage_hot',
        "feed_count": 22,
        'group_id': '66666666666',
        'log_pb': {
            'impr_id': '20181019222416010015077160391AF8'
        },
        'order': 0,
        'player_type': 'AVPlayer',
        'previous_page': 'homepage_hot',
        'request_id': '20181019222416010015077160391AF8'
    }, 1)


    ret = {
        'event': tracker.event,
        'eventV3': tracker.eventV3
    }
    print(json.dumps(ret))
    print(tracker.get_event())

    ret = {
        'event': tracker.event,
        'eventV3': tracker.eventV3
    }
    print(json.dumps(ret))
