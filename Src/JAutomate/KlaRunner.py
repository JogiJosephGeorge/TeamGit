# coding=utf-8
import sys

from Test.UnitTestsRunner import UnitTestsRunner
from UI.UIMain import UIMain
from UI.UIGitLogViewer import UIGitLogViewer
from KlaModel.Model import Model
from KLA.GoldenReportComparer import GoldenReportComparer


def GetTempModel():
    model = Model()
    model.ReadConfigFile()
    return model

def ShowGitLog():
    UIGitLogViewer(None, GetTempModel()).Show()

def CompareGolderReports():
    testPath = r'C:\Users\1014769\Downloads\35149\CDA\Mmi\OutputBatchReelReport~1'
    comparer = GoldenReportComparer(GetTempModel())
    leftFolder = testPath + '/GoldenReports'
    rightFolder = testPath + '/_results'
    newRightFolder = testPath + '/NewGoldenReports'
    comparer.CopyAndCompareTestResults(leftFolder, rightFolder, newRightFolder)

def main():
    if len(sys.argv) == 2:
        param1 = sys.argv[1].lower()
        if param1 == 'test':
            UnitTestsRunner().Run()
    elif __name__ == '__main__':
        UIMain().Run()
        print 'Have a nice day...'


#ShowGitLog()
#CompareGolderReports()
main()
