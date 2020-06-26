# -*- coding: utf-8 -*-

import os
import sys
import time
import json
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import requests
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
import html5lib
import base64

from inspect import isfunction

from utils.downloader import downloader
from utils.historyRecorder import Recorder

def getPage(header, url):
    if header:
        page = requests.get(url,headers = header)
    else:
        page = requests.get(url)
    page.encoding = UnicodeDammit(page.content).original_encoding
    pageSoup = BeautifulSoup(page.content,'html5lib')
    return pageSoup

def getResourceURL(setting, pageSoup):
    s = pageSoup
    returns = list()
    # 按照search列表顺序依次搜索
    for i, search_key in enumerate(setting["search"]):
        if type(search_key)==type(dict()):
            if "children" in search_key:
                s = s.contents[search_key["children"]]
        elif search_key[0]=='#':
            s = s.find_all(id=search_key[1:])
        elif search_key[0]=='.':
            s = s.find_all(class_=search_key[1:])
        else:
            s = s.find_all(search_key)
        # 列表最后一项为多结果搜索，其余为单结果搜索
        if i != len(setting["search"])-1:
            s = s[0]
    if not len(setting["search"]): s = [s]# 循环保证（元素=>列表）的转换，若不执行for，需保证传递结果仍为列表
    
    # tag列表对每一个search结果进行处理
    for t in s:
        for target_key in setting["target"]:
            if type(target_key)==type(dict()):
                 if "children" in target_key:
                    t = t.contents[target_key["children"]]
            elif target_key[0]=='#':
                t = t.find(id=target_key[1:])
            elif target_key[0]=='.':
                t = t.find(class_=target_key[1:])
            elif target_key[0]=='[' and target_key[-1]==']':
                t = t[target_key[1:-1]]
            else:
                t = t.find(target_key)
        t = str(t)
        for process_key in setting["process"]:
            if "replace" in process_key:
                for key,value in process_key["replace"].items():
                    t = t.replace(key,value)
            elif process_key[0]=="split":
                pass # TODO: 添加split处理
        returns.append(t)
    return returns

def getInfo(setting, pageSoup):
    returns = dict()
    for name,subsetting in setting.items():
        returns[name]=list()
        s = pageSoup
        # 按照search列表顺序依次搜索
        for i, search_key in enumerate(subsetting["search"]):
            if type(search_key)==type(dict()):
                if "children" in search_key:
                    s = s.contents[search_key["children"]]
            elif search_key[0]=='#':
                s = s.find_all(id=search_key[1:])
            elif search_key[0]=='.':
                s = s.find_all(class_=search_key[1:])
            else:
                s = s.find_all(search_key)
            # 列表最后一项为多结果搜索，其余为单结果搜索
            if i != len(subsetting["search"])-1:
                s = s[0]
        if not len(subsetting["search"]): s = [s]# 循环保证（元素=>列表）的转换，若不执行for，需保证传递结果仍为列表

        # tag列表对每一个search结果进行处理
        for t in s:
            for target_key in subsetting["target"]:
                if type(target_key)==type(dict()):
                    if "children" in target_key:
                        t = t.contents[target_key["children"]]
                elif target_key[0]=='#':
                    t = t.find(id=target_key[1:])
                elif target_key[0]=='.':
                    t = t.find(class_=target_key[1:])
                elif target_key[0]=='[' and target_key[-1]==']':
                    t = t[target_key[1:-1]]
                else:
                    t = t.find(target_key)
            t = str(t)
            for process_key in subsetting["process"]:
                if "replace" in process_key:
                    for key,value in process_key["replace"].items():
                        t = t.replace(key,value)
                elif process_key[0]=="split":
                    pass # TODO: 添加split处理
            returns[name].append(t)
    return returns

