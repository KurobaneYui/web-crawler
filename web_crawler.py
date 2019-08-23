# -*- coding: utf-8 -*-

import html5lib
import urllib3
import bs4
import os
import sys
import codecs
import base64
import requests
import time
import multiprocessing
import threading
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit

class PaChong:
    '''
    说明
    属性:
        original_pages_set 起始挖掘页集
        head 通信头文件
        save_folder 保存文件夹位置
        ---------------------------------------------------
        rfs 资源搜索函数
        nfs 网页迭代函数
        sfns 文件夹名产生函数
    方法:
        add_original_page() 添加起始挖掘页
        set_head() 设置通信头文件
        set_newpages_find_strategy() 设置网页迭代方式
        set_resources_find_strategy() 设置资源发现方式
        ---------------------------------------------------
        set_save_folder() 设置保存文件夹
        set_save_folder_name_strategy() 设置保存分类的文件夹名称规则
        ---------------------------------------------------
        start() 单进程（多线程）方式启动
        start_with_multiprocessor() 多进程方式下载
        ----------------------------------------------------
        newpages_find_strategy() 网页迭代方式
        resources_find_strategy() 资源发现方式
        save_folder_name_strategy() 获取保存分类的文件夹名称
    '''
    
    def __init__(self):
        self.original_pages_set = set()
        self.head = ""
        self.save_folder = "./pachong"
        self.nfs = lambda x : list()
        self.rfs = lambda x : list()
        self.sfns = lambda x : x+1

    def add_original_page(self, pages):
        '''
        说明
        pages:
            1.if is list or tuple of strings: add urls to the set of urls
            2.if is string: add to the set of urls
        return:
            bool, return False unless add at least one url
        '''
        if isinstance(pages, str):
            self.original_pages_set.add(pages)
            return True
        elif isinstance(pages, list) or isinstance(pages, tuple):
            returns = False
            for i in pages:
                if isinstance(i, str):
                    self.original_pages_set.add(pages)
                    returns = True
                else:
                    print("\nWarning!!! The list or tuple has instance that not the string:")
                    print("\ttype of the instance: {}\n".format(type(i)))
            return returns
        else:
            print("\nError!!! Not string or list of string\n")
            return False

    def set_head(self, head):
        '''
        说明
        head:
            head for sending linking
        return:
            if head is a sting, then return True
        '''
        if isinstance(head, str):
            self.head = head
            return True
        else:
            print("\nError!!! Unsupport instance type\n")
            return False

    def set_newpages_find_strategy(self, func):
        '''
        说明
        func:
            a function which accept one para and return a list of urls of pages
        return:
            a list of urls of pages
        '''
        if isinstance(func, function):
            self.nfs = func
            return True
        else:
            print("\nError!!! Not a function\n")
            return False

    def set_resources_find_strategy(self, func):
        '''
        说明
        func:
            a function which accept one para and return a list of urls of resources
        return:
            a list of urls of resources
        '''
        if isinstance(func, function):
            self.rfs = func
            return True
        else:
            print("\nError!!! Not a function\n")
            return False

    def set_save_folder(self, path):
        '''
        说明
        path:
            the path of the folder where files are saved
        return:
            if path exist, then return True
        '''
        if os.path.isdir(path):
            self.save_folder = os.path.join(path, "pachong/")
            print("Set save folder directory as: {}".format(self.save_folder))
            return True
        else:
            print("\nError!!! Not a directory\n")
            return False

    def set_save_folder_name_strategy(self, func):
        '''
        说明
        func:
            a function which accept one para and return a string of a folder name
        return:
            a string of a folder name
        '''
        if isinstance(func, function):
            self.sfns = func
            return True
        else:
            print("\nError!!! Not a function\n")
            return False

    def start(self, method=1, have_content=True):
        '''
        两种网页迭代方式
        方式一：从原始网页可以获取所有要迭代的网页链接（原始网页是否包含数据分别对应以下1和2）
            1.遍历原始网页，挑出一个
                i.送入网页迭代函数，获取所有网页（原始网页添加在第一个位置）
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
            2.遍历原始网页，挑出一个
                i.送入网页迭代函数，获取所有网页
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
        ----------------------------------------------------
        方式二：网页需要通过已发现的网页进行不重复的迭代（原始网页是否包含数据分别对应以下1和2）
            1.遍历原始网页，挑出一个
                i.送入文件夹名称函数，获取保存的文件夹名称
                *ii.第几个网页则保存的文件前缀为几
                *iii.送入资源获取函数，返回资源列表
                *iv.第几个资源则文件名后缀为几
                *v.传入资源链接和文件保存位置以及名称，下载资源
                ii.循环直至迭代终了
                    i.网页放入迭代函数，获取到下一个网页，无则循环终了
                    ii.第几个网页则保存的文件前缀为几
                    iii.送入资源获取函数，返回资源列表
                    iv.第几个资源则文件名后缀为几
                    v.传入资源链接和文件保存位置以及名称，下载资源
            2.遍历原始网页，挑出一个
                i.送入文件夹名称函数，获取保存的文件夹名称
                ii.循环直至迭代终了
                    i.网页放入迭代函数，获取到下一个网页，无则循环终了
                    ii.第几个网页则保存的文件前缀为几
                    iii.送入资源获取函数，返回资源列表
                    iv.第几个资源则文件名后缀为几
                    v.传入资源链接和文件保存位置以及名称，下载资源
        '''
        pass

    def start_with_multiprocessor(self):
        pass

    def newpages_find_strategy(self):
        pass

    def resources_find_strategy(self):
        pass

    def save_folder_name_strategy(self):
        pass

    def download_resource(self, url, filepath):
        '''
        说明
        url:
            the url of the file waiting for downloading
        filepath:
            the path where the file is saved
        return:
            when download successfully, return True; else return False
        '''
        resurce = requests.get(url, stream=True)
        with open(filepath, "wb") as f:
            for chunk in resource.iter_content(chunk_size=10241024):
                if chunk:
                    f.write(chunk)