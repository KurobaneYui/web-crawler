# -*- coding: utf-8 -*-

import os
import sys
import time
# import pickle
import requests
import bs4
import html5lib
import urllib3
import codecs
import base64
from inspect import isfunction
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
# from concurrent.futures import wait, ALL_COMPLETED
from multiprocessing import Lock
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit

TYPE_TAG = {
    'img': 'src',
    'audio': 'src',
    'video': 'src'
    }

def _log(logString, logStyle='', logType='error'):
    print(logType, ': ', logString)

def downloader(url, filepath, filename, header):
    try:
        resource = requests.get(url, stream=True)
        if os.path.splitext(filename)[-1] == '':
            filename += os.path.splitext(url)[-1]
    except requests.RequestException as error:
        _log("There is some error of connection, please see: {}".format(error))
        return False
    else:
        with open(os.path.join(filepath, filename), 'wb') as f:
            for chunk in resource.iter_content(chunk_size=10241024):
                if chunk:
                    f.write(chunk)
        _log("Successfully download: {}, and saved it to {}".format(filename,filepath),logType='success')
        return True

def _resourceFind(pageSoup, fileType):
    if isinstance(fileType,str):
        fileUrls = set()
        for fileTags in pageSoup.find_all(fileType):
            fullUrl = fileTags[TYPE_TAG[fileType]]
            if fullUrl[:2] == '//':
                fullUrl = 'https:' + fullUrl
            fullUrl = fullUrl.split('?')[0].split('&')[0]
            fileUrls.add(fullUrl)
        return list(fileUrls)
    else:
        _log('Your input is not list, please see: {}'.format(error))
        return False

def _newPageFind(pageSoup):
    return set()

def _fileNameGeneration(pageSoup, lastOne):
    if isinstance(lastOne,str):
        if lastOne == '':
            currentOne = 'file_'+str(1)
        else:
            pre = lastOne[:5]
            order = lastOne[5:]
            try:
                order = int(order)
            except ValueError as error:
                _log("Maybe the last name is not as expection, please see: {}".format(error))
                return False
            else:
                order = order+1
                currentOne = str(pre)+str(order)
        return currentOne
    else:
        _log('Your input is not string, please see: {}'.format(error))
        return False

def _folderNameGeneration(pageSoup, lastOne):
    if isinstance(lastOne,str):
        if lastOne == '':
            currentOne = str(1)
        else:
            order = lastOne
            try:
                order = int(order)
            except ValueError as error:
                _log("Maybe the last name is not as expection, please see: {}".format(error))
                return False
            else:
                order = order+1
                currentOne = str(order)
        return currentOne
    else:
        _log('Your input is not string, please see: {}'.format(error))
        return False

