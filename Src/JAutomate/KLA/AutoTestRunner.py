import os
import sys

from Common.FileOperations import FileOperations
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from Common.StdOutRedirect import StdOutRedirect
from KLA.PreTestActions import PreTestActions, SourceCodeUpdater
from KLA.TaskMan import TaskMan
from KLA.VMWareRunner import VMWareRunner
from KlaModel.ConfigEncoder import ConfigEncoder


class AutoTestRunner:
    def __init__(self, model, VM):
        self.model = model
        self.VM = VM
        self.lastSrc = None

    def InitAutoTest(self):
        curSrc = self.model.CurSrc()
        if self.lastSrc is None:
            self.lastSrc = curSrc.Source
        elif self.lastSrc != curSrc.Source:
            msg = 'Test has already been executed with {}. So please restart KLA Runner.'.format(self.lastSrc)
            MessageBox.ShowMessage(msg)
            return False
        TaskMan.StopTasks()
        return VMWareRunner.RunSlots(self.model)

    def RunAutoTest(self):
        curSrc = self.model.CurSrc()
        testType = 'Start' if self.model.StartOnly else 'Run'
        Logger.Log('{} Auto Test {} in {}'.format(testType, self.model.TestName, curSrc.Source))
        SourceCodeUpdater.ModifyVisionSystem(self.model)

        initWait = 15  # 8 is not working for CDA/Mmi/WithLead3D

        if self.model.GenerateLicMgrConfigOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.CopyMockLicense(self.model, False, initWait)
        if self.model.CopyLicMgrConfigOnTest:
            PreTestActions.CopyLicMgrConfig(self.model, initWait)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model, initWait)

        #FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
        os.chdir(self.model.StartPath)

        # After switching sources with different configurations, we have to remove myconfig.py
        FileOperations.Delete('{}/libs/testing/myconfig.py'.format(curSrc.Source))

        libsPath = AutoTestRunner.UpdateLibsTestingPath(curSrc.Source)
        self.tests = AutoTestRunner.SearchInTests(libsPath, self.model.TestName)
        if len(self.tests) == 0:
            return
        import my
        #print 'Module location of my : ' + my.__file__
        my.c.startup = self.model.StartOnly
        my.c.debugvision = self.model.DebugVision
        my.c.copymmi = self.model.CopyMmi
        my.c.mmiBuildConfiguration = ConfigEncoder.GetBuildConfig(self.model)
        my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
        my.c.platform = curSrc.Platform
        my.c.mmiConfigurationsPath = self.model.MMiConfigPath
        my.c.mmiSetupsPath = self.model.MMiSetupsPath
        version = self.model.MMiSetupVersion if self.model.MMiSetupVersion else ''
        my.run(self.tests[0][0], version=version)
        if self.VM is not None:
            self.VM.UpdateSlots()

    def EndAutoTest(self):
        msg = 'Completed Auto Test : {} : {}'.format(self.tests[0][0], self.tests[0][1])
        #MessageBox.ShowMessage(msg)
        print msg
        self.VM.window.focus_force()

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
