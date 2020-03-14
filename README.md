# 两个文件相互独立

> 用于资源下载的简单爬虫

## web_crawler_legency

> 利用BeautifulSoup4, requests, threading模块进行并行下载。还调用了如os等模块辅助。请先使用pip install bs4, requests下载依赖

从网页获取资源并下载。可以指定下载的资源类型，同时可以指定如何通过已有页面获取相关的其他页面（如：下一页）。但是此方案没有处理诸如js加密、动态加载等问题，只能用于爬取没有防爬虫的静态网站。

## web_crawler_pyppeteer

> 利用requests, pyppeteer, aiofiles, asyncio模块进行爬取。还调用了诸如os模块辅助。请先使用pip install aiofiles,pyppeteer,requests进行依赖的安装。对于pyppeteer依赖的chromium内核的安装，请参考官方文档或网络博客

功能同legency文件，但使用pyppeteer进行协程并行，资源占用较大，但是可以解决网站js加密、动态加载等问题。