# -*- coding: utf-8 -*-

import asyncio
import aiofiles
import requests
import os, math, json, time, random
from pyppeteer import launcher
from pyppeteer import errors
# hook 禁用 防止监测webdriver
# launcher.DEFAULT_ARGS.remove("--enable-automation")
from pyppeteer import launch

async def crawlPage(bro, url): # FIXME: add exception support
    '''
    指定浏览器和网址，返回打开的页。内部会调用资源发现函数和文件保存函数。
    bro为pyppeteer的浏览器实例，URL为要打开的网址，返回类型为pyppeteer页面实例
    '''
    global settings

    # 页面错开加载
    await asyncio.sleep(0.5+random.random())
    page = await bro.newPage()
    print('\ta new page opened')
    try:
        await page.goto(url)
    except errors.TimeoutError as error:
        await asyncio.sleep(1)
        try:
            await page.goto(url)
        except errors.TimeoutError as error:
            print("we got TimeoutError, but it doesn't matter: {}".format(error))
    print('\t\tsuccessfully goto {}'.format(url))

    # 等待0.5秒确保页面加载正常
    await asyncio.sleep(0.5)
    urls = await getResourceURL(page)
    title, author, tags = await  getFolderInfo(page)

    # 判断目录是否存在确保同名不同url的下载不会重叠
    count = 1
    while True:
        if os.path.isfile(os.path.join(saveFolder,title+'-'+author,'infomation.json')):
            with open(os.path.join(saveFolder,title+'-'+author,'infomation.json'),'r', encoding='utf-8') as f:
                try:
                    information = json.load(f)
                    if 'url' in information :
                        if information['url']!=url:
                            if count>1:
                                title = title[:-len('('+str(count-1)+')')] +'('+str(count)+')'
                            else:
                                title = title+'('+str(count)+')'
                            continue
                except json.decoder.JSONDecodeError as error:
                    pass
        folderName = title+'-'+author
        print('\t\tresource will save to: {}'.format(folderName))
        if not os.path.isdir(os.path.join(saveFolder,folderName)):
            os.makedirs(os.path.join(saveFolder,folderName))
        break

    # json形式记录文件夹下爬取的相关信息
    with open(os.path.join(os.path.join(saveFolder,folderName),'infomation.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'url':url,
                'author':author,
                'title':title,
                'number of resources':len(urls),
                'tag': tags,
                'date':time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False)

    # 以fileGroupNum 为一组，组内协程并行下载，组间串行
    count = 0; tasks = list()
    for saveTuple in urls.items():
        tasks.append( saveFile(saveTuple, os.path.join(saveFolder,folderName)) )
        count += 1
        if count%fileGroupNum==0 or count==len(urls):
            await asyncio.wait(tasks)
            tasks.clear()

    # return page
    await page.close()
    print('\tpage closed')
    # make sure the page has been closed
    await asyncio.sleep(0.5)

async def getFolderInfo(page):
    '''
    指定页面，从中获取保存文件夹的名称
    page为pyppeteer页面实例，返回值为文件名字符串
    '''
    a = await page.J('.title-ctnr')
    a = await a.J('h1')
    a = await a.getProperty('textContent')
    title = (await a.jsonValue()).replace('\r\n','').replace('\n','').replace('>',')').replace('<','(')
    if title == '':
        title = page.url.split('/')[-1]

    a = await page.J('.author-name')
    a = await a.getProperty('textContent')
    author = (await a.jsonValue()).replace('\r\n','').replace('\n','').replace('>',')').replace('<','(')

    a = await page.JJ('.link-tag')
    tags = list()
    for tag in a:
        tag = await tag.getProperty('textContent')
        tags.append( (await tag.jsonValue()).replace('\r\n','').replace('\n','').replace('>',')').replace('<','(') )


    return (title, author, tags)

async def getResourceURL(page, types = None):
    '''
    指定页面和资源类型，从中获取资源的网址。
    page为pyppeteer页面实例，types为需要搜索的资源HTML标签与URL所在属性名（用dict封装），返回值为文件名及类型和资源网址（用dict封装）
    '''
    urls = dict()

    # code (down) about how to locate the resource tag
    a = await page.J('.images')
    # code (up) about how to locate the resource tag

    files = await a.JJ('img')
    for No, file in enumerate(files):
        urlHandle = await file.getProperty('src')
        url = (await urlHandle.jsonValue()).split('@')[0]
        ext = os.path.splitext(url)[-1]
        urls[str(No)+ext] = url
    print('\t\tfind {} resource'.format(len(urls)))
    return urls

async def saveFile(urlFile, path):
    '''
    给定文件名及类型和资源网址，依照保存路径保存文件
    '''
    fileName = urlFile[0]
    fileURL = urlFile[1]
    print('\t\t\tstarting download: {}'.format(fileName))
    if not os.path.isdir(path):
        os.makedirs(path)
    async with aiofiles.open(os.path.join(path,fileName), 'wb') as f:
        await f.write(requests.get(fileURL).content)
    print('\t\t\tfinished download')

async def findNewPage(page):
    '''
    在指定的页面内寻找其他包含资源页的跳转地址。
    '''
    pass

async def start():
    global pageDict, settings

    print('a browser started')
    browser = await launch(headless=False, dumpio=True, timeout=1000*360, autoClose=False,
                        defaultViewport={'width':1366,'height':768})

    try:
        groupSize = settings["groupSize"]
        for subFolderName in pageDict.keys():
            settings["saveSubfolder"] = settings["saveRootFolder"] if subFolderName=="None" else os.path.join(settings["saveRootFolder"],subFolderName)
            pages = pageDict[subFolderName]
            groupNum = math.ceil(len(pages)/groupSize)
            # 每组包含groupSize个链接，组内协程并行爬取，组间串行
            print('=========\nevery {} page per group, we have {} group\n========='.format(groupSize, groupNum))
            for i in range(groupNum):
                print('=========\nNo.{} group\n========='.format(i+1))
                pageGroup = pages[i*groupSize:] if (i+1)*groupSize>len(pages) else pages[i*groupSize:(i+1)*groupSize]
                await asyncio.wait( [crawlPage(browser, pageURL) for pageURL in pageGroup] )
        # 保证正常退出浏览器
        await asyncio.sleep(1)
        print('wait 1 seconds to exit the browser')
    except Exception as error:
        print("### an error occurred:\n#\t{}".format(error))
    finally:
        await browser.close()
        await asyncio.sleep(1) # wait for close
        print('a browser closed')

if __name__ == "__main__":
    '''
    历史记录
    '''
    settings = {
        "saveRootFolder": "G:/待整理恢复/桌面文档/bilibili相簿",
        "groupSize": 5,
        "fileGroupNum": 10,
        "historyFile": "G:/待整理恢复/桌面文档/bilibili相簿/crawl_history.json"
    }
    pageDict = {
        "摄影": [
            
        ],
        "插画": [

        ]
        }
    with open('G:/待整理恢复/桌面文档/bilibili相簿/crawl_history.json','r',encoding="utf-8") as f:
        historyRecording = json.load(f)
    asyncio.run(start())
    for key,value in pageDict:
        historyRecording["爬取记录（按文件夹分类）"][key].extend(value)
    with open('C:/Users/15310/Desktop/待整理恢复/桌面文档/bilibili相簿/crawl_history.json','w',encoding="utf-8") as f:
        json.dump(historyRecording,f,ensure_ascii=False)