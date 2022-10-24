from Common.OsOperations import OsOperations
from Common.UIFactory import UIFactory
from KLA.GoldenReportComparer import GoldenReportComparer
from KLA.VMWareRunner import VMWareRunner
from KlaModel.VsVersions import VsVersions
from UI.UIAutoTestSettings import UIAutoTestSettings


class UITestGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, tr):
        self.window = UI.window
        self.parent = UI.window
        self.model = UI.model
        self.VM = UI.VM
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler
        self.tr = tr
        self.grComparer = GoldenReportComparer(self.model)

        UI.AddSeparator()

        row1 = UI.AddRow()

        if not self.model.NoAutoTest:
            self.AddRunTestButton(row1, 0, 0)
        self.AddTestCombo(row1, 0, 1)
        self.AddAutoTestSettings(row1, 0, 2)

        row2 = UI.AddRow()
        self.col = 0
        self.AddStartOnly(row2, 0)
        self.AddAttachMmi(row2, 0)
        UIFactory.AddButton(row2, 'Open Test Folder', 0, self.col, self.grComparer.OpenTestFolder)
        self.col += 1
        UIFactory.AddButton(row2, 'Compare Test Results', 0, self.col, self.grComparer.CompareMmiReports)
        self.col += 1
        if self.model.UserAccess.IsExpertUser():
            self.AddSetupVersion(row2, 0)
            self.AddVSVersion(row2, 0)

        row3 = UI.AddRow()
        self.col = 0
        UIFactory.AddLabel(row3, 'Slots', 0, self.col)
        self.col += 1
        self.AddSlots(row3, 0)
        UIFactory.AddButton(row3, 'Run Slots', 0, self.col, VMWareRunner.RunSlots, (self.model,))
        self.col += 1
        label = self.GetSlotLabel()
        self.TestSlotBut = UIFactory.AddButton(row3, label, 0, self.col, VMWareRunner.TestSlots, (self.model,))
        self.col += 1

    def AddRunTestButton(self, parent, r, c):
        label = self.GetLabel()
        self.RunTestBut = self.threadHandler.AddButton(parent, label, r, c, self.tr.RunAutoTest, None, self.tr.InitAutoTest, self.tr.EndAutoTest)

    def GetLabel(self):
        return 'Start Test' if self.model.StartOnly else 'Run Test'

    def AddTestCombo(self, parent, r, c):
        testNames = self.model.AutoTests.GetNames()
        testIndex = self.model.AutoTests.TestIndex
        self.VM.cmbTest = UIFactory.AddCombo(parent, testNames, testIndex, r, c, self.VM.OnTestChanged, None, 70)

    def AddAutoTestSettings(self, parent, r, c):
        UIFactory.AddButton(parent, ' + ', r, c, self.ShowAutoTestSettings)

    def ShowAutoTestSettings(self):
        uiAutoTestSettings = UIAutoTestSettings(self.window, self.model, self.VM)
        uiAutoTestSettings.Show()

    def AddStartOnly(self, parent, r):
        self.chkStartOnly = UIFactory.AddCheckBox(parent, 'Start only', self.model.StartOnly, r, self.col, self.OnStartOnly)
        self.col += 1

    def OnStartOnly(self):
        self.model.StartOnly = self.chkStartOnly.get()
        self.model.WriteToFile()
        label = self.GetLabel()
        print label
        self.RunTestBut.config(text=label)

    def AddAttachMmi(self, parent, r):
        self.chkAttachMmi = UIFactory.AddCheckBox(parent, 'Attach MMi', self.model.DebugVision, r, self.col, self.OnAttach)
        self.col += 1

    def OnAttach(self):
        self.model.DebugVision = self.chkAttachMmi.get()
        self.model.WriteToFile()
        print 'Test Runner will ' + ['NOT ', ''][self.model.DebugVision] + 'wait for debugger to attach to testhost/mmi.'

    def AddSetupVersion(self, parent, r):
        UIFactory.AddLabel(parent, 'MMi Setup Version', r, self.col)
        self.col += 1

        self.versions = ['Default'] + OsOperations.GetAllSubDir(self.model.MMiSetupsPath)
        verInx = 0
        curSrc = self.model.Src.GetCur()
        if curSrc.MMiSetupVersion in self.versions:
            verInx = self.versions.index(curSrc.MMiSetupVersion)
        self.cmbVersions = UIFactory.AddCombo(parent, self.versions, verInx, r, self.col, self.OnSetupVerChanged, None, 10)
        self.col += 1
        self.VM.UpdateVersionCombo = self.UpdateVersionCombo

    def OnSetupVerChanged(self, event):
        index = self.cmbVersions.current()
        curSrc = self.model.Src.GetCur()
        if index == 0:
            curSrc.MMiSetupVersion = ''
            print 'MMI Setup Version changed to : Default'
        elif len(self.versions) > index:
            curSrc.MMiSetupVersion = self.versions[index]
            print 'MMI Setup Version changed to : ' + curSrc.MMiSetupVersion
        else:
            print 'MMI Setup Version Combo is NOT correct.'

    def UpdateVersionCombo(self):
        self.versions = ['Default'] + OsOperations.GetAllSubDir(self.model.MMiSetupsPath)
        verInx = 0
        curSrc = self.model.Src.GetCur()
        if curSrc.MMiSetupVersion in self.versions:
            verInx = self.versions.index(curSrc.MMiSetupVersion)
        self.cmbVersions['values'] = self.versions
        self.cmbVersions.current(verInx)

        verInx = VsVersions().GetIndex(curSrc.VsVersion)
        self.cmbVsVersions.current(verInx)

    def AddVSVersion(self, parent, r):
        UIFactory.AddLabel(parent, 'Visual Studio', r, self.col)
        self.col += 1

        vsVersions = VsVersions()
        curSrc = self.model.Src.GetCur()
        verInx = vsVersions.GetIndex(curSrc.VsVersion)
        self.cmbVsVersions = UIFactory.AddCombo(parent, vsVersions.GetAll(), verInx, r, self.col, self.OnVsVerChanged, None, 5)
        self.col += 1
        self.VM.UpdateVersionCombo = self.UpdateVersionCombo

    def OnVsVerChanged(self, event):
        index = self.cmbVsVersions.current()
        curSrc = self.model.Src.GetCur()
        curSrc.VsVersion = VsVersions().GetAll()[index]
        print 'MMI Setup Version changed to : ' + curSrc.VsVersion

    def AddSlots(self, parent, r):
        frame = UIFactory.AddFrame(parent, r, self.col)
        self.col += 1
        self.VM.chkSlots = []
        for i in range(self.model.MaxSlots):
            isSelected = (i+1) in self.model.AutoTests.slots
            txt = str(i+1)
            self.VM.chkSlots.append(UIFactory.AddCheckBox(frame, txt, isSelected, 0, i, self.OnSlotChn, (i,)))

    def OnSlotChn(self, index):
        self.model.AutoTests.UpdateSlot(index, self.VM.chkSlots[index].get())
        self.model.WriteToFile()
        print 'Slots for the current test : ' + str(self.model.AutoTests.slots)

        label = self.GetSlotLabel()
        self.TestSlotBut.config(text=label)

    def GetSlotLabel(self):
        if len(self.model.AutoTests.slots) > 0:
            return 'Test ' + str(self.model.AutoTests.slots[0])
        return 'Test None'
