#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:chendarcy
@file:chatyuan_wechat.py
@time:2023/03/06
"""

import os
import re
import uuid
import time
import base64
import hashlib
import asyncio
import socketio
import threading
from typing import List
from datetime import datetime
from wechaty_puppet import FileBox, MessageType
from wechaty import Contact, Room, Wechaty, get_logger, Message

sio = socketio.Client(logger=True, engineio_logger=True)
lock = threading.Lock()
log = get_logger('RoomBot')

share_mem = {}
ans_wait_time = 480
reconnect_time = 1
inner_ans_1 = "这是我帮您作的画，请查收~"
inner_ans_2 = "抱歉，我没有理解您需要我做什么，请换个描述试试~"
inner_ans_3 = '欢迎加入群聊! @我开启我们的对话吧~'
inner_ans_4 = "抱歉呀，我暂时无法提供服务，具体原因如下：{}"

SERVER_URL = os.environ.get("SERVER_URL", "")
whitelist_room = os.environ.get("WHITELIST_ROOM", [])
whitelist_friend = os.environ.get("WHITELIST_FRIEND", [])
wechat_name = os.environ.get("WECHAT_NAME", "")
whitelist_room = whitelist_room.split("&&") if whitelist_room else whitelist_room
whitelist_friend = whitelist_friend.split("&&") if whitelist_friend else whitelist_friend

async def get_anwser(uniq_uuid):
    global share_mem
    intent, res_anw = -1, "None" # "None"为预置的标志位

    for _ in range(ans_wait_time):
      print(uniq_uuid)
      if uniq_uuid in share_mem:
          res_anw = share_mem[uniq_uuid]["msg"]
          intent = share_mem[uniq_uuid]["intent"]
          del share_mem[uniq_uuid]
          break
      else:
          await asyncio.sleep(1)
    return intent, res_anw

def code_md5(str):
    code = str.encode("utf-8")
    m = hashlib.md5()
    m.update(code)
    result = m.hexdigest()
    return result

def strip_emotion(msg_text):
    emotion_set = [
        "[微笑]", "[撇嘴]", "[色]", "[发呆]", "[得意]", "[流泪]", "[害羞]", "[闭嘴]", "[睡]", "[大哭]",
        "[尴尬]", "[发怒]", "[调皮]", "[呲牙]", "[惊讶]", "[难过]", "[囧]", "[抓狂]", "[吐]", "[偷笑]",
        "[愉快]", "[白眼]", "[傲慢]", "[困]", "[惊恐]", "[憨笑]", "[悠闲]", "[咒骂]", "[疑问]", "[嘘]",
        "[晕]", "[衰]", "[骷髅]", "[敲打]", "[再见]", "[擦汗]", "[抠鼻]", "[鼓掌]", "[坏笑]", "[右哼哼]",
        "[鄙视]", "[委屈]", "[快哭了]", "[阴险]", "[亲亲]", "[可怜]", "[笑脸]", "[生病]", "[脸红]", "[破涕为笑]",
        "[恐惧]", "[失望]", "[无语]", "[嘿哈]", "[捂脸]", "[奸笑]", "[机智]", "[皱眉]", "[耶]", "[吃瓜]",
        "[加油]", "[汗]", "[天啊]", "[Emm]", "[社会社会]", "[旺柴]", "[好的]", "[打脸]", "[哇]", "[翻白眼]",
        "[666]", "[让我看看]", "[叹气]", "[苦涩]", "[裂开]", "[嘴唇]", "[爱心]", "[心碎]", "[拥抱]", "[强]",
        "[弱]", "[握手]", "[胜利]", "[抱拳]", "[勾引]", "[拳头]", "[OK]", "[合十]", "[啤酒]", "[咖啡]",
        "[蛋糕]", "[玫瑰]", "[凋谢]", "[菜刀]", "[炸弹]", "[便便]", "[月亮]", "[太阳]", "[庆祝]", "[礼物]",
        "[红包]", "[發]", "[福]", "[烟花]", "[爆竹]", "[猪头]", "[跳跳]", "[发抖]", "[转圈]"
    ]
    for emotion in emotion_set:
        msg_text = msg_text.replace(emotion, '')
    res = re.compile(u'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]')
    msg_text = res.sub("", msg_text)
    return msg_text


class MyBot(Wechaty):
    def on_error(self, payload):
        log.info(str(payload))

    def on_logout(self, contact: Contact):
        log.info('Bot %s logouted' % contact.name)

    async def on_room_join(self, room: Room, invitees: List[Contact],
                           inviter: Contact, date: datetime):
        print('bot room id:', room.room_id)
        # topic = await room.topic()
        # await room.say(inner_ans_3)

    async def on_message(self, msg: Message):
        is_self_msg = msg.is_self()
        if is_self_msg:
            log.info('on_message: send by self, skip.')
            return
        
        msg_type = msg.type()
        if msg_type != MessageType.MESSAGE_TYPE_TEXT:
            log.info('on_message: non-text content, skip.')
            return

        talker = msg.talker()
        if not talker:
            log.info('on_message: there is no specific talker, skip.')
            return
        else:
            talker_contact_id = talker.contact_id
            if not talker.is_personal():
                log.info('on_message: non-personal request, skip.')
                return 
        
        uniq_uuid = str(uuid.uuid1())
        room = msg.room()
        if room:
            mention_self = await msg.mention_self()
            mention_text = msg.text()

            if (not mention_self) and (("@"+wechat_name+" ") not in mention_text) and (("@"+wechat_name+" ") not in mention_text):
                log.info('on_message: Have not @bot, skip.')
                return
            else:
                room_topic = await room.topic()
                if whitelist_room and (room_topic not in whitelist_room):
                    return 
                log.info(
                    'on_message: {} mentioned me, please response.'.format(room_topic))     

            try:
                mention_list = await msg.mention_list()
            except:
                mention_list = []
                log.info('on_message: can not get mention_list')     
            
            for j in range(len(mention_list)):
                mention_name = mention_list[j].name
                strip_word_1 = "@" + mention_name + " "
                strip_word_2 = "@" + mention_name + " "
                mention_text = mention_text.replace(strip_word_1, "").replace(strip_word_2, "")
            mention_text = mention_text.replace("@所有人 ", "").replace("@所有人 ", "")
            mention_text = mention_text.replace("@"+wechat_name+" ", "").replace("@"+wechat_name+" ", "")
            if not mention_list:
                regex = re.compile(r"@.*?[  ]")
                mention_text = regex.sub('', mention_text)
            msg_text_after = strip_emotion(mention_text)
            log.info(msg_text_after)
            if not msg_text_after:
                log.info('on_message: empty content after strip emotion, skip.')
                await room.ready()
                await room.say(inner_ans_2, [talker_contact_id])
                return

            # 请求
            send_msg(talker_contact_id, msg_text_after, uniq_uuid)
            intent, msg_text_response = await get_anwser(uniq_uuid)
            log.info(msg_text_response[:20])
            # 回复对话
            await room.ready()
            if msg_text_response and msg_text_response != "None":
                if intent in [0,3,4,5,6]: # -1:未识别 0:公文 1:绘画 2:对话 3:绝句 4:律诗 5:对联 6:宋词
                    msg_text_response = '\n' + msg_text_response
                await room.say(msg_text_response, [talker_contact_id])
                return
            elif msg_text_response == "None":
                await room.say(inner_ans_2, [talker_contact_id])
                return
            else:
                log.info('it is a painting respond.')
            # 回复图片
            file_name = './' + uniq_uuid + ".png"
            if os.path.exists(file_name):
                gen_image = FileBox.from_file(file_name, file_name)
                lock.acquire() # 上锁
                try:
                    await room.say(inner_ans_1, [talker_contact_id])
                    await room.ready()
                    await room.say(gen_image)
                    lock.release()  # 解锁
                except:
                    lock.release()  # 解锁
                # 删除图片
                os.remove(file_name)
            else:
                await room.say(inner_ans_2, [talker_contact_id])
            return 
        else:
            if whitelist_friend and (talker_contact_id not in whitelist_friend):
                return 
            msg_text = msg.text()
            msg_text_after = strip_emotion(msg_text)
            if not msg_text_after:
                log.info('on_message: empty content after strip emotion, skip.')
                await talker.ready()
                await talker.say(inner_ans_2)
                return 
            # 请求
            send_msg(talker_contact_id, msg_text_after, uniq_uuid)
            _, msg_text_response = await get_anwser(uniq_uuid)
            log.info(msg_text_response[:20])
            # 回复对话
            await talker.ready()
            if msg_text_response and msg_text_response != "None":
                await talker.say(msg_text_response)
                return
            elif msg_text_response == "None":
                await talker.say(inner_ans_2)
                return
            else:
                log.info('it is a painting respond.')
            # 回复图片 
            file_name = './' + uniq_uuid + ".png"
            if os.path.exists(file_name):
                gen_image = FileBox.from_file(file_name, file_name)
                await talker.say(gen_image)
                # 删除文件
                os.remove(file_name)
            else:
                await talker.say(inner_ans_2)
            return


@sio.event
def chatevent(data):
    global start_timer, share_mem
    latency = time.time() - start_timer
    print('latency is {0:.2f} ms'.format(latency * 1000))
    
    if not data["flag"]:
        quesId = data["resData"]['questionId'] if ("resData" in data) and (
            'questionId' in data["resData"]) else None
        res_msg_error = data["errMessage"] if "errMessage" in data else "Unknown"
        res_msg = inner_ans_4.format(res_msg_error)
        res_pic = None
        intent = -1
        print(res_msg)
    else:
        quesId = data["resData"]['questionId'] if ("resData" in data) and (
            'questionId' in data["resData"]) else None
        res_msg = data["resData"]['textInfo'] if ("resData" in data) and (
            'textInfo' in data["resData"]) else "Unknown"
        res_pic = data["resData"]['picInfo'] if (
            "resData" in data) and ('picInfo' in data["resData"]) else ""
        intent = data["resData"]['intent'] if ("resData" in data) and (
            'intent' in data["resData"]) else -1
        print(res_msg)

        if res_pic:
            file_name = quesId + '.png'
            res_pic = res_pic[22:]
            # if(len(res_pic) % 3 == 1):
            #     res_pic += "=="
            # elif(len(res_pic) % 3 == 2):
            #     res_pic += "="
            if len(res_pic) < 512:
                print("illegal image.(too small)")
            else:
                try:
                    img_body = base64.b64decode(res_pic)
                    with open(file_name, 'wb') as f:
                        f.write(img_body)
                except:
                    print("illegal image type.")
    if quesId:
        share_mem[quesId] = {}
        share_mem[quesId]["msg"] = res_msg
        share_mem[quesId]["intent"] = intent


@sio.event
def connect():
    print('connection established')

@sio.event
def connect_error(data):
    print("connection failed!")

@sio.event
def disconnect():
    global sio, connect, connect_error, disconnect, chatevent
    print('disconnected from server')
    try:
        time.sleep(reconnect_time)
        sio = socketio.Client(logger=True, engineio_logger=True)
        ws_connect()
        connect = sio.event(connect)
        connect_error = sio.event(connect_error)
        disconnect = sio.event(disconnect)
        chatevent = sio.event(chatevent)
    except:
        print("hooops, server refused your connection request.")


def send_msg(userId, message, quesId):
    global start_timer, sio
    start_timer = time.time()
    sio.emit('chatevent', {"userId": userId,
             "message": message, "questionId": quesId})


def ws_connect():
    inner_account = 'admin'
    date_time = datetime.now().strftime("%Y-%m-%d")  # Y-m-d H:M:S
    md5_token = code_md5(inner_account + date_time)
    ws_url = 'http://{SERVER_URL}/?token={md5_token}&account={inner_account}'.format(
        SERVER_URL=SERVER_URL,
        md5_token=md5_token,
        inner_account=inner_account)
    sio.connect(ws_url)


async def bot_start():
    bot = MyBot()
    await bot.start()


if __name__ == '__main__':
    #连接ws
    start_timer = time.time()
    ws_connect()

    # 测试请求
    time.sleep(1)
    # send_msg("wechat_send_test", "say something, anything is fine.", '9f34a6c0-a6a1-4dd4-8b7d-c96869b4484e')

    # 机器人启动监听
    asyncio.run(bot_start())
