from Common.EffortLog import TestEffortLogger
from Common.NumValDict import TestNumValDict
from Common.PrettyTable import TestPrettyTable
from Common import Test
from Test import TestKlaRunnerIni
from Test import TestSourceCode


class UnitTestsRunner:
    def Run(self):
        TestNumValDict()
        TestEffortLogger()
        TestPrettyTable()
        TestSourceCode()
        TestKlaRunnerIni()

        Test.PrintResults()
