import os
import subprocess
from Common.FileOperations import FileOperations
from Common.MessageBox import MessageBox
from Common.Test import Test
from KLA.IcosPaths import IcosPaths


class GoldenReportComparer:
    def __init__(self, model):
        self.model = model

    def GetTestPath(self):
        curSrc = self.model.Src.GetCur()
        return IcosPaths.GetTestPath(curSrc.Source, self.model.AutoTests.TestName)

    def OpenTestFolder(self):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
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
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        testPath = self.GetTestPath()
        if not os.path.exists(testPath):
            print 'Test path does not exists : ' + testPath
            return
        leftFolder = testPath + '/GoldenReports'
        rightFolder = testPath + '~/_results'
        newRightFolder = testPath + '~/NewGoldenReports'
        self.CopyAndCompareTestResults(leftFolder, rightFolder, newRightFolder)

    def CopyAndCompareTestResults(self, leftFolder, rightFolder, newRightFolder):
        if not os.path.isfile(self.model.BCompare):
            print 'Beyond compare does not exist in the given path : ' + self.model.BCompare
            return
        if self.CopyResultFiles(leftFolder, rightFolder, newRightFolder):
            subprocess.Popen([self.model.BCompare, leftFolder, newRightFolder])

    def CopyResultFiles(self, leftFolder, rightFolder, newRightFolder):
        leftFiles = self.GetAllFileNames(leftFolder)
        rightFiles = self.GetAllFileNames(rightFolder)
        #print leftFiles
        #print rightFiles
        matchedFiles = []
        missingFiles = []
        for left in leftFiles:
            matchName = self.GetMatchedFile(left, rightFiles)
            if matchName:
                matchedFiles.append(matchName)
                #print 'Left  : ' + left
                #print 'Right : ' + matchName
                FileOperations.Copy(rightFolder + matchName, newRightFolder + left, 0, -1)
            else:
                missingFiles.append(left)

        missingCount = len(missingFiles)
        filesCreated = len(leftFiles) - missingCount
        if filesCreated == 0:
            MessageBox.ShowMessage('No file found!')
            return False
        if len(missingFiles) > 0:
            msg = 'Out of ' + str(len(leftFiles)) + ' file(s), '
            if missingCount > 1:
                msg += str(missingCount) + ' are'
            else:
                msg += '1 is'
            msg += ' missing.'
            MessageBox.ShowMessage(msg)
        return True

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
        left = left.lower()
        right = right.lower()
        left = left.replace("\'", "?")
        if len(left) != len(right):
            return False
        for l, r in zip(left, right):
            if l != "?" and l != r:
                return False
        return True

class GoldenReportComparerTest:
    def __init__(self):
        path = r'D:\CI\Src4\handler\tests\CDA\Mmi\SurfaceReport'
        self.comparer = GoldenReportComparer(self.CreateModel())
        self.TestAreSame()

    def CreateModel(self):
        class AutoTests:
            pass
        class Model:
            def __init__(self):
                self.AutoTests = AutoTests()
        model = Model()
        model.Source = r'D:\CI\Src4'
        model.AutoTests.TestName = r'CDA\Mmi\SurfaceReport'
        model.BCompare = ''
        return model

    def TestAreSame(self):
        a = r"batchAllRejects_pvi_'''.txt"
        b = r'batchAllRejects_pvi_cda.txt'
        Test.Assert(self.comparer.AreSame(a, b), True, 'Path 1')

        a = r'\ascii\PVI\batchAllRejects_pvi_cda.txt'
        b = r'\ascii\PVI\batchAllRejects_pvi_cda.txt'
        Test.Assert(self.comparer.AreSame(a, b), True, 'Path 2')

        a = "\ascii\csv\BatchName\machine_\'\'\'\'\'\'\'\'\'\'\'\'\'\'_BatchName.LIS"
        b = "\ascii\CSV\BatchName\machine_20170101000037_BatchName.LIS"
        Test.Assert(self.comparer.AreSame(a, b), True, 'Path 3')

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
