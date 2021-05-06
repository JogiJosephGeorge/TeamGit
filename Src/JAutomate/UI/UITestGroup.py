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
        self.AddStartOnly(row2, 0, 0)
        self.AddAttachMmi(row2, 0, 1)
        UIFactory.AddButton(row2, 'Open Test Folder', 0, 2, self.grComparer.OpenTestFolder)
        UIFactory.AddButton(row2, 'Compare Test Results', 0, 3, self.grComparer.CompareMmiReports)

        row3 = UI.AddRow()
        UIFactory.AddLabel(row3, 'Slots', 0, 0)
        self.AddSlots(row3, 0, 1)
        UIFactory.AddButton(row3, 'Run Slots', 0, 2, VMWareRunner.RunSlots, (self.model,))
        UIFactory.AddButton(row3, 'Test First Slot Selected', 0, 4, VMWareRunner.TestSlots, (self.model,))

    def AddRunTestButton(self, parent, r, c):
        label = self.GetLabel()
        self.RunTestBut = self.threadHandler.AddButton(parent, label, r, c, self.tr.RunAutoTest, None, self.tr.InitAutoTest, self.tr.EndAutoTest)

    def GetLabel(self):
        return 'Start Test' if self.model.StartOnly else 'Run Test'

    def AddTestCombo(self, parent, r, c):
        testNames = self.model.AutoTests.GetNames()
        self.VM.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, r, c, self.VM.OnTestChanged, None, 70)

    def AddAutoTestSettings(self, parent, r, c):
        UIFactory.AddButton(parent, ' ... ', r, c, self.ShowAutoTestSettings)

    def ShowAutoTestSettings(self):
        uiAutoTestSettings = UIAutoTestSettings(self.window, self.model, self.VM)
        uiAutoTestSettings.Show()

    def AddStartOnly(self, parent, r, c):
        self.chkStartOnly = UIFactory.AddCheckBox(parent, 'Start only', self.model.StartOnly, r, c, self.OnStartOnly)

    def OnStartOnly(self):
        self.model.StartOnly = self.chkStartOnly.get()
        self.model.WriteConfigFile()
        label = self.GetLabel()
        print label
        self.RunTestBut.config(text=label)

    def AddAttachMmi(self, parent, r, c):
        self.chkAttachMmi = UIFactory.AddCheckBox(parent, 'Attach MMi', self.model.DebugVision, r, c, self.OnAttach)

    def OnAttach(self):
        self.model.DebugVision = self.chkAttachMmi.get()
        self.model.WriteConfigFile()
        print 'Test Runner will ' + ['NOT ', ''][self.model.DebugVision] + 'wait for debugger to attach to testhost/mmi.'

    def AddSlots(self, parent, r, c):
        frame = UIFactory.AddFrame(parent, r, c)
        self.VM.chkSlots = []
        for i in range(self.model.MaxSlots):
            isSelected = (i+1) in self.model.slots
            txt = str(i+1)
            self.VM.chkSlots.append(UIFactory.AddCheckBox(frame, txt, isSelected, 0, i, self.OnSlotChn, (i,)))

    def OnSlotChn(self, index):
        self.model.UpdateSlot(index, self.VM.chkSlots[index].get())
        self.model.WriteConfigFile()
        print 'Slots for the current test : ' + str(self.model.slots)
