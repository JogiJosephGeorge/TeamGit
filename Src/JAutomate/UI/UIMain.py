import ctypes
import os
import re

from KLA.AutoTestRunner import AutoTestRunner
from KLA.UIViewModel import UIViewModel

from Common.Git import Git
from Common.Logger import Logger
from Common.OsOperations import OsOperations
from Common.UIFactory import UIFactory
from KLA.PreTestActions2 import KlaRunner
from KLA.UIMainMenu import UIMainMenu
from KLA.UISourceGroup import UISourceGroup
from KLA.UITestGroup import UITestGroup
from KLA.VisualStudioSolutions import VisualStudioSolutions
from KlaModel.Model import Model
from UI.ThreadHandler import ThreadHandler
from UI.UISourceSelector import UISourceSelector


class UIMain:
    def Run(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raw_input('Please run this application with Administrator privilates')
            #os.system('PAUSE')
            return
        self.model = Model()
        self.VM = UIViewModel(self.model)
        self.model.ReadConfigFile()
        vsSolutions = VisualStudioSolutions(self.model)
        threadHandler = ThreadHandler()
        fileName = self.model.StartPath + '/' + self.model.LogFileName
        Logger.Init(fileName)
        klaRunner = KlaRunner(self.model)
        testRunner = AutoTestRunner(self.model, self.VM)

        title = 'KLA Application Runner'
        self.window = UIFactory.CreateWindow(None, title, self.model.StartPath)
        self.VM.window = self.window
        self.mainFrame = UIFactory.AddFrame(self.window, 0, 0, 20, 0)
        self.Row = 0
        UISourceGroup(self, klaRunner, vsSolutions, threadHandler)
        UITestGroup(self, klaRunner, vsSolutions, threadHandler, testRunner)
        UIMainMenu(self, klaRunner, vsSolutions, threadHandler, testRunner)

        self.window.after(200, self.LazyInit)
        self.window.mainloop()

    def LazyInit(self):
        title = 'KLA Application Runner ' + self.GetVersion()
        self.window.title(title)
        self.model.Branch = Git.GetBranch(self.model.Source)
        self.VM.lblBranch.set(self.model.Branch)
        Git.GitSilent('.', 'pull')
        print title

    def GetVersion(self):
        commitCnt = Git.ProcessOpen('rev-list --all --count')
        revision = int(re.sub('\W+', '', commitCnt)) - 165
        desStr = Git.ProcessOpen('describe --always')
        hash = re.sub('\W+', '', desStr)
        return '1.3.{}.{}'.format(revision, hash)

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddSeparator(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, ' ', 0, 0)
