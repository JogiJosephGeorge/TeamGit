from Common.OsOperations import OsOperations
from Common.UIFactory import UIFactory
from KLA.GoldenReportComparer import GoldenReportComparer
from KLA.VMWareRunner import VMWareRunner
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
        if self.model.UILevel < 3:
            self.AddVersion(row2, 0)

        row3 = UI.AddRow()
        self.col = 0
        UIFactory.AddLabel(row3, 'Slots', 0, self.col)
        self.col += 1
        self.AddSlots(row3, 0)
        UIFactory.AddButton(row3, 'Run Slots', 0, self.col, VMWareRunner.RunSlots, (self.model,))
        self.col += 1
        UIFactory.AddButton(row3, 'Test First Slot Selected', 0, self.col, VMWareRunner.TestSlots, (self.model,))
        self.col += 1

    def AddRunTestButton(self, parent, r, c):
        label = self.GetLabel()
        self.RunTestBut = self.threadHandler.AddButton(parent, label, r, c, self.tr.RunAutoTest, None, self.tr.InitAutoTest, self.tr.EndAutoTest)

    def GetLabel(self):
        return 'Start Test' if self.model.StartOnly else 'Run Test'

    def AddTestCombo(self, parent, r, c):
        testNames = self.model.AutoTests.GetNames()
        self.VM.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, r, c, self.VM.OnTestChanged, None, 70)

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
        self.model.WriteConfigFile()
        label = self.GetLabel()
        print label
        self.RunTestBut.config(text=label)

    def AddAttachMmi(self, parent, r):
        self.chkAttachMmi = UIFactory.AddCheckBox(parent, 'Attach MMi', self.model.DebugVision, r, self.col, self.OnAttach)
        self.col += 1

    def OnAttach(self):
        self.model.DebugVision = self.chkAttachMmi.get()
        self.model.WriteConfigFile()
        print 'Test Runner will ' + ['NOT ', ''][self.model.DebugVision] + 'wait for debugger to attach to testhost/mmi.'

    def AddVersion(self, parent, r):
        UIFactory.AddLabel(parent, 'MMi Setup Version', r, self.col)
        self.col += 1

        self.versions = ['Default'] + OsOperations.GetAllSubDir(self.model.MMiSetupsPath)
        verInx = 0
        if self.model.MMiSetupVersion in self.versions:
            verInx = self.versions.index(self.model.MMiSetupVersion)
        self.cmbVersions = UIFactory.AddCombo(parent, self.versions, verInx, r, self.col, self.OnVersionChanged, None, 10)
        self.col += 1
        self.VM.UpdateVersionCombo = self.UpdateVersionCombo

    def OnVersionChanged(self, event):
        index = self.cmbVersions.current()
        if index == 0:
            self.model.MMiSetupVersion = ''
            print 'MMI Setup Version changed to : Default'
        elif len(self.versions) > index:
            self.model.MMiSetupVersion = self.versions[index]
            print 'MMI Setup Version changed to : ' + self.model.MMiSetupVersion
        else:
            print 'MMI Setup Version Combo is NOT correct.'

    def UpdateVersionCombo(self):
        self.versions = ['Default'] + OsOperations.GetAllSubDir(self.model.MMiSetupsPath)
        verInx = 0
        if self.model.MMiSetupVersion in self.versions:
            verInx = self.versions.index(self.model.MMiSetupVersion)
        self.cmbVersions['values'] = self.versions
        self.cmbVersions.current(verInx)

    def AddSlots(self, parent, r):
        frame = UIFactory.AddFrame(parent, r, self.col)
        self.col += 1
        self.VM.chkSlots = []
        for i in range(self.model.MaxSlots):
            isSelected = (i+1) in self.model.slots
            txt = str(i+1)
            self.VM.chkSlots.append(UIFactory.AddCheckBox(frame, txt, isSelected, 0, i, self.OnSlotChn, (i,)))

    def OnSlotChn(self, index):
        self.model.UpdateSlot(index, self.VM.chkSlots[index].get())
        self.model.WriteConfigFile()
        print 'Slots for the current test : ' + str(self.model.slots)
