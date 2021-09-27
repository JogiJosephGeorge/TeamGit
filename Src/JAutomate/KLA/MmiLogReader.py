import os
from Common.FileOperations import FileOperations


class FileReader:
    def __init__(self, fileName):
        self.Lines = FileOperations.ReadLine(fileName)
        self.NumLines = len(self.Lines)
        self.Index = 0

    def GetLine(self):
        if self.Index < self.NumLines:
            return self.Lines[self.Index]
        return ''

    def MoveNext(self):
        self.Index += 1

    def IsEOF(self):
        return self.Index >= self.NumLines


class TextPartReader:
    def IgnoreInitialLines(self, fileReader):
        pass

    def Read(self, fileReader):
        pass


class ApplicationNames(TextPartReader):
    def Read(self, fileReader):
        if not self.IgnoreInitialLines(fileReader):
            return False
        appNames = []
        while not fileReader.IsEOF():
            parts = fileReader.GetLine().split(': ')
            if len(parts) == 3 and parts[1].startswith('Application '):
                appNames.append(parts[2])
            else:
                return appNames
            fileReader.MoveNext()
        return appNames

    def GetAppName(self, line):
        return ''

    def IgnoreInitialLines(self, fileReader):
        prevLine = ': Installed Software Version:'
        while not fileReader.IsEOF():
            if prevLine in fileReader.GetLine():
                fileReader.MoveNext()
                return True
            fileReader.MoveNext()
        return False


class MmiLogReader:
    def __init__(self):
        fileReader = FileReader(self.GetMmiLogFileName())
        partReaders = []
        partReaders.append(ApplicationNames())

        for partReader in partReaders:
            partReader.Read(fileReader)

    def GetMmiLogFileName(self):
        logDir = r'C:\icos\log'
        files = os.listdir(logDir)
        for file in files:
            if file.startswith('mmi_') and file.endswith('.log'):
                return os.path.join(logDir, file)
