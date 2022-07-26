# coding=utf-8
import sys

from Common.FileOperations import FileOperations
from KLA.GoldenReportComparer import GoldenReportComparer
from KLA.MmiLogReader import MmiLogReader
from KlaModel.Model import Model
from Test.UnitTestsRunner import UnitTestsRunner
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

def LogReader():
    MmiLogReader()

def main():
    if len(sys.argv) == 2:
        param1 = sys.argv[1].lower()
        if param1 == 'test':
            UnitTestsRunner().Run()
    elif __name__ == '__main__':
        UIMain().Run()
        print 'Have a nice day...'

# New Functionality
# Modify last fline of "C:\Mvs Message Analyzer\Preferences.ini"
# with content of "C:\MVS8000\slot1\software_link.cfg"

#CompareGolderReports()
main()
