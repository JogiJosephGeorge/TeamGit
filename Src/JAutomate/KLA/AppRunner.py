import os
import subprocess
import sys

from Common.Logger import Logger
from Common.OsOperations import OsOperations
from KLA.PreTestActions import PreTestActions
from KLA.TaskMan import TaskMan
from KLA.VMWareRunner import VMWareRunner


class AppRunner:
    def __init__(self, model, testRunner, vsSolutions):
        self.model = model
        self.testRunner = testRunner
        self.vsSolutions = vsSolutions

    def RunHandler(self):
        Logger.Log('Run Handler in ' + self.model.Source)
        TaskMan.StopTasks()

        handlerPath,consoleExe = self.vsSolutions.GetHandlerPath()
        testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'

        simulatorExe = self.vsSolutions.GetSimulatorPath()

        for file in [consoleExe, testTempDir, simulatorExe]:
            if not os.path.exists(file):
                print 'File not found : ' + file
                return

        OsOperations.System('start ' + consoleExe + ' ' + testTempDir)
        OsOperations.System('start {} {} {}'.format(simulatorExe, testTempDir, handlerPath))

    def StopMMi(self):
        TaskMan.StopTask('MMi.exe')
        VMWareRunner.RunSlots(self.model)

    def RunMMi(self, fromSrc):
        if self.model.RestartSlotsForMMiAlone:
            self.StopMMi()

        mmiPath = PreTestActions.GetMmiPath(self.model, fromSrc)
        Logger.Log('Run MMi from ' + mmiPath)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.CopyMockLicense(self.model, fromSrc)
            PreTestActions.CopyLicMgrConfig(self.model, False)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model)
        if self.model.RestartSlotsForMMiAlone:
            OsOperations.Timeout(8)

        mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')
        if not os.path.exists(mmiExe):
            print 'File not found : ' + mmiExe
            return

        OsOperations.System('start ' + mmiExe)

    def RunHandlerMMi(self):
        self.RunHandler()
        self.RunMMi(True)

    def RunToollinkHost(self):
        sys.path.append('C:\Handler\\testing')
        import handlerprocesses
        from generated.handlerSystem import ActionIds

        fabLinkPath = self.model.Source + '\handler\FabLink'
        processes = handlerprocesses.HandlerProcesses('', '', '', fabLinkPath)
        processes.secshost.start()
        OsOperations.Timeout(10)

        #visionApplications = ['BBI/Surface1: OFF', 'TopPVI/Mark: ON', 'TopPVI/Surface1: ON', 'TopPVI/Surface2: OFF']
        #visionApplications = ['Top Spectrum Plus/Mark: OFF', 'Top Spectrum Plus/Data Matrix: ON','Top Spectrum Plus/Alignment based Combined Surf:ON','Top Spectrum Plus/Alignment based Surface*:OFF','Bottom Spectrum Plus/Mark:OFF','Top Spectrum Plus/Pin 1:OFF','Top Spectrum Plus/Empty Pocket:OFF']
        #visionApplications = ['BGA: ON']
        visionApplications = ["LeadLess/*: ON"]
        #visionApplications= ['SMI/Pin*: ON']
        #ppidList=['/component/test', '/handler/test']
        ppSelectParams = {
            'PPID' : 'test',
            #'PASS-DESTINATION': 'TAPE',
            'VISION-APPLICATIONS' : visionApplications,
            #'PPID-LIST' : ppidList,
        }
        processes.secshost.proxy.runHostCommandSend(remoteCommand=ActionIds.PP_SELECT, commandParameters=ppSelectParams, waitForAnswer=True, enhanced=True)

    @classmethod
    def OpenLocalDif(cls, model):
        par = [ 'TortoiseGitProc.exe', '/command:diff', '/path:' + model.Source + '' ]
        print 'subprocess.Popen : ' + str(par)
        subprocess.Popen(par)
