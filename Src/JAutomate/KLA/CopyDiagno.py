import os
import tkFileDialog

from Common.FileOperations import FileOperations
from Common.PathOps import PathOps

class CopyDiagno:
    def __init__(self):
        self.src = tkFileDialog.askdirectory()
        if not os.path.isdir(self.src):
            return

        self.dst = self.src + '\\TempC1'

        eventFilePath = self.src + '\\console\\Events'
        eventFileName = ''
        for root, dirs, files in os.walk(eventFilePath):
            for file in files:
                eventFileName = file
        # TODO: Ensure that this is the latest file in Events

        eventFileName = eventFilePath + '\\' + eventFileName
        self.ReadEventFile(eventFileName)

        self.CopySystemFiles()
        self.CopyFromMmiSet(self.layout)
        self.CopyFromMmiSet(self.mmi_setup)

    def ReadEventFile(self, fileName):
        lines = FileOperations.ReadAllLines(fileName)
        index = self.GetLastIndex(lines)

        self.layout = self.GetPathAlone(lines, index + 2)
        self.handler = self.GetPathAlone(lines, index + 3)
        self.mmi_setup = self.GetPathAlone(lines, index + 4)
        self.recipe = self.GetPathAlone(lines, index + 5)

    def GetPathAlone(self, lines, index):
        line = lines[index].replace('\n', '')
        parts = line.split('= ')
        return parts[1]

    def GetLastIndex(self, lines):
        searchTxt = 'DOWN  Load recipe'
        i = 0
        index = -1
        for line in lines:
            if searchTxt in line:
                index = i
            i += 1
        return index

    def CopySystemFiles(self):
        sf = self.src + '\\system files\\'
        self.CopyFile(sf + 'console.ini', self.dst + '\\Handler\\system\\')
        self.CopyFile(sf + 'handler.cnf', self.dst + '\\Handler\\')
        self.CopyFile(sf + 'calib.cal', self.dst + '\\Handler\\')

        self.CopyFile(sf + 'current.rcp', self.dst + self.recipe[2:])
        self.CopyFile(sf + 'current.han', self.dst + self.handler[2:])

    def CopyFromMmiSet(self, setFile):
        path, fileName = PathOps.SplitFilePath(setFile)
        path = path[2:]
        src = self.src + '\\Mmi\\SET\\' + fileName
        dst = self.dst + path + '\\'
        self.CopyFile(src, dst)

    def CopyFile(self, src, dst):
        FileOperations.Copy(src, dst, 0, -1)
