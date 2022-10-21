from Common.EffortLog import EffortLogger
from Common.Git import Git
from Common.Logger import Logger
from Common.OsOperations import OsOperations
from KLA.AppRunner import AppRunner
from KLA.JiraOpener import JiraOpener
from KLA.MmiSpcTestRunner import MmiSpcTestRunner
from KLA.PreTestActions import PreTestActions
from KLA.SpecialTextOperations import SpecialTextOperations
from KLA.UIGrid import UIGrid
from UI.UIGitLogViewer import UIGitLogViewer
from UI.UISettings import UISettings
from UI.UISolutionList import UISolutionList


class UIMainMenu:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, testRunner):
        self.window = UI.window
        self.VM = UI.VM
        self.OnSettingsClosed = UI.OnSettingsClosed
        self.model = klaRunner.model
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.testRunner = testRunner
        self.jiraOpener = JiraOpener(self.model)
        self.mmiSpcTestRunner = MmiSpcTestRunner(self.model)
        self.appRunner = AppRunner(self.model, testRunner, vsSolutions)

        UI.AddSeparator()

        self.uiGrid = UIGrid(UI.AddRow(), threadHandler)
        self.AddColumn1()
        self.AddColumn2()
        self.AddColumn3()
        self.AddColumn4()
        self.AddColumn5()

        UI.AddSeparator()

    def AddColumn1(self):
        self.uiGrid.CreateColumnFrame()
        self.uiGrid.AddButton('STOP All KLA Apps', self.StopTasks)
        if self.model.UserAccess.IsExpertUser():
            self.uiGrid.AddButton('STOP MMi alone', self.StopMMi)
            self.uiGrid.AddButton('Run Handler', self.RunHandler)
            self.uiGrid.AddButton('Run MMi from Source', self.RunMMi, (True,))
            self.uiGrid.AddButton('Run MMi from C:/Icos', self.RunMMi, (False,))
        self.uiGrid.AddButton('Run MMi SPC Tests', self.mmiSpcTestRunner.RunAllTests)

    def StopTasks(self):
        Logger.Log('STOP All KLA Apps')
        self.VM.StopTasks()

    def StopMMi(self):
        Logger.Log('STOP MMi alone')
        self.appRunner.StopMMi()

    def RunHandler(self):
        self.appRunner.RunHandler()

    def RunMMi(self, fromSrc):
        self.appRunner.RunMMi(fromSrc, self.model.RemoveStartedTXT)

    def AddColumn2(self):
        self.uiGrid.CreateColumnFrame()
        vsSolutions = self.vsSolutions
        self.uiGrid.AddButton('Open Python', self.klaRunner.OpenPython)
        for inx,sln in enumerate(self.vsSolutions.Solutions):
            label = 'Open ' + self.vsSolutions.GetSlnName(sln)
            self.uiGrid.AddButton(label, vsSolutions.OpenSolutionFile, (sln,))
        self.uiGrid.AddButton('Other Solutions', self.ShowOpenSolutionDlg)
        if self.model.UserAccess.IsExpertUser():
            self.uiGrid.AddButton('Open Jira Int Tests', self.jiraOpener.OpenIntegrationTests)
            self.uiGrid.AddButton('Open Jira Unit Tests', self.jiraOpener.OpenUnitTests)

    def ShowOpenSolutionDlg(self):
        UISolutionList(self.window, self.model, self.vsSolutions).Show()

    def OpenIntegrationTests(self):
        JiraOpener().OpenIntegrationTests(self.model.Branch)

    def AddColumn3(self):
        self.uiGrid.CreateColumnFrame()
        self.uiGrid.AddButton('Tortoise Git Diff', AppRunner.OpenLocalDif, (self.model,))
        if self.model.UserAccess.IsExpertUser():
            self.uiGrid.AddButton('Git GUI', Git.OpenGitGui, (self.model,))
            self.uiGrid.AddButton('Git Bash Console', Git.OpenGitBash, (self.model,))
        self.uiGrid.AddButton('Git Fetch Pull', Git.FetchPull, (self.model,))
        self.uiGrid.AddButton('Git Submodule Update', Git.SubmoduleUpdate, (self.model,))
        if self.model.UserAccess.IsDeveloper():
            self.uiGrid.AddButton('Git Log Viewer', self.ShowGitLogViewer)

    def ShowGitLogViewer(self):
        gitLogViewer = UIGitLogViewer(self.window, self.model)
        gitLogViewer.Show()

    def AddColumn4(self):
        if self.model.UserAccess.IsExpertUser():
            self.uiGrid.CreateColumnFrame()
            #self.uiGrid.AddButton('Run ToolLink Host', self.appRunner.RunToollinkHost)
            self.uiGrid.AddButton('Copy Mock License', PreTestActions.CopyMockLicense, (self.model,))
            self.uiGrid.AddButton('Copy xPort xml', PreTestActions.CopyxPortIllumRef, (self.model,))
            self.uiGrid.AddButton('Generate LicMgrConfig', PreTestActions.GenerateLicMgrConfig, (self.model,))
            self.uiGrid.AddButton('Copy LicMgrConfig', PreTestActions.CopyLicMgrConfig, (self.model,))
            self.uiGrid.AddButton('Copy MmiSaveLogs.exe', PreTestActions.CopyMmiSaveLogExe, (self.model,))

    def AddColumn5(self):
        self.uiGrid.CreateColumnFrame()
        effortLogger = EffortLogger()
        specialTextOps = SpecialTextOperations()
        self.uiGrid.AddButton('Settings', self.ShowSettings)
        if self.model.UserAccess.IsExpertUser():
            self.uiGrid.AddButton('Clear Output', OsOperations.Cls)
            self.uiGrid.AddButton('Print Missing IDs', self.klaRunner.PrintMissingIds)
        if self.model.UserAccess.IsDeveloper():
            self.uiGrid.AddButton('Effort Log', effortLogger.PrintEffortLogInDetail, (self.model.EffortLogFile,))
            self.uiGrid.AddButton('Daily Log', effortLogger.PrintDailyLog, (self.model.EffortLogFile,))
            self.uiGrid.AddButton('Convert Stack', specialTextOps.ConvertStack)

    def ShowSettings(self):
        uiSettings = UISettings(self.window, self.model, self.OnSettingsClosed)
        uiSettings.Show()
