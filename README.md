# 简单网页爬虫

提供两种爬虫。legency使用普通requests、BeautifulSoup4模块，部分网页无法爬取；pyppeteer使用pyppeteer的API，速度较慢。

## 目录结构

根目录：提供了web_crawler_legeny和web_crawler_pyppeteer两个下载器，相互独。

utils目录：包含了历史下载记录模块和多线程下载模块，根目录下两个下载器均会用到。

configure目录：提供了用于设置爬取流程的json文件，调整json文件可以让爬虫适应不同的网站结构。已包含用于bilibili相册、绝对领域网的json文件。

## web_crawler_legency

> 利用BeautifulSoup4, requests, threading模块进行并行下载。还调用了如os等模块辅助。请先使用pip install bs4, requests下载依赖

从网页获取资源并下载。可以指定下载的资源类型，同时可以指定如何通过已有页面获取相关的其他页面（如：下一页）。但是此方案没有处理诸如js加密、动态加载等问题，只能用于爬取没有防爬虫的静态网站。

## web_crawler_pyppeteer

> 利用requests, pyppeteer, aiofiles, asyncio模块进行爬取。还调用了诸如os模块辅助。请先使用pip install aiofiles,pyppeteer,requests进行依赖的安装。对于pyppeteer依赖的chromium内核的安装，请参考官方文档或网络博客

功能同legency文件，但使用pyppeteer进行协程并行，资源占用较大，但是可以解决网站js加密、动态加载等问题。

## json文件格式

第一级|第二级|第三级|第四级|第五级|备注
:-:|:-:|:-:|:-:|:-:|:-:
saveRootFolder|（文件夹路径字符串）|-|-|-|必选，保存根目录
resources|（键值对）|-|-|-|-
-|search|-|-|-|-
folderName|-|-|-|-|-
fileName|-|-|-|-|-