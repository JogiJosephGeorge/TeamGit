from Common.EffortLog import TestEffortLogger
from Common.NumValDict import TestNumValDict
from Common.PrettyTable import TestPrettyTable
from Common.Test import Test
from Test.TestKlaRunnerIni import TestKlaRunnerIni
from Test.TestSourceCode import TestSourceCode
from UI.UIAutoTestSettings_UT import FilterTestSelector_UT


class UnitTestsRunner:
    def Run(self):
        TestNumValDict()
        TestEffortLogger()
        TestPrettyTable()
        #TestSourceCode()
        TestKlaRunnerIni()
        FilterTestSelector_UT()

        Test.PrintResults()
