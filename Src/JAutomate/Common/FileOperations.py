import os
import time

from Common.MyTimer import MyTimer
from Common.OsOperations import OsOperations


class FileOperations:
    @classmethod
    def ReadLine(cls, fileName, utf = None):
        if not os.path.exists(fileName):
            print "File doesn't exist : " + fileName
            return []
        f = open(fileName, 'rb')
        data = f.read()
        f.close()
        if utf:
            data = data.decode(utf)
        return data.splitlines()

    @classmethod
    def Append(cls, fileName, message):
        if not os.path.exists(fileName):
            print "File doesn't exist : " + fileName
            return
        with open(fileName, 'a') as f:
             f.write((message + '\n').encode('utf8'))

    @classmethod
    def Write(cls, fileName, message):
        with open(fileName, 'w') as f:
             f.write((message + '\n').encode('utf8'))

    @classmethod
    def Delete(cls, fileName):
        if os.path.isfile(fileName):
            os.remove(fileName)
            print 'File deleted : ' + fileName
        else:
            print 'Not found to delete : ' + fileName

    @classmethod
    def Copy(cls, src, des, initWait = 0, inter = 0):
        if initWait == 0 and inter == 0:
            cls._Copy(src, des, inter)
        else:
            print 'Try to Copy({},{}) after {} seconds.'.format(src, des, initWait)
            copyTimer = MyTimer(cls._Copy, initWait, inter, src, des)
            copyTimer.start()
            return copyTimer

    @classmethod
    def _Copy(cls, src, des, inter = 0):
        src = src.replace('/', '\\')
        des = des.replace('/', '\\')
        while not os.path.exists(des):
            if inter > 0:
                print '({}) not existing. Try to Copy({}) after {} seconds.'.format(des, src, inter)
                time.sleep(inter)
            else:
                print 'Wrong input - Destination folder not existing : ' + des
                return False
        if os.path.isfile(src):
            OsOperations.System('COPY /Y "' + src + '" "' + des + '"')
        elif os.path.isdir(src):
            OsOperations.System('XCOPY /S /Y "' + src + '" "' + des + '"')
        else:
            print 'Wrong input - Neither file nor directory : ' + src
            return False
        return True

    @classmethod
    def GetAllFiles(cls, path, filterFun):
        selectedFiles = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if filterFun(file):
                    selectedFile = os.path.join(root, file).replace('\\', '/')
                    selectedFiles.append(selectedFile)
        return selectedFiles

    @classmethod
    def GetAllFilesFromList(cls, paths, filterFun):
        selectedFiles = []
        for path in paths:
            selectedFiles += cls.GetAllFiles(path, filterFun)
        return selectedFiles

    @classmethod
    def GetAllDirs(cls, path, filterFun):
        selectedDirs = []
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if filterFun(dir):
                    selectedDir = os.path.join(root, dir).replace('\\', '/')
                    selectedDirs.append(selectedDir)
        return selectedDirs
