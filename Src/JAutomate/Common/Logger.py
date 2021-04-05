import os

from datetime import datetime
from Common.FileOperations import FileOperations


class Logger:
    @classmethod
    def Init(cls, fileName):
        cls.fileName = fileName
        fileName = fileName.replace('\\', '/')
        parts = fileName.split('/')[:-1]
        path = None
        for part in parts:
            if path is None:
                path = part
            else:
                path += '/' + part
            if not os.path.isdir(path):
                os.mkdir(path)
        if not os.path.exists(fileName):
            print "File created : " + fileName
            FileOperations.Write(fileName, '')

    @classmethod
    def Log(cls, message):
        message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
        FileOperations.Append(cls.fileName, message)