class WebCrawler():
    '''
    '''
    def __init__(self):
        self.originalPagesSet = set()
        self.resourceTypes = set()
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36 Edg/80.0.361.54'
            }
        self.saveFolder = './PagesResources'
        self.newPageFind = _newPageFind
        self.resourceFind = _resourceFind
        self.log = _log
        self.fileNameGenerator = _fileNameGeneration
        self.folderNameGenerator = _folderNameGeneration
        # self._folderNum = 0

    def setLogStrategy(self, func):
        if isfunction(func):
            self.log = func
            return True
        else:
            self.log('Parameter given is not a function')
            return False

    def setNewPagesFindStrategy(self, func):
        if isfunction(func):
            self.newPageFind = func
            return True
        else:
            self.log('Parameter given is not a function')
            return False

    def setResourcesFindStrategy(self, func):
        if isfunction(func):
            self.resourceFind = func
            return True
        else:
            self.log('Parameter given is not a function')
            return False

    def setFileNameGenerationStrategy(self, func):
        if isfunction(func):
            self.fileNameGenerator = func
            return True
        else:
            self.log('Parameter given is not a function')
            return False

    def setFolderNameGenerationStrategy(self, func):
        if isfunction(func):
            self.folderNameGenerator = func
            return True
        else:
            self.log('Parameter given is not a function')
            return False

    def setHeader(self, head):
        '''
        '''
        if isinstance(head, str):
            self.header = head
            return True
        else:
            self.log('Header must be string, but given type is: {}'.format(type(head)))
            
    def setSaveFolder(self, path):
        if os.path.isdir(path):
            self.saveFolder = os.path.join(path, 'PagesResources/')
            self.log('Set save folder to: {}'.format(self.saveFolder), logType='success')
            return True
        else:
            self.log("It's not a folder path, or folder is not exist")
            return False

    def addResourceType(self, resourceType):
        if isinstance(resourceType, str):
            if resourceType in TYPE_TAG:
                self.resourceTypes.add(resourceType)
                self.log('Successfully add a resource type: {}'.format(resourceType),logType='success')
                return True
            else:
                self.log('The resource type you want to add is not support: {}'.format(resourceType))
                return False
        elif isinstance(resourceType, list) or isinstance(resourceType, tuple):
            add_counter = 0
            for i in resourceType:
                if isinstance(i, str):
                    if i in TYPE_TAG:
                        self.resourceTypes.add(i)
                        add_counter += 1
                    else:
                        self.log("We got an file type but not in our support list, the type is: {}".format(i))
                else:
                    self.log('We got an element that not string, element type is: {}'.format(type(i)))
            self.log('Successfully add {} types of resource'.format(type(add_counter)), logType='success')
            return True
        else:
            self.log('The resource type you input is in unsupported type: {}'.format(type(resourceType)))
            return False

    def addOriginalPage(self, urls):
        if isinstance(urls, str):
            self.originalPagesSet.add(urls)
            self.log('Add 1 url to OriginalPages.', logType='success')
            return True
        elif isinstance(urls, list) or isinstance(urls, tuple):
            add_counter = 0
            # SET.update(set(LIST)) method cannot check the elements
            for url in urls:
                if isinstance(url, str):
                    self.originalPagesSet.add(url)
                    add_counter += 1
                else:
                    self.log('We got an element that not string, and type is: {}'.format(type(url)), logType='warning')
            self.log('Add {} url(s) to OriginalPages.'.format(add_counter), logType='success')
            return True
        else:
            self.log('The given parameter is not string, tuple, or list, the type is: {}'.format(type(urls)))
            return False

    def oneProcess(self, multithread):
        if not os.path.isdir(self.saveFolder):
            os.mkdir(self.saveFolder)
            self.log('root folder is not exist, create folder: {}'.format(self.saveFolder),logType='warning')
        
        pageFolderName = ''
        while len(self.originalPagesSet):
            url = self.originalPagesSet.pop()
            
            page = requests.get(url,headers = self.header)
            page.encoding = UnicodeDammit(page.content).original_encoding
            pageSoup = BeautifulSoup(page.content,'html5lib')

            self.originalPagesSet = self.originalPagesSet.union(self.newPageFind(pageSoup))
            pageFolderName = self.folderNameGenerator(pageSoup, pageFolderName) # TODO: finished name generator
            if not os.path.isdir(os.path.join(self.saveFolder,pageFolderName)):
                os.mkdir(os.path.join(self.saveFolder,pageFolderName))
            while len(self.resourceTypes):
                resourceType = self.resourceTypes.pop()
                if not resourceType in TYPE_TAG:
                    self.log('file type is not support: {}'.format(fType))
                    continue
                #==========
                processor(
                    pageSoup,
                    self.header,
                    resourceType,
                    os.path.join(self.saveFolder,pageFolderName),
                    self.resourceFind,
                    self.fileNameGenerator,
                    multithread
                    )
                #==========

    def multiProcess(self, multithread):
        processPool = ProcessPoolExecutor()

        if not os.path.isdir(self.saveFolder):
            os.mkdir(self.saveFolder)
            self.log('root folder is not exist, create folder: {}'.format(self.saveFolder),logType='warning')
        
        pageFolderName = '';fileName=1
        while len(self.originalPagesSet):
            url = self.originalPagesSet.pop()
            
            page = requests.get(url,headers = self.header)
            page.encoding = UnicodeDammit(page.content).original_encoding
            pageSoup = BeautifulSoup(page.content,'html5lib')

            self.originalPagesSet = self.originalPagesSet.union(self.newPageFind(pageSoup))
            pageFolderName = self.folderNameGenerator(pageSoup, pageFolderName) # TODO: finished name generator
            if not os.path.isdir(os.path.join(self.saveFolder,pageFolderName)):
                os.mkdir(os.path.join(self.saveFolder,pageFolderName))
            while len(self.resourceTypes):
                resourceType = self.resourceTypes.pop()
                if not resourceType in TYPE_TAG:
                    self.log('file type is not support: {}'.format(fType))
                    continue
                # 针对指定类型，开启进程，传入参数：
                # pageSoup、文件夹完整目录、header参数、
                # 文件类型、资源发现函数、文件名生成函数
                #==========
                processPool.submit(
                    processor,
                    pageSoup,
                    self.header,
                    resourceType,
                    os.path.join(self.saveFolder,pageFolderName),
                    self.resourceFind,
                    self.fileNameGenerator,
                    multithread,
                    )
                #==========
        # for future in as_completed(processPoolTasks):
        #     try:
        #         result = future.result()
        #     except BaseException as error:
        #         print(error)
        processPool.shutdown(True)
    
    def start(self, multiprocess=True, multithread=True):
        print(sys.getrecursionlimit())
        sys.setrecursionlimit(5000)
        self.log('Start crawler, you set download folder: {} \n\t absolute path is: {}'.format(self.saveFolder,os.path.abspath(self.saveFolder)),logType='warning')
        if multiprocess:
            self.multiProcess(multithread)
        else:
            self.oneProcess(multithread)
        

def processor(pageSoup, header, fileType, saveFolder, func_resourceFind, func_fileName, multithread):
    if multithread:
        threadPool = ThreadPoolExecutor()

    fileUrls = func_resourceFind(pageSoup, fileType)
    # 对每个list启动线程进行下载，传入参数：
    # header、文件名、保存路径、文件链接
    #==========
    fileName = ''
    for fileUrl in fileUrls:
        fileName = func_fileName(pageSoup, fileName) # TODO: finished name generator

        if multithread:
            threadPool.submit(
                downloader,
                fileUrl,
                saveFolder,
                fileName,
                header
                )
        else:
            downloader(
                fileUrl,
                saveFolder,
                fileName,
                header
                )
    #==========
    if multithread:
        threadPool.shutdown(True)