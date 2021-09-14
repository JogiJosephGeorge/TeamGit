# coding=utf-8
import sys

from KLA.GoldenReportComparer import GoldenReportComparer
from KlaModel.Model import Model
from Test.UnitTestsRunner import UnitTestsRunner
from UI.UIGitLogViewer import UIGitLogViewer
from UI.UIMain import UIMain


def GetTempModel():
    model = Model()
    model.ReadConfigFile()
    return model

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


#CompareGolderReports()
main()