def start(settings, pageDict):
    skipURL = list()
    for subfoldername in pageDict.keys():
        if subfoldername=="None":
            subfolderpath= settings['saveRootFolder']
        else:
            subfolderpath = os.path.join(settings['saveRootFolder'],subfoldername)
        for url in pageDict[subfoldername]:
            # 爬取指定资源和信息
            pageSoup = getPage(settings["header"], url)
            resources = getResourceURL(settings["configure"]["resources"], pageSoup)
            infos = getInfo(settings["configure"]["info"], pageSoup)

            foldername = infos['title'][0].replace('\r\n','').replace('\n','').replace('>',')').replace('<','(').replace('?','？').replace(':','-')
            folderpath = os.path.join(subfolderpath,foldername)
            if not os.path.isdir(folderpath):
                os.makedirs(folderpath)
            elif os.path.isfile(os.path.join(folderpath,"information.json")):
                try:
                    with open(os.path.join(folderpath,"information.json"),'r',encoding="utf-8") as f:
                        existInfos = json.load(f)
                    if existInfos['url'] != url: # 对比url不一致则替换名称
                        print("While try to download resources from: {} to folder named: {} , "
                            "we find information.json file, and recognize this folder saved resources "
                            "which from different url. We decide to add number to the end of the foldername".format(url,foldername))
                        operate = "search full foldername"
                        for i in range(1,21): # 最多允许重名20个文件夹
                            if os.path.isdir(folderpath+"({})".format(i)):
                                try:
                                    with open(os.path.join(folderpath+"({})".format(i),"information.json"),'r',encoding="utf-8") as f:
                                        existInfos = json.load(f)
                                    if existInfos['url'] == url:
                                        skipURL.append(url)
                                        print("While try to download resources from: {} to folder named: {} , "
                                            "we find information.json file, and recognize this folder saved resources "
                                            "which from the same url. We decide to skip this url".format(url,foldername+"({})".format(i)))
                                        operate = "skip URL"
                                        break
                                except Exception as error:
                                    foldername = foldername+"({})".format(i)
                                    folderpath = folderpath+"({})".format(i)
                                    print("We find information.json in existed folder: {} "
                                        ", but this program cannot recognize the file. We "
                                        "will still download resources in the folder".format(folderpath+"({})".format(i)))
                                    if not os.path.isdir(folderpath):
                                        os.makedirs(folderpath)
                                    operate = "download"
                                    break
                            else:
                                foldername = foldername+"({})".format(i)
                                folderpath = folderpath+"({})".format(i)
                                if not os.path.isdir(folderpath):
                                    os.makedirs(folderpath)
                                operate = "download"
                                break
                        if operate == "search full foldername":
                            skipURL.append(url)
                            print("While try to download resources from: {} to folder named: {} , "
                                "we try 20 different foldernames, but still cannot decide final foldername. "
                                "Thus, we decide to skip this url".format(url,foldername))
                            continue
                        elif operate == "skip URL":
                            continue
                    else: # 对比url一致则跳过下载，并输出网址信息以便对比
                        skipURL.append(url)
                        print("While try to download resources from: {} to folder named: {} , "
                            "we find information.json file, and recognize this folder saved resources "
                            "which from the same url. We decide to skip this url".format(url,foldername))
                        continue
                except Exception as error:
                    print("We find information.json in existed folder: {} "
                        ", but this program cannot recognize the file. We "
                        "will still download resources in the folder".format(folderpath))

            # 每个末端文件夹均有一个json文件记录本文件夹爬取的相关信息：url、作者、标题、资源总数、标签、日期……
            infoRecord = dict()
            infoRecord['url'] = url
            for key,value in infos.items():
                infoRecord[key] = value
            infoRecord['number of resources'] = len(resources)
            infoRecord['date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(os.path.join(folderpath,'information.json'),'w',encoding='utf-8') as f:
                json.dump(infoRecord,f,ensure_ascii=False,indent=4)

            # =================================
            # =============下载文件=============
            for i,fileURL in enumerate(resources):
                ext = os.path.splitext(fileURL)[-1]
                filename = str(i)+ext
                downloader.submit((filename,fileURL),folderpath)
            # =================================

if __name__ == "__main__":
    sys.setrecursionlimit(5000)
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36 Edg/80.0.361.54'
        }
    with open("./config/jdlingyu.json",'r',encoding="utf-8") as f:
        configure = json.load(f)
    settings = {
        "saveRootFolder": "G:/待整理恢复/桌面文档/jdlyy",
        "historyFile": "G:/待整理恢复/桌面文档/jdly/crawl_history.json",
        "configure": configure,
        "header":header
    }

    pageDict= {
        "None":[
        ],
        "[拇指兔]":[
        ]
    }

    recorder = Recorder(settings["historyFile"])
    pageDict = recorder.filter(pageDict)
    start(settings, pageDict)
    downloader.close()
    recorder.add(pageDict)
    recorder.save()