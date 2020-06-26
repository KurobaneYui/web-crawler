from concurrent.futures import ThreadPoolExecutor
import requests
import os

def subprogram(urlFile, path):
    try:
        fileName = urlFile[0]
        fileURL = urlFile[1]
        print('\t\t\tstarting download: {}'.format(fileName))
        if not os.path.isdir(path):
            os.makedirs(path)
        with open(os.path.join(path,fileName), 'wb') as f:
            f.write(requests.get(fileURL).content)
        print('\t\t\tfinished download: {}'.format(fileName))
    except Exception as error:
        print("### While downloading {} ,an error occurred: {}".format(fileName,error))

class DownLoader(object):
    def __init__(self):
        super().__init__()
        self.downloadPoor = ThreadPoolExecutor(max_workers=6)

    def __del__(self):
        self.close()

    def close(self):
        self.downloadPoor.shutdown(wait=True)

    def submit(self, urlFile, path):
        '''
        给定文件名及类型和资源网址，依照保存路径保存文件
        '''
        self.downloadPoor.submit(subprogram,urlFile,path)

downloader = DownLoader()

def test():
    url = "https://www.jdlingyu.mobi/wp-content/uploads/2016/02/2017-06-22_23-29-07.jpg"
    for filename in range(10):
        fn = str(filename)+".jpg"
        downloader.submit((fn,url), "D:/testDownload")

if __name__ == "__main__":
    test()