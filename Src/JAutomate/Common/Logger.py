import os

from datetime import datetime
from Common.FileOperations import FileOperations


class Logger:
    @classmethod
    def Init(cls, fileName):
        cls.fileName = fileName
        cls.ExtLoggers = []
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
    def AddLogger(cls, logMethod):
        if not logMethod:
            print 'Invalid log method is given!'
            return
        for logMethod in cls.ExtLoggers:
            print 'Same logger exists already'
            return
        cls.ExtLoggers.append(logMethod)

    @classmethod
    def Log(cls, message):
        for extLogger in cls.ExtLoggers:
            extLogger(message)
        message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
        FileOperations.Append(cls.fileName, message)
