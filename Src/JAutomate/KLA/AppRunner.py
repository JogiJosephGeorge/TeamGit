import os
import subprocess
import sys

from Common.FileOperations import FileOperations
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from KLA.IcosPaths import IcosPaths
from KLA.PreTestActions import PreTestActions
from KLA.TaskMan import TaskMan
from KLA.VMWareRunner import VMWareRunner


class AppRunner:
    def __init__(self, model, testRunner, vsSolutions):
        self.model = model
        self.testRunner = testRunner
        self.vsSolutions = vsSolutions

    def RunHandler(self):
        curSrc = self.model.CurSrc()
        Logger.Log('Run Handler in ' + curSrc.Source)
        TaskMan.StopTasks()

        runFromCHandler = self.model.ConsoleFromCHandler
        consoleExe = IcosPaths.GetConsolePath(curSrc.Source, curSrc.Platform, curSrc.Config, runFromCHandler)
        simulatorExe = IcosPaths.GetSimulatorPath(curSrc.Source, curSrc.Platform, curSrc.Config, runFromCHandler)
        EXEs = [consoleExe, simulatorExe]
        handlerPath = ''
        testTempDir = ''
        if not runFromCHandler:
            handlerPath = IcosPaths.GetHandlerPath(curSrc.Source, curSrc.Platform, curSrc.Config, False)
            testTempDir = IcosPaths.GetTestPathTemp(curSrc.Source, self.model.AutoTests.TestName)
            EXEs.append(testTempDir)

        for file in EXEs:
            if not os.path.exists(file):
                MessageBox.ShowMessage('File not found : ' + file)
                return

        OsOperations.System('start ' + consoleExe + ' ' + testTempDir)
        OsOperations.System('start {} {} {}'.format(simulatorExe, testTempDir, handlerPath))

    def RunHostCam(self):
        fileName = FileOperations.ReadLine('C:/MVS8000/slot1/software_link.cfg', 'utf-8')[0]
        fileName += '/hostsw/hostcam/HostCamServer.exe'
        OsOperations.System('start ' + fileName)

    def StopMMi(self):
        TaskMan.StopTask('MMi.exe')
        VMWareRunner.RunSlots(self.model)

    def RunMMi(self, fromSrc, removePrevInst):
        if self.model.RestartSlotsForMMiAlone:
            self.StopMMi()

        if removePrevInst:
            FileOperations.Delete('C:/icos/started.txt')

        if self.model.RunHostCam:
            self.RunHostCam()

        mmiPath = PreTestActions.GetMmiPath(self.model, fromSrc)
        Logger.Log('Run MMi from ' + mmiPath)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.CopyMockLicense(self.model, fromSrc)
            PreTestActions.CopyLicMgrConfig(self.model, 0)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model)
        if self.model.RestartSlotsForMMiAlone:
            OsOperations.Timeout(8)

        mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')
        if not os.path.exists(mmiExe):
            MessageBox.ShowMessage('File not found : ' + mmiExe)
            return

        OsOperations.System('start ' + mmiExe)

    def RunHandlerMMi(self):
        self.RunHandler()
        self.RunMMi(True, False)

    def RunToollinkHost(self):
        sys.path.append(r'C:\Handler\testing')
        import handlerprocesses
        from generated.handlerSystem import ActionIds

        curSrc = self.model.CurSrc()
        fabLinkPath = curSrc.Source + '\handler\FabLink'
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
        curSrc = model.CurSrc()
        par = [ 'TortoiseGitProc.exe', '/command:diff', '/path:' + curSrc.Source + '' ]
        print 'Tortoise Git Diff : ' + str(curSrc.Source)
        subprocess.Popen(par)
