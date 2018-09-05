# -*- coding: UTF-8 -*-

'''
Python 3.x
无忧代理IP Created on 2018年05月11日
描述：本DEMO演示了使用爬虫（动态）代理IP请求网页的过程，代码使用了多线程
逻辑：每隔5秒从API接口获取IP，对于每一个IP开启一个线程去抓取网页源码
@author: www.data5u.com
'''
import requests
import time
import threading
from requests.packages import urllib3
import json
import re
import os
import random

ips = []
ip_lock = threading.Lock()

MOVIE = "http://api.douban.com/v2/movie/subject/"
with open("add_actors.json", encoding="utf-8") as f:
    actors = json.load(f)

order = "bcb7a843b004ebd1e5641ac070d34da8"
# apiUrl = "http://dynamic.goubanjia.com/dynamic/get/" + order + ".html?sep=3&random=true"
apiUrl = "http://piping.mogumiao.com/proxy/api/get_ip_al?appKey=413d4c34e6ef45f197e052a66300b7fc&count=1&expiryDate=0&format=1&newLine=2"
fetchSecond = 5



# 爬数据的线程类
class CrawlThread(threading.Thread):
    def __init__(self, number, actor):
        super(CrawlThread, self).__init__()
        self.number = number
        self.actor = actor
        #消除关闭证书验证的警告
        urllib3.disable_warnings()

    def getIP(self):
        global ips, ip_lock
        if ip_lock.acquire():
            if len(ips) == 0:
                ips = []
                time.sleep(5)
                req = json.loads(requests.get(apiUrl).text)["msg"]
                for msg in req:
                    ips.append(msg['ip']+':'+msg['port'])
            idx = random.randint(0, len(ips) - 1)
            ip = ips[idx]
            ip_lock.release()
            return ip

    def removeIP(self, ip):
        global ips, ip_lock
        if ip_lock.acquire():
            if ip in ips:
                ips.remove(ip)
            ip_lock.release()

    def getRes(self, get_proxyip):
        # 开始计时
        start = time.time()

        actor = self.actor
        celeID = str(actor['id'])
        url = "https://movie.douban.com/celebrity/" + celeID + "/movies?start=0&format=text&sortby=time&"
        try:
            req = requests.get(url=url, proxies={"http" : 'http://' + get_proxyip, "https" : 'https://' + get_proxyip}, verify=False, timeout=10)
            # req = requests.get(url)
        except Exception:
            raise Exception
        if req.status_code != 200:
            raise Exception
        Countregex = re.compile(r'<span class="count">\(共(.*?)条\)</span>')
        count = Countregex.findall(req.text)
        regex = re.compile(r'<td headers="mc_date">(.*?)</td>')
        result = regex.findall(req.text)
        years = []
        for r in result:
            if r != '' and r != '(Sou':
                years.append(int(r))
        if len(count) > 0:
            end = ((int(count[0]) - 1) // 25) * 25
            url = "https://movie.douban.com/celebrity/" + celeID + "/movies?start=" + str(end) + "&format=text&sortby=time&"
            try:
                req = requests.get(url=url, proxies={"http" : 'http://' + get_proxyip, "https" : 'https://' + get_proxyip}, verify=False, timeout=10)
                # req = requests.get(url)
            except Exception:
                raise Exception
            if req.status_code != 200:
                raise Exception
            regex = re.compile(r'<td headers="mc_date">(.*?)</td>')
            result = regex.findall(req.text)
            for r in result:
                if r != '' and r != '(Sou':
                    years.append(int(r))
        if len(years) == 0:
            year = {
                "firstYear": 0
            }
            with open("year/" + celeID + ".json", "w", encoding='utf-8') as f:
                json.dump(year, f)
            return True
        years = sorted(years)
        year = {
            "firstYear": years[0]
        }
        with open("year/" + celeID + ".json", "w", encoding='utf-8') as f:
            json.dump(year, f)

        # 结束计时
        end = time.time()
        # 输出内容
        print("线程完成", threading.current_thread().getName(), "编号", self.number, celeID)
        return True

    def run(self):
        while True:
            # try:
            get_proxyip = self.getIP()
            self.getRes(get_proxyip)
            break
            # except Exception:
                # self.removeIP(get_proxyip)
                # print("EXCEPTION, thread", threading.current_thread().getName(), self.number)


# 获取代理IP的线程类
class GetIpThread(threading.Thread):
    def __init__(self,fetchSecond):
        super(GetIpThread, self).__init__()
        self.fetchSecond=fetchSecond
    def run(self):
        global ips
        # actors.reverse()
        for number, actor in enumerate(actors):
            # number = len(actors) - number
            # if number <= 4600:
                # continue
            if os.path.exists("year/" + str(actor['id']) + ".json"):
                continue
            print(number, actor['id'])
            CrawlThread(number, actor).start()
            while threading.activeCount() > 5:
                time.sleep(10)

if __name__ == '__main__':
    if not os.path.exists("year/"):
        os.mkdir("year/")
    # 开始自动获取IP
    urllib3.disable_warnings()
    GetIpThread(fetchSecond).start()