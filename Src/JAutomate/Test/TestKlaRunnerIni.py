import os

from Common.Test import Test
from KlaModel.Model import Model


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