import os
import sys

from Common.FileOperations import FileOperations
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from Common.StdOutRedirect import StdOutRedirect
from KLA.PreTestActions import PreTestActions
from KLA.TaskMan import TaskMan
from KLA.VMWareRunner import VMWareRunner
from KlaModel.ConfigEncoder import ConfigEncoder


class AutoTestRunner:
    def __init__(self, model, VM):
        self.model = model
        self.VM = VM
        self.lastSrc = None

    def InitAutoTest(self):
        if self.lastSrc is None:
            self.lastSrc = self.model.Source
        elif self.lastSrc != self.model.Source:
            msg = 'Test has already been executed with {}. So please restart KLA Runner.'.format(self.lastSrc)
            MessageBox.ShowMessage('KLA Runner', msg)
            return False
        TaskMan.StopTasks()
        return VMWareRunner.RunSlots(self.model)

    def RunAutoTest(self):
        testType = 'Start' if self.model.StartOnly else 'Run'
        Logger.Log('{} Auto Test {} in {}'.format(testType, self.model.TestName, self.model.Source))
        PreTestActions.ModifyVisionSystem(self.model)

        if self.model.GenerateLicMgrConfigOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            #PreTestActions.CopyMockLicense(self.model, False)
            PreTestActions.CopyLicMgrConfig(self.model, True)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model, True)

        #FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
        os.chdir(self.model.StartPath)

        # After swtiching sources with different configurations, we have to remove myconfig.py
        FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))

        libsPath = AutoTestRunner.UpdateLibsTestingPath(self.model.Source)
        tests = AutoTestRunner.SearchInTests(libsPath, self.model.TestName)
        if len(tests) == 0:
            return
        import my
        #print 'Module location of my : ' + my.__file__
        my.c.startup = self.model.StartOnly
        my.c.debugvision = self.model.DebugVision
        my.c.copymmi = self.model.CopyMmi
        my.c.mmiBuildConfiguration = ConfigEncoder.GetBuildConfig(self.model)
        my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
        my.c.platform = self.model.Platform
        my.c.mmiConfigurationsPath = self.model.MMiConfigPath
        my.c.mmiSetupsPath = self.model.MMiSetupsPath
        my.run(tests[0][0])
        if self.VM is not None:
            self.VM.UpdateSlots()
        print 'Completed Auto Test : {} : {}'.format(tests[0][0], tests[0][1])

    @classmethod
    def SearchInTests(cls, libsPath, text):
        sys.stdout = stdOutRedirect = StdOutRedirect()
        import my
        lineBreak = 'KLARunnerLineBreak'
        print lineBreak
        my.h.l(text)
        msgs = stdOutRedirect.ResetOriginal()
        inx = msgs.index(lineBreak)
        tests = []
        for msg in msgs[inx+1:]:
            arr = msg.split(':')
            if len(arr) == 2:
                tests.append([int(arr[0].strip()), arr[1].strip()])
        return tests

    @classmethod
    def GetTestName(cls, source, number):
        libsPath = cls.UpdateLibsTestingPath(source)
        tests = cls.SearchInTests(libsPath, number)
        if len(tests) > 0:
            return tests[0][1]
        return ''

    @classmethod
    def UpdateLibsTestingPath(cls, source):
        libsTesting = '/libs/testing'
        newPath = os.path.abspath(source + libsTesting)
        sys.path.append(newPath)
        return newPath
