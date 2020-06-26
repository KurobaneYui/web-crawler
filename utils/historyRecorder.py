import os, json

class Recorder(object):
    def __init__(self,file):
        super().__init__()
        self.file = file
        if os.path.isfile(file):
            with open(file,'r',encoding="utf-8") as f:
                try:
                    self.history = json.load(f)
                except Exception as error:
                    print("find error while reading json file: {}".format(error))
                else:
                    return
        print("历史记录不存在，将建立新文件，请输入相关信息以完善历史记录文件：")
        wangzhan = input("网站名称：")
        wangzhi = input("网站URL：")
        self.history = {"网站":wangzhan,"网址":wangzhi}
        self.history["爬取记录（按文件夹分类）"] = dict()

    def save(self):
        with open(self.file,'w',encoding="utf-8") as f:
            json.dump(self.history,f,ensure_ascii=False,indent=4)

    def add(self, historyDict):
        for key,value in historyDict.items():
            if not key in self.history["爬取记录（按文件夹分类）"]:
                self.history["爬取记录（按文件夹分类）"][key] = list()
            self.history["爬取记录（按文件夹分类）"][key].extend(value)
    
    def check(self,Url): # 检查重复，重复返回True，不重复返回False
        for value in self.history["爬取记录（按文件夹分类）"].values():
            if Url in value:
                return True
        return False

    def filter(self, historyDict):
        for key,value in historyDict.items():
            for i in tuple(value):
                for v in self.history["爬取记录（按文件夹分类）"].values():
                    if i in v: value.remove(i)
        return historyDict

def test():
    r = Recorder("D:/crawler.json")

if __name__ == "__main__":
    test()