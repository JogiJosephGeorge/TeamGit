import os
import shutil
import subprocess
from Common.MessageBox import MessageBox
from Common.Test import Test
from KLA.IcosPaths import IcosPaths


class GoldenReportComparer:
    def __init__(self, model):
        self.model = model

    def GetTestPath(self):
        return IcosPaths.GetTestPath(self.model.Source, self.model.TestName)

    def OpenTestFolder(self):
        dirPath = self.GetTestPath()
        if not os.path.isdir(dirPath):
            msg = 'Test folder does not exists : ' + dirPath
            print msg
            MessageBox.ShowMessage(msg)
            return
        dirPath = dirPath.replace('/', '\\')
        subprocess.Popen(['Explorer', dirPath])
        print 'Open directory : ' + dirPath

    def CompareMmiReports(self):
        if not os.path.isfile(self.model.BCompare):
            print 'Beyond compare does not exist in the given path : ' + self.model.BCompare
            return
        leftFolder = self.GetTestPath() + '/GoldenReports'
        rightFolder = self.GetTestPath() + '~/_results'
        newRightFolder = self.GetTestPath() + '~/NewGoldenReports'
        self.CopyResultFiles(leftFolder, rightFolder, newRightFolder)
        subprocess.Popen([self.model.BCompare, leftFolder, newRightFolder])

    def CopyResultFiles(self, leftFolder, rightFolder, newRightFolder):
        leftFiles = self.GetAllFileNames(leftFolder)
        rightFiles = self.GetAllFileNames(rightFolder)
        print leftFiles
        print rightFiles
        matchedFiles = []
        missingFiles = ''
        for left in leftFiles:
            matchName = self.GetMatchedFile(left, rightFiles)
            if matchName:
                matchedFiles.append(matchName)
                print 'Left  : ' + left
                print 'Right : ' + matchName
                self.CopyFile(rightFolder + matchName, newRightFolder + left)
            else:
                missingFiles += left + '\n'

        if len(missingFiles) > 0:
            MessageBox.ShowMessage('Equivalent file Not found for the following:\n' + missingFiles)

    def CopyFile(self, Src, Dst):
        Src = Src.replace('/', '\\')
        Dst = Dst.replace('/', '\\')
        dirs = Dst.split('\\')
        fullPath = ''
        for dir in dirs[:-1]:
            fullPath += dir + '\\'
            if not os.path.isdir(fullPath):
                os.mkdir(fullPath)
        print 'Src : ' + Src
        print 'Dst : ' + Dst
        shutil.copy(Src, Dst)

    def GetAllFileNames(self, path):
        if not os.path.isdir(path):
            print "Path doesn't exist: " + path
            return []
        allFileNames = []
        leftLen = len(path)
        for (dirPath, dirNames, fileNames) in os.walk(path):
            for f in fileNames:
                relPath = dirPath[leftLen:] + '\\' + f
                allFileNames.append(relPath)
        return allFileNames

    def GetMatchedFile(self, name, names):
        for n in names:
            if self.AreSame(name, n):
                return n
        return None

    def AreSame(self, left, right):
        if len(left) != len(right):
            return False
        for l, r in zip(left, right):
            if l != "'" and l != r:
                return False
        return True

class GoldenReportComparerTest:
    def __init__(self):
        path = r'D:\CI\Src4\handler\tests\CDA\Mmi\SurfaceReport'
        self.comparer = GoldenReportComparer(self.CreateModel())
        self.TestAreSame()

    def CreateModel(self):
        class Model:
            pass
        model = Model()
        model.Source = r'D:\CI\Src4'
        model.TestName = r'CDA\Mmi\SurfaceReport'
        model.BCompare = ''
        return model

    def TestAreSame(self):
        a = r"batchAllRejects_pvi_'''.txt"
        b = r'batchAllRejects_pvi_cda.txt'
        Test.Assert(self.comparer.AreSame(a, b), True, 'PathAreSame 1')

        a = r'\ascii\PVI\batchAllRejects_pvi_cda.txt'
        b = r'\ascii\PVI\batchAllRejects_pvi_cda.txt'
        Test.Assert(self.comparer.AreSame(a, b), True, 'PathAreSame 1')

class TempCopy:
    def __init__(self):
        self.TestCopy()

    def TestCopy(self):
        basePath = 'D:/33812/25Feb2058/tests'
        basePath = 'D:/CI/Src3/handler/tests'
        testPath = '/CDA/Mmi/SurfaceReport~'
        fullTestPath = basePath + testPath
        newRightFolder = 'D:/33812/ccc' + testPath

        leftFolder = fullTestPath + '/GoldenReports'
        rightFolder = fullTestPath + '/_results'
        comparer = GoldenReportComparer(None)
        comparer.CopyResultFiles(leftFolder, rightFolder, newRightFolder)

if __name__ == '__main__':
    #GoldenReportComparerTest()
    TempCopy()
