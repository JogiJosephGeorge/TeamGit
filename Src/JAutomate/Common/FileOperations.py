import os

class FileOperations:
    @classmethod
    def ReadLine(cls, fileName, utf = 'utf-8'):
        if not os.path.exists(fileName):
            print "File doesn't exist : " + fileName
            return []
        f = open(fileName, 'rb')
        data = f.read()
        f.close()
        return data.decode(utf).splitlines()

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
