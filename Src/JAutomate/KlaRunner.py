# coding=utf-8
import sys

from Test.UnitTestsRunner import UnitTestsRunner
from UI.UIMain import UIMain
from UI.UIGitLogViewer import UIGitLogViewer
from KlaModel.Model import Model


def ShowGitLog():
    model = Model()
    model.ReadConfigFile()
    UIGitLogViewer(None, model).Show()

def main():
    if len(sys.argv) == 2:
        param1 = sys.argv[1].lower()
        if param1 == 'test':
            UnitTestsRunner().Run()
    elif __name__ == '__main__':
        UIMain().Run()
        print 'Have a nice day...'


#ShowGitLog()
main()
