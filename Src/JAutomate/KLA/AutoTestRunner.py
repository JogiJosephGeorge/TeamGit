import os
import sys
import imp
import threading
import time

from Common.FileOperations import FileOperations
from Common.Git import Git
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
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return False
        curSrc = self.model.Src.GetCur()
        if not os.path.exists(curSrc.Source):
            print 'The directory does not exist : ' + curSrc.Source
            return False
        if self.lastSrc is None:
            self.lastSrc = curSrc.Source
        elif self.lastSrc != curSrc.Source:
            if self.model.RestartAfterSrcChange:
                msg = 'Test has already been executed with {}. So please restart KLA Runner.'.format(self.lastSrc)
                MessageBox.ShowMessage(msg)
                return False
            else:
                AutoTestRunner.ReplaceLibsTestingPath(self.lastSrc, curSrc.Source)
            self.lastSrc = curSrc.Source
        TaskMan.StopTasks()
        return VMWareRunner.RunSlots(self.model)

    def RunAutoTest(self):
        curSrc = self.model.Src.GetCur()
        testType = 'Start' if self.model.StartOnly else 'Run'
        testName = self.model.AutoTests.TestName
        commitId = Git.GetCommitId(curSrc.Source)
        mmiSetup = curSrc.MMiSetupVersion
        Logger.Log('{} Auto Test {} in {} ({}) {}'.format(testType, testName, curSrc.Source, commitId, mmiSetup))
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
        if self.model.CopyMVSDConversionOnTest:
            PreTestActions.CopyMVSDConversion(self.model, initWait)

        #FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
        os.chdir(self.model.StartPath)

        # After switching sources with different configurations, we have to remove myconfig.py
        FileOperations.Delete('{}/libs/testing/myconfig.py'.format(curSrc.Source))
        FileOperations.Delete('{}/libs/testing/myconfig.pyc'.format(curSrc.Source))

        libsPath = AutoTestRunner.UpdateLibsTestingPath(curSrc.Source)
        my = self.LoadMyModule(curSrc.Source)
        self.tests = AutoTestRunner.SearchInTests(my, libsPath, self.model.AutoTests.TestName)
        if len(self.tests) == 0:
            print 'Test is not available'
            return

        print 'Module location of my : ' + my.__file__
        my.c.debugvision = self.model.DebugVision
        my.c.prompt = self.model.PromptOnTestFail
        my.c.startup = self.model.StartOnly
        buildConfig = ConfigEncoder.GetBuildConfig(self.model)
        if self.model.ConsoleFromCHandler:
            my.c.console_config = 'm'
        else:
            my.c.console_config = buildConfig[0]
        my.c.simulator_config = buildConfig[0]
        my.c.removeOldCopies = self.model.removeOldCopies
        my.c.copymmi = self.model.CopyMmi
        my.c.mmiBuildConfiguration = buildConfig
        my.c.mmiConfigurationsPath = self.model.MMiConfigPath
        my.c.platform = curSrc.Platform
        my.c.mmiSetupsPath = self.model.MMiSetupsPath
        my.c.installerShare = ''

        print '\n' * 10 + '*' * 30 + ' Running Auto Test ' + '*' * 30 + '\n' * 5
        print my.c
        testNum = self.tests[0][0]
        if curSrc.MMiSetupVersion:
            print 'run(' + str(testNum) + ', version="' + str(curSrc.MMiSetupVersion) + '")'
            my.run(testNum, version=curSrc.MMiSetupVersion)
        else:
            print 'run(' + str(testNum) + ')'
            my.run(testNum)
        if self.VM is not None:
            self.VM.UpdateSlots()

    def EndAutoTest(self):
        msg = 'Completed Auto Test : {} : {}'.format(self.tests[0][0], self.tests[0][1])
        #MessageBox.ShowMessage(msg)
        print msg
        self.VM.window.focus_force()

    def LoadMyModule(self, source):
        #sys.stdout = stdOutRedirect = StdOutRedirect()
        myPyFileName = '{}/libs/testing/my.py'.format(source)
        myMod = imp.load_source('my', myPyFileName)
        #stdOutRedirect.ResetOriginal()
        return myMod

    @classmethod
    def SearchInTests(cls, myMod, libsPath, text):
        sys.stdout = stdOutRedirect = StdOutRedirect()
        lineBreak = 'KLARunnerLineBreak'
        print lineBreak
        myMod.h.l(text)
        msgs = stdOutRedirect.ResetOriginal()
        inx = msgs.index(lineBreak)
        tests = []
        for msg in msgs[inx+1:]:
            arr = msg.split(':')
            if len(arr) == 2:
                tests.append([int(arr[0].strip()), arr[1].strip()])
        return tests

    @classmethod
    def UpdateLibsTestingPath(cls, source):
        libsTesting = '/libs/testing'
        newPath = os.path.abspath(source + libsTesting)
        sys.path.append(newPath)
        return newPath

    @classmethod
    def ReplaceLibsTestingPath(cls, lastSrc, source):
        lastSrc = lastSrc.replace('/', '\\')
        a = lastSrc + u'\\libs\\testing'
        sys.path.remove(a)
        b = str(lastSrc + u'\\libs\\testing\\..\\..\\handler/scripts')
        sys.path.remove(b)

        source = source.replace('/', '\\')
        a = source + u'\\libs\\testing'
        sys.path.append(a)
        b = str(source + u'\\libs\\testing\\..\\..\\handler/scripts')
        sys.path.append(b)

        keys = []
        for key in sys.modules:
            mo = sys.modules[key]
            if mo:
                if 'libs\\testing' in str(mo):
                    print 'Unloading module : ' + str(sys.modules[key])
                    keys.append(key)
        for key in keys:
            del sys.modules[key]
