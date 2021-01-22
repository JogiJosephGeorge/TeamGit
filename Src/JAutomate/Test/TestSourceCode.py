import inspect
import sys

from Common.Test import Test


class TestSourceCode:
    def __init__(self):
        self.TestClassLineCount()

    def TestClassLineCount(self):
        data = []
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj) and '__main__' in str(obj):
                lineCnt = len(inspect.getsourcelines(obj)[0])
                data.append([name, lineCnt])
        sorted(data, key=lambda x: x[1])
        for item in data:
            #Test.Assert(item[1] < 100, True, '{:20} {}'.format(item[0], item[1]))
            #print '{:20} {}'.format(item[0], item[1])
            if item[1] > 100:
                Test.Assert(item[1], '< 100', 'Exceeds line count : {}'.format(item[0]))