import ctypes
import os
import re
import threading
from win32api import OutputDebugString

from Common.Git import Git
from Common.Logger import Logger
from Common.MessageBox import MessageBox
# from Common.PerformanceTester import PerformanceTester
from Common.UIFactory import UIFactory
from KLA.AutoTestRunner import AutoTestRunner
from KLA.PreTestActions import SourceCodeUpdater
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
        self.model = Model()
        self.model.ReadFromFile()
        fileName = self.model.StartPath + '/' + self.model.LogFileName
        Logger.Init(fileName)
        Logger.AddLogger(self.DebugViewLog)

        if not ctypes.windll.shell32.IsUserAnAdmin():
            msg = 'Please run this application with Administrator privilates'
            Logger.Log(msg)
            MessageBox.ShowMessage(msg)
            return

        klaRunner = KlaRunner(self.model)
        self.VM = UIViewModel(self.model)
        testRunner = AutoTestRunner(self.model, self.VM)

        title = 'KLA Application Runner'
        self.window = UIFactory.CreateWindow(None, title, self.model.StartPath)
        self.VM.window = self.window
        self.mainFrame = UIFactory.AddFrame(self.window, 0, 0, 20, 0)
        self.Row = 0
        vsSolutions = VisualStudioSolutions(self.model)
        threadHandler = ThreadHandler()
        self.uiSourceGroup = UISourceGroup(self, klaRunner, vsSolutions, threadHandler, self.OnSrcChanged)
        self.uiTestGroup = UITestGroup(self, klaRunner, vsSolutions, threadHandler, testRunner)
        UIMainMenu(self, klaRunner, vsSolutions, threadHandler, testRunner)

        self.model.Geometry.ReadGeomInfo(self.window, 'Main')
        self.window.protocol('WM_DELETE_WINDOW', self.OnClosing)
        self.window.after(200, self.LazyInit)
        self.window.mainloop()

    def OnSrcChanged(self):
        self.VM.UpdateVersionCombo()

    def DebugViewLog(self, message):
        OutputDebugString(self.model.LogName + message)

    def OnClosing(self):
        self.model.Geometry.WriteGeomInfo(self.window, 'Main')
        self.model.WriteToFile()
        self.window.destroy()

    def OnSettingsClosed(self):
        self.VM.UpdateVersionCombo()

    def LazyInit(self):
        class LazyData:
            def __init__(self):
                self.Version = ''
                self.Branch = ''
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
        self.uiSourceGroup.UpdateBranch()
        print title
        self.CheckLicense()
        SourceCodeUpdater.CopyPreCommit(self.model)

    def GetVersion(self):
        path = os.getcwd() + '/../../../.git'
        if not os.path.exists(path):
            return
        commitCnt = Git.ProcessOpen('rev-list master --count --no-merges')
        if not commitCnt:
            return
        revision = int(re.sub('\W+', '', commitCnt)) - 247

        desStr = Git.ProcessOpen('describe --always')
        if not desStr:
            return
        hash = re.sub('\W+', '', desStr)
        self.LazyData.Version = '1.4.{}.{}'.format(revision, hash)

    def GetBranch(self):
        curSrc = self.model.Src.GetCur()
        self.LazyData.Branch = Git.GetBranch(curSrc.Source)

    def CheckLicense(self):
        VMWareRunner.CheckLicense(self.model)

    def UpdateSource(self):
        if not os.path.exists('.git'):
            return
        Git.GitSilent('.', 'pull')

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddSeparator(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, ' ', 0, 0)
