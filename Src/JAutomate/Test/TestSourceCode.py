import inspect
import os
import sys

from Common.Test import Test


class TestSourceCode:
    def __init__(self):
        self.TestClassLineCount()

    def TestClassLineCount(self):
        for name, lineCnt in self.GetAllClasses():
            #Test.Assert(lineCnt < 100, True, '{:20} {}'.format(name, lineCnt))
            #print '{:20} {}'.format(name, lineCnt)
            if lineCnt > 150:
                Test.Assert(lineCnt, '< 150', 'Exceeds line count : {}'.format(name))

    def GetAllClasses(self):
        for modName in self.GetModules():
            #print modName
            for name, lineCnt in self.GetClasses(modName):
                yield (name, lineCnt)

    def GetModules(self):
        baseDir = os.path.dirname(os.path.dirname(__file__))
        left = len(baseDir) + 1
        for root, dirs, files in os.walk(baseDir):
            pkg = root[left:].replace('\\', '.')
            if len(pkg) > 0:
                pkg += '.'
                for file in files:
                    if file[-3:] == '.py' and not file == '__init__.py':
                        yield pkg + file[:-3]

    def GetClasses(self, modName):
        __import__(modName)
        for name, obj in inspect.getmembers(sys.modules[modName], inspect.isclass):
            if obj.__module__ == modName:
                lineCnt = len(inspect.getsourcelines(obj)[0])
                yield (name, lineCnt)
        del modName
