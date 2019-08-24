# -*- coding: utf-8 -*-

import os
import sys
import time
import requests
import bs4
import html5lib
import urllib3
import codecs
import base64
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit

def _newpageFind(url, header):
    return list()

def _resourceFind(url,header):
    resource_dict = dict()

    page = requests.get(url,headers=header)
    page.encoding = UnicodeDammit(page.content).original_encoding
    page_soup = BeautifulSoup(page.content, 'html5lib')

    for x in page_soup.find_all('img'):
        resource_dict[x['src']] = 'img'+'/'+x['src'].split('.')[-1]

    return resource_dict

def _sourceFileName(x, header):
    return ""

def download_resource(url, filepath, filename):
    '''
    说明
    url:
        the url of the file waiting for downloading
    filepath:
        the path where the file is saved
    return:
        when download successfully, return True; else return False
    '''
    resource = requests.get(url, stream=True)
    with open(os.path.join(filepath, filename), "wb") as f:
        for chunk in resource.iter_content(chunk_size=10241024):
            if chunk:
                f.write(chunk)
    print("Successfully download file {}, saved at {}".format(filename,filepath))

class PaChong:
    '''
    说明
    属性:
        original_pages_set 起始挖掘页集
        header 通信头文件
        save_folder 保存文件夹位置
        ---------------------------------------------------
        rfs 资源搜索函数
        nfs 网页迭代函数
        sfns 文件夹名产生函数
    方法:
        add_original_page() 添加起始挖掘页
        set_header() 设置通信头文件
        set_newpages_find_strategy() 设置网页迭代方式
        set_resources_find_strategy() 设置资源发现方式
        ---------------------------------------------------
        set_save_folder() 设置保存文件夹
        set_save_folder_name_strategy() 设置保存分类的文件夹名称规则
        ---------------------------------------------------
        start() 单进程方式启动
        start_with_multiprocessor() 多进程方式启动
        ----------------------------------------------------
        newpages_find() 网页迭代方式
        resources_find() 资源发现方式
        save_folder_name() 获取保存分类的文件夹名称
    '''
    
    def __init__(self):
        self.original_pages_set = set()
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
            }
        self.save_folder = "./GetPagesDatas"
        self.nfs = _newpageFind
        self.rfs = _resourceFind
        self.sfns = _sourceFileName
        self._folderNum = 0

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

    def set_header(self, head):
        '''
        说明
        head:
            head for sending linking
        return:
            if head is a sting, then return True
        '''
        if isinstance(head, str):
            self.header = head
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
        import inspect
        if inspect.isfunction(func):
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
        import inspect
        if inspect.isfunction(func):
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
        import inspect
        if inspect.isfunction(func):
            self.sfns = func
            return True
        else:
            print("\nError!!! Not a function\n")
            return False

    def start(self, method=1, have_content=True, numerical=False):
        '''
        两种网页迭代方式
        方式一(method=1)：从原始网页可以获取所有要迭代的网页链接（原始网页是否包含数据分别对应以下1和2）
        （建立保存文件夹！！！）
            1.遍历原始网页，挑出一个(have_content=True)
                i.送入网页迭代函数，获取所有网页（原始网页添加在第一个位置）
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
            2.遍历原始网页，挑出一个(have_content=False)
                （建立保存文件夹）
                i.送入网页迭代函数，获取所有网页
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
        ----------------------------------------------------
        方式二(method=2)：网页需要通过已发现的网页进行不重复的迭代（原始网页是否包含数据分别对应以下1和2）
        （建立保存文件夹！！！）
            1.遍历原始网页，挑出一个(have_content=True)
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
            2.遍历原始网页，挑出一个(have_content=False)
                i.送入文件夹名称函数，获取保存的文件夹名称
                ii.循环直至迭代终了
                    i.网页放入迭代函数，获取到下一个网页，无则循环终了
                    ii.第几个网页则保存的文件前缀为几
                    iii.送入资源获取函数，返回资源列表
                    iv.第几个资源则文件名后缀为几
                    v.传入资源链接和文件保存位置以及名称，下载资源
        '''

        if not os.path.isdir(self.save_folder):
            os.mkdir(self.save_folder)

        if method == 1:
            for url in self.original_pages_set: # 从原始网页中遍历每一个原始页面
                
                new_page_list = self.newpages_find(url) # 获取子页面
                
                if have_content == True: # 如果原始页面也包含内容
                    new_page_list = [url]+new_page_list # 把原始页面放入子页面列表的第一个
                elif have_content == False:
                    pass
                else:
                    print("\nError!!! have_content must be bool type\n")
                
                folder_name = self.save_folder_name(url, numerical) # 获取要保存至的文件夹的名称
                folder_path = os.path.join(self.save_folder,folder_name)
                if not os.path.isdir(folder_path):
                    os.mkdir(folder_path)

                page_counter = 0
                for subpage in new_page_list: # 遍历每一个含有资源的网页
                    page_counter += 1
                    fileNAMEq = str(page_counter)
                    resources_url = self.resources_find(subpage) # 获取每一个资源的链接和资源类型

                    resource_counter = 0
                    for resource_url,resource_type in resources_url.items():
                        resource_counter += 1
                        fileNAME = fileNAMEq+'_'+str(resource_counter)
                        print("Downloading {} file, named as: {}".format(resource_type.split('/')[0], fileNAME))
                        download_resource(resource_url, folder_path, fileNAME+'.{}'.format(resource_type.split('/')[1])) # 开始下载
        elif method == 2:
            pass
        else:
            print("\nError!!! method can only be 1 or 2\n")

    def start_with_multiprocessor(self, method=1, have_content=True, numerical=False, max_workers=None):
        '''
        两种网页迭代方式
        方式一(method=1)：从原始网页可以获取所有要迭代的网页链接（原始网页是否包含数据分别对应以下1和2）
        （建立保存文件夹！！！）
            1.遍历原始网页，挑出一个(have_content=True)
                i.送入网页迭代函数，获取所有网页（原始网页添加在第一个位置）
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
            2.遍历原始网页，挑出一个(have_content=False)
                （建立保存文件夹）
                i.送入网页迭代函数，获取所有网页
                ii.送入文件夹名称函数，获取保存的文件夹的名称
                iii.迭代每一个网页
                    i.第几个网页，则文件名前缀为几
                    ii.送入资源获取函数，返回资源列表
                    iii.第几个资源则文件名后缀为几
                    iv.传入资源链接和文件保存位置以及名称，下载资源
        ----------------------------------------------------
        方式二(method=2)：网页需要通过已发现的网页进行不重复的迭代（原始网页是否包含数据分别对应以下1和2）
        （建立保存文件夹！！！）
            1.遍历原始网页，挑出一个(have_content=True)
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
            2.遍历原始网页，挑出一个(have_content=False)
                i.送入文件夹名称函数，获取保存的文件夹名称
                ii.循环直至迭代终了
                    i.网页放入迭代函数，获取到下一个网页，无则循环终了
                    ii.第几个网页则保存的文件前缀为几
                    iii.送入资源获取函数，返回资源列表
                    iv.第几个资源则文件名后缀为几
                    v.传入资源链接和文件保存位置以及名称，下载资源
        '''

        if not os.path.isdir(self.save_folder):
            os.mkdir(self.save_folder)

        if method == 1:
            process_pool = ProcessPoolExecutor(max_workers=max_workers)
            process_pool_tasks = list()

            for url in self.original_pages_set: # 从原始网页中遍历每一个原始页面
                
                new_page_list = self.newpages_find(url) # 获取子页面
                
                if have_content == True: # 如果原始页面也包含内容
                    new_page_list = [url]+new_page_list # 把原始页面放入子页面列表的第一个
                elif have_content == False:
                    pass
                else:
                    print("\nError!!! have_content must be bool type\n")
                
                folder_name = self.save_folder_name(url, numerical) # 获取要保存至的文件夹的名称
                folder_path = os.path.join(self.save_folder,folder_name)
                if not os.path.isdir(folder_path):
                    os.mkdir(folder_path)

                page_counter = 0
                for subpage in new_page_list: # 遍历每一个含有资源的网页
                    page_counter += 1
                    fileNAMEq = str(page_counter)
                    resources_url = self.resources_find(subpage) # 获取每一个资源的链接和资源类型

                    resource_counter = 0
                    for resource_url,resource_type in resources_url.items():
                        resource_counter += 1
                        fileNAME = fileNAMEq+'_'+str(resource_counter)
                        print("Downloading {} file, named as: {}".format(resource_type.split('/')[0], fileNAME))

                        process_pool_tasks.append(
                            process_pool.submit(
                                download_resource,
                                resource_url,
                                folder_path,
                                fileNAME+'.{}'.format(resource_type.split('/')[1])
                                )
                            ) # 放入进程池
            process_pool.shutdown()
            #wait(process_pool_tasks,return_when=ALL_COMPLETED)
        elif method == 2:
            pass
        else:
            print("\nError!!! method can only be 1 or 2\n")

    def newpages_find(self, url):
        '''
        说明
        url:
            the url which to find new pages based on
        return:
            a list of new pages
        '''
        print("searching new pages...")
        new_pages = self.nfs(url, self.header)
        print("we find these page(s):")
        if new_pages is None or new_pages == []:
            print("\tNothing")
        else:
            for i in new_pages:
                print("\t",i)
        return new_pages

    def resources_find(self, url):
        '''
        说明
        url:
            the url where to find resource
        return:
            a dict of all resources, the key is the url of resource and the value is the type of the resource
        '''
        print("searching all resources...")
        resources = self.rfs(url, self.header);print(resources)
        print("we get these resources:")
        if resources is None or resources == {}:
            print("\tNothing")
        else:
            for a,b in resources.items():
                print("\t",b,"\t",a)
        return resources

    def save_folder_name(self, urlORnum, numerical=False):
        '''
        说明
        urlORnum:
            url to substract name or accumulatable num for name
        return:
            a string of file name
        '''
        if numerical:
            self._folderNum += 1
            return str(self._folderNum)
        else:
            return self.sfns(urlORnum, self.header)