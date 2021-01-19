import os
from datetime import datetime, timedelta

from Common.FileOperations import FileOperations


class Logger:
    @classmethod
    def Init(cls, fileName):
        cls.fileName = fileName
        if not os.path.exists(fileName):
            print "File created : " + fileName
            FileOperations.Write(fileName, '')

    @classmethod
    def Log(cls, message):
        message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
        FileOperations.Append(cls.fileName, message)
