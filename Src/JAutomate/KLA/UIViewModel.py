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
            self.chkSlots[i].set((i+1) in self.model.slots)
        if writeToFile:
            self.model.WriteConfigFile()

    def OnCopyMmi(self):
        self.model.CopyMmi = self.chkCopyMmi.get()
        self.model.WriteConfigFile()
        print 'Copy MMi to ICOS : ' + str(self.chkCopyMmi.get())

    def UpdateCombo(self):
        tests = self.model.AutoTests.GetNames()
        self.cmbTest['values'] = tests
        if self.model.AutoTests.TestIndex >= 0 and len(tests) > self.model.AutoTests.TestIndex:
            self.cmbTest.current(self.model.AutoTests.TestIndex)

    def OnTestChanged(self, event):
        if self.model.UpdateTest(self.cmbTest.current(), False):
            print 'Test Changed to : ' + self.model.TestName
            self.UpdateSlotsChk(True)

    def UpdateSlots(self):
        if VMWareRunner.SelectSlots(self.model):
            print 'Slots Updated : ' + str(self.model.slots)
            self.UpdateSlotsChk(True)
