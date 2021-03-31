#!/usr/bin/env python3
import json
import requests
import os
import time


def SendMessage(data):
    headers = {"Content-Type": "application/json;charset=utf-8"}
    ding_url = "https://oapi.dingtalk.com/robot/send?access_token=79ac4d6743c960c3e230b780f08863ef39214a6e61c0c2b3eba8dda50c59f5a3"
    r = requests.post(ding_url, data=json.dumps(data), headers=headers)


def Start_Market(bit_name):
    count = 1
    while True:
        huobi_url = "https://api.huobi.pro/market/history/kline?symbol={}usdt&period={}min&size={}".format(
            bit_name, 1, 1
        )
        req = requests.get(url=huobi_url)
        data = json.loads(req.text)
        if count <= 3:
            data = json.loads(req.text)
            count += 1
        if len(data["data"]):
            break
        else:
            time.sleep(30)
    res = {"msgtype": "text", "text": {"content": "{} is online".format(bit_name)}}
    SendMessage(res)


def CheckNewBits():
    huobi_url = "https://api.huobi.pro/v1/common/symbols"
    req = requests.get(url=huobi_url)
    data = json.loads(req.text)
    bitlist, newlist = list(), list()
    for k in data["data"]:
        if "usdt" in k["symbol"]:
            bitlist.append((k["symbol"].replace("usdt", "")))
    bitlist.append("11")
    bitlist.sort()

    recode = "/tmp/bts.log"
    if not os.path.isfile(recode):
        os.mknod(recode)
    with open(recode, "r") as f:
        old = f.readlines()
        if len(old):
            old = json.loads(old[0])
    for i in bitlist:
        if i not in old:
            old.append(i)
            data = {"msgtype": "text", "text": {"content": "new bits: {}".format(i)}}
            SendMessage(data)
            Start_Market(i)

    with open(recode, "w+") as b:
        b.write(json.dumps(list(old)))


if __name__ == "__main__":
    CheckNewBits()