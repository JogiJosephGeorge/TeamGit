import inspect
import itertools
import os
import sys

from Common.NumValDict import TestNumValDict
from Common.PrettyTable import TestPrettyTable
from Model.Model import Model
from QuEST.EffortLog import TestEffortLogger


class Test:
    _ok = 0
    _notOk = 0

    @classmethod
    def AssertMultiLines(cls, actual, expected, level = 0):
        isEqual = True
        clsName, funName = cls._GetClassMethod(level)
        for lineNum,(act,exp) in enumerate(itertools.izip(actual.splitlines(), expected.splitlines()), 1):
            if act != exp:
                message = '{}.{} Line # {}'.format(clsName, funName, lineNum)
                cls._Print(act, exp, message)
                return
        message = '{}.{}'.format(clsName, funName)
        cls._Print(True, True, message)

    @classmethod
    def Assert(cls, actual, expected, message = '', level = 0):
        clsName, funName = cls._GetClassMethod(level)
        message = '{}.{} {}'.format(clsName, funName, message)
        cls._Print(actual, expected, message)

    @classmethod
    def _Print(cls, actual, expected, message):
        if actual == expected:
            print 'Test OK      : ' + message
            cls._ok += 1
        else:
            print 'Test Not OK : ' + message
            print 'Expected     : ' + str(expected)
            print 'Actual        : ' + str(actual)
            cls._notOk += 1

    @classmethod
    def _GetClassMethod(cls, level):
        stack = inspect.stack()
        clsName = stack[2 + level][0].f_locals['self'].__class__.__name__
        funName = stack[2 + level][0].f_code.co_name
        return (clsName, funName)

    @classmethod
    def PrintResults(cls):
        print
        print 'Tests OK      : ' + str(cls._ok)
        print 'Tests NOT OK : ' + str(cls._notOk)
        print 'Total Tests  : ' + str(cls._ok + cls._notOk)

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

class UnitTestsRunner:
    def Run(self):
        TestNumValDict()
        TestEffortLogger()
        TestPrettyTable()
        TestSourceCode()
        TestKlaRunnerIni()

        Test.PrintResults()

class TestKlaRunnerIni:
    def __init__(self):
        self.model = Model()
        self.model.ReadConfigFile()
        self.Source()
        self.AutoTest()
        self.FileExists()
        self.DirectoryExists()

    def Source(self):
        for srcSet in self.model.Sources:
            src = srcSet[0]
            Test.Assert(os.path.isdir(src), True, 'Directory {} exists.'.format(src))
        self.TestIndex(self.model.Sources, self.model.SrcIndex, 'Index')

    def AutoTest(self):
        self.TestIndex(self.model.AutoTests.Tests, self.model.TestIndex, 'Index')

    def TestIndex(self, list, index, message):
        isValidIndex = index >= 0 and index < len(list)
        Test.Assert(isValidIndex, True, message, 1)

    def FileExists(self):
        Test.Assert(os.path.isfile(self.model.DevEnvCom), True, 'DevEnv.com')
        Test.Assert(os.path.isfile(self.model.DevEnvExe), True, 'DevEnv.exe')
        Test.Assert(os.path.isfile(self.model.EffortLogFile), True, 'EffortLogFile')

    def DirectoryExists(self):
        Test.Assert(os.path.isdir(self.model.GitBin), True, 'GitBin')
        Test.Assert(os.path.isdir(self.model.VMwareWS), True, 'VMwareWS')
        Test.Assert(os.path.isdir(self.model.MMiConfigPath), True, 'MMiConfigPath')
        Test.Assert(os.path.isdir(self.model.MMiSetupsPath), True, 'MMiSetupsPath')
