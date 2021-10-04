import inspect
import itertools


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
            print 'Test ok      : ' + message
            cls._ok += 1
        else:
            print 'TEST NOT OK  : ' + message
            print 'Expected     : ' + str(expected)
            print 'Actual       : ' + str(actual)
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