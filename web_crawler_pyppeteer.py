# -*- coding: utf-8 -*-

import asyncio
import aiofiles
import requests
import os
from pyppeteer import launcher
# hook  禁用 防止监测webdriver
launcher.AUTOMATION_ARGS.remove("--enable-automation")
from pyppeteer import launch

async def gotoPage(bro, url): # FIXME: add exception support
    '''
    指定浏览器和网址，返回打开的页。内部会调用资源发现函数和文件保存函数。
    bro为pyppeteer的浏览器实例，URL为要打开的网址，返回类型为pyppeteer页面实例
    '''
    print('\ta new page opened')
    page = await bro.newPage()
    await page.goto(url,waitUntil='networkidle0')
    print('\tsuccessfully goto {}'.format(url))

    # 等待0.5秒确保页面加载正常
    await asyncio.sleep(0.5)
    await getResourceURL(page)
    
    
    return page

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
        urls[str(No)+'.png'] = await urlHandle.jsonValue()

    await asyncio.wait( [saveFile(saveTuple, 'C:/Users/15310/Desktop') for saveTuple in urls.items()] )
    
    return urls

async def saveFile(urlFile, path):
    '''
    给定文件名及类型和资源网址，依照保存路径保存文件
    '''
    print('\tstarting download')
    fileName = urlFile[0]
    fileURL = urlFile[1]
    async with aiofiles.open(os.path.join(path,fileName), 'wb') as f:
        await f.write(requests.get(fileURL).content)
    print('\tfinished download')

async def findNewPage(page):
    '''
    在指定的页面内寻找其他包含资源页的跳转地址。
    '''
    pass

async def start():
    print('a browser started')
    browser = await launch()
    page = await gotoPage(browser,'https://h.bilibili.com/1618979')
    # 保证正常退出浏览器
    print('wait 2 seconds to exit the browser')
    await asyncio.sleep(1)
    await browser.close()
    print('a browser closed')
    await asyncio.sleep(1)

asyncio.run(start())
