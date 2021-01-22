# coding=utf-8
import sys

from Test.UnitTestsRunner import UnitTestsRunner
from UI.UIMain import UIMain


def main():
    if len(sys.argv) == 2:
        param1 = sys.argv[1].lower()
        if param1 == 'test':
            UnitTestsRunner().Run()
    elif __name__ == '__main__':
        UIMain().Run()
        print 'Have a nice day...'


main()
