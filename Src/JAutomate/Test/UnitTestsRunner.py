from Common.EffortLog import TestEffortLogger
from Common.NumValDict import TestNumValDict
from Common.PrettyTable import TestPrettyTable
from Common.Test import Test
from KLA.GoldenReportComparer import GoldenReportComparerTest
from Test.TestKlaRunnerIni import TestKlaRunnerIni
from Test.TestSourceCode import TestSourceCode


class UnitTestsRunner:
    def Run(self):
        TestNumValDict()
        TestEffortLogger()
        TestPrettyTable()
        TestSourceCode()
        TestKlaRunnerIni()
        GoldenReportComparerTest()

        Test.PrintResults()
