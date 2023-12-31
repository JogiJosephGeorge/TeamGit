import os
import sys

from KLA.TaskMan import TaskMan
from KLA.VMWareRunner import VMWareRunner


class UIViewModel:
    def __init__(self, model):
        self.model = model
        self.UpdateVersionCombo = None

    def StopTasks(self):
        TaskMan.StopTasks()
        VMWareRunner.RunSlots(self.model, False, False)

    @classmethod
    def RestartApp(cls, model):
        # This won't work when we execute the application using shortcut link
        # This works only when running from command prompt
        print 'Application Restarted.'
        argv = sys.argv
        if not os.path.exists(argv[0]):
            argv[0] = model.StartPath + '\\' + argv[0]
            #argv[0] = model.StartPath + '\\StartKLARunner.lnk'
        python = sys.executable
        os.execl(python, python, * argv)

    def UpdateSlotsChk(self, writeToFile):
        for i in range(self.model.MaxSlots):
            self.chkSlots[i].set((i+1) in self.model.AutoTests.slots)
        if writeToFile:
            self.model.WriteToFile()

    def OnCopyMmi(self):
        self.model.CopyMmi = self.chkCopyMmi.get()
        self.model.WriteToFile()
        print 'Copy MMi to ICOS : ' + str(self.chkCopyMmi.get())

    def UpdateCombo(self):
        tests = self.model.AutoTests.GetNames()
        self.cmbTest['values'] = tests
        if self.model.AutoTests.IsValidIndex(self.model.AutoTests.TestIndex):
            self.cmbTest.current(self.model.AutoTests.TestIndex)

    def OnTestChanged(self, event):
        if self.model.AutoTests.UpdateTest(self.cmbTest.current()):
            print 'Test Changed to : ' + self.model.AutoTests.TestName
            self.UpdateSlotsChk(True)

    def UpdateSlots(self):
        if VMWareRunner.SelectSlots(self.model):
            print 'Slots Updated : ' + str(self.model.AutoTests.slots)
            self.UpdateSlotsChk(True)
