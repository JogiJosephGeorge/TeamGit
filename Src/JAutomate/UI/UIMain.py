import ctypes
import re
import threading

from Common.Git import Git
from Common.Logger import Logger
# from Common.PerformanceTester import PerformanceTester
from Common.UIFactory import UIFactory
from KLA.AutoTestRunner import AutoTestRunner
from KLA.PreTestActions2 import KlaRunner
from KLA.UIViewModel import UIViewModel
from KLA.VMWareRunner import VMWareRunner
from KLA.VisualStudioSolutions import VisualStudioSolutions
from KlaModel.Model import Model
from UI.ThreadHandler import ThreadHandler
from UI.UIMainMenu import UIMainMenu
from UI.UISourceGroup import UISourceGroup
from UI.UITestGroup import UITestGroup


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
        class LazyData:
            pass
        self.LazyData = LazyData()
        threads = []
        threads.append(threading.Thread(target=self.GetVersion))
        threads.append(threading.Thread(target=self.GetBranch))
        threads.append(threading.Thread(target=self.UpdateSource))

        [t.start() for t in threads]
        [t.join() for t in threads]

        title = 'KLA Application Runner ' + self.LazyData.Version
        self.window.title(title)
        self.model.Branch = self.LazyData.Branch
        self.VM.lblBranch.set(self.model.Branch)
        print title
        self.CheckLicense()

    def GetVersion(self):
        commitCnt = Git.ProcessOpen('rev-list master --count --no-merges')
        revision = int(re.sub('\W+', '', commitCnt)) - 160
        desStr = Git.ProcessOpen('describe --always')
        hash = re.sub('\W+', '', desStr)
        self.LazyData.Version = '1.3.{}.{}'.format(revision, hash)

    def GetBranch(self):
        self.LazyData.Branch = Git.GetBranch(self.model.Source)

    def CheckLicense(self):
        VMWareRunner.CheckLicense(self.model)

    def UpdateSource(self):
        Git.GitSilent('.', 'pull')

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddSeparator(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, ' ', 0, 0)
