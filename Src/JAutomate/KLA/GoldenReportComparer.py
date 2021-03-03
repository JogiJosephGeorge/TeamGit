import os
import subprocess
from Common.MessageBox import MessageBox


class GoldenReportComparer:
    def __init__(self, model):
        self.model = model

    def GetTestPath(self):
        return os.path.abspath(self.model.Source + '/handler/tests/' + self.model.TestName)

    def OpenTestFolder(self):
        dirPath = self.GetTestPath()
        if not os.path.isdir(dirPath):
            msg = 'Test folder does not exists : ' + dirPath
            print msg
            MessageBox.ShowMessage(msg)
            return
        subprocess.Popen(['Explorer', dirPath])
        print 'Open directory : ' + dirPath

    def CompareMmiReports(self):
        if not os.path.isfile(self.model.BCompare):
            print 'Beyond compare does not exist in the given path : ' + self.model.BCompare
            return
        leftFolder = self.GetTestPath() + '/GoldenReports'
        rightFolder = self.GetTestPath() + '~/_results'
        subprocess.Popen([self.model.BCompare, leftFolder, rightFolder])

    def SplitCsvToMultipleFiles(self, fileName):
        dirPath = fileName[:-4]
