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
            copyTimer = MyTimer(cls._Copy, initWait, inter, src, des, 0)
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
    def LazyCreateDir(cls, dirPath, dirName, initWait, inter):
        print 'Try to Create Dir {} in {} after {} seconds.'.format(dirName, dirPath, initWait)
        copyTimer = MyTimer(cls._CreateDir, initWait, inter, dirPath, dirName)
        copyTimer.start()
        return copyTimer

    @classmethod
    def _CreateDir(cls, dirPath, dirName):
        dirPath = dirPath.replace('/', '\\')
        if not os.path.exists(dirPath):
            print '({}) not existing. Try to create ({}) later.'.format(dirPath, dirName)
            return False
        if os.path.exists(dirPath + dirName):
            return True
        os.mkdir(dirPath + dirName)
        return True

    @classmethod
    def GetAllFiles(cls, path, filterFun):
        for root, dirs, files in os.walk(path):
            for file in files:
                selectedFile = os.path.join(root, file).replace('/', '\\')
                if filterFun(selectedFile):
                    yield selectedFile

    @classmethod
    def GetAllFilesFromList(cls, pathCollection, filterFun):
        selectedFiles = []
        for path in pathCollection:
            for file in cls.GetAllFiles(path, filterFun):
                selectedFiles.append(file)
        return selectedFiles

    @classmethod
    def GetAllDirs(cls, path, filterFun):
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                if filterFun(dir):
                    yield os.path.join(root, dir).replace('\\', '/')

    @classmethod
    def MoveFile(cls, srcPath, desPath):
        if not os.path.exists(srcPath):
            print 'Source Path does not exist : ' + srcPath
            return False
        if os.path.exists(desPath):
            print 'Already file exists in destination : ' + desPath
            return False
        os.rename(srcPath, desPath)
        return True

    @classmethod
    def MoveFiles(cls, srcPaths, desPaths):
        movedFiles = []
        if len(srcPaths) != len(desPaths):
            print 'Error : Mismatch in srcPaths and desPaths'
            return
        for src,des in zip(srcPaths, desPaths):
            if cls.MoveFile(src, des):
                movedFiles.append((src, des))
        return movedFiles
