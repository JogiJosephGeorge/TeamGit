import os

from Common.Test import Test
from KlaModel.Model import Model


class TestKlaRunnerIni:
    def __init__(self):
        self.model = Model()
        self.model.ReadFromFile()
        self.Source()
        self.AutoTest()
        self.FileExists()
        self.DirectoryExists()

    def Source(self):
        srcs = list(self.model.Src.GetAllSrcs())
        for src in srcs:
            Test.Assert(os.path.isdir(src.Source), True, 'Directory {} exists.'.format(src.Source))
        self.DoTestIndex(srcs, self.model.Src.SrcIndex, 'Index')

    def AutoTest(self):
        self.VerifyNamesAndSlots(self.model.AutoTests.Tests)
        self.DoTestIndex(self.model.AutoTests.Tests, self.model.AutoTests.TestIndex, 'Index')

    def VerifyNamesAndSlots(self, list):
        for testName, slots in list:
            Test.Assert(len(testName) > 0, True, 'Test Name : ' + testName, 1)
            Test.Assert(len(slots) > 0, True, 'Slots selected for ' + testName, 1)
            for slot in slots:
                Test.Assert(slot > 0 and slot <= self.model.MaxSlots, True, 'Test Name {} Slot {}'.format(testName, slot), 1)

    def DoTestIndex(self, list, index, message):
        if len(list) == 0:
            Test.Assert(index, -1, message, 1)
        else:
            isValidIndex = index >= 0 and index < len(list)
            Test.Assert(isValidIndex, True, message, 1)

    def FileExists(self):
        Test.Assert(os.path.isfile(self.model.VsVersions.DevEnvCom), True, 'DevEnv.com')
        Test.Assert(os.path.isfile(self.model.VsVersions.DevEnvExe), True, 'DevEnv.exe')
        Test.Assert(os.path.isfile(self.model.VsVersions.DevEnvCom22), True, 'DevEnv.com')
        Test.Assert(os.path.isfile(self.model.VsVersions.DevEnvExe22), True, 'DevEnv.exe')
        Test.Assert(os.path.isfile(self.model.EffortLogFile), True, 'EffortLogFile')
        Test.Assert(os.path.isfile(self.model.VMwareExe), True, 'VMwareExe')
        Test.Assert(os.path.isfile(self.model.BCompare), True, 'BCompare')

    def DirectoryExists(self):
        Test.Assert(os.path.isdir(self.model.GitPath), True, 'GitPath')
        Test.Assert(os.path.isdir(self.model.MMiConfigPath), True, 'MMiConfigPath')
        Test.Assert(os.path.isdir(self.model.MMiSetupsPath), True, 'MMiSetupsPath')
