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
apiUrl = "http://piping.mogumiao.com/proxy/api/get_ip_al?appKey=413d4c34e6ef45f197e052a66300b7fc&count=2&expiryDate=0&format=1&newLine=2"
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
                try:
                    req = json.loads(requests.get(apiUrl).text)["msg"]
                    for msg in req:
                        ips.append(msg['ip']+':'+msg['port'])
                except:
                    ip_lock.release()
                    return self.getIP()
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

    def getOne(self, proxyip, movieID):
        global ips
        try:
            print(self.number, self.actor['id'], movieID, "ip remain:", len(ips))
            targetUrl = MOVIE + movieID
            req = requests.get(url=targetUrl, proxies={"http" : 'http://' + proxyip, "https" : 'https://' + proxyip}, verify=False, timeout=10)
            time.sleep(3)
            if req.status_code == 200:
                ret = json.loads(req.text)
                if ret['subtype'] != 'movie':
                    return True
                if int(ret['rating']['average']) == 0:
                    return True
                try:
                    need_ret = {
                        'rating': ret['rating'],
                        'genres': ret['genres'],
                        'title': ret['title'],
                        'subtype': ret['subtype'],
                        'id': ret['id'],
                        'year': int(ret['year'])
                    }
                except Exception:
                    return True
                self.movies.append(need_ret)
                return True
            else:
                if json.loads(req.text)["msg"] == "movie_not_found":
                    return True
            print(req.text)
            return False
        except Exception:
            print("FALSE thread", threading.current_thread().getName(), self.number, self.actor['id'], movieID, "ip remain:", len(ips))
            return False

    def getRes(self):
        # 开始计时
        start = time.time()

        actor = self.actor
        celeID = str(actor['id'])
        url = "https://movie.douban.com/celebrity/" + celeID + "/movies?start=0&format=text&sortby=time&"
        get_proxyip = self.getIP()
        try:
            req = requests.get(url=url, proxies={"http" : 'http://' + get_proxyip, "https" : 'https://' + get_proxyip}, verify=False, timeout=10)
            # req = requests.get(url)
        except Exception:
            self.removeIP(get_proxyip)
            raise Exception
        if req.status_code != 200:
            self.removeIP(get_proxyip)
            raise Exception
        Countregex = re.compile(r'<span class="count">\(共(.*?)条\)</span>')
        count = Countregex.findall(req.text)
        res_set = []
        regex = re.compile(r'<a href="https://movie.douban.com/subject/(.*?)"')
        result = regex.findall(req.text)
        for res in result:
            res = res[:-1] if res[-1] == '/' else res
            if res not in res_set:
                res_set.append(res)
        if len(count) > 0:
            for starter in range(25, int(count[0]), 25):
                url = "https://movie.douban.com/celebrity/" + celeID + "/movies?start=" + str(starter) + "&format=text&sortby=time&"
                try:
                    req = requests.get(url=url, proxies={"http" : 'http://' + get_proxyip, "https" : 'https://' + get_proxyip}, verify=False, timeout=10)
                    # req = requests.get(url)
                except Exception:
                    self.removeIP(get_proxyip)
                    raise Exception
                if req.status_code != 200:
                    self.removeIP(get_proxyip)
                    raise Exception
                regex = re.compile(r'<a href="https://movie.douban.com/subject/(.*?)"')
                result = regex.findall(req.text)
                for res in result:
                    res = res[:-1] if res[-1] == '/' else res
                    if res not in res_set:
                        res_set.append(res)
        self.movies = []
        for movieID in res_set:
            if len(self.movies) >= 5:
                break
            while True:
                proxyip = self.getIP()
                if self.getOne(proxyip, movieID) == True:
                    break
                else:
                    self.removeIP(proxyip)

        self.movies = sorted(self.movies, key=lambda i:i['year'], reverse=True)
        actor['works'] = []
        for i in range(min(len(self.movies), 5)):
            actor['works'].append(self.movies[i])
        with open("result/" + celeID + ".json", "w", encoding='utf-8') as f:
            json.dump(actor, f)

        # 结束计时
        end = time.time()
        # 输出内容
        print("线程完成", threading.current_thread().getName(), "编号", self.number, celeID, "ip remain:", len(ips))
        return True

    def run(self):
        while True:
            try:
                self.getRes()
                break
            except Exception:
                print("EXCEPTION, thread", threading.current_thread().getName(), self.number, "ip remain:", len(ips))


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
            # if number <= 3458:
                # continue
            if os.path.exists("result/" + str(actor['id']) + ".json"):
                continue
            print(number, actor['id'])
            CrawlThread(number, actor).start()
            time.sleep(self.fetchSecond)
            while threading.activeCount() > 5:
                time.sleep(10)

if __name__ == '__main__':
    if not os.path.exists("result/"):
        os.mkdir("result/")
    # 开始自动获取IP
    urllib3.disable_warnings()
    GetIpThread(fetchSecond).start()