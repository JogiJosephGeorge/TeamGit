import os
import tkFileDialog

from Common.UIFactory import UIFactory
from Common.MessageBox import MessageBox
from UI.UIWindow import UIWindow


class UISettings(UIWindow):
    def __init__(self, parent, model):
        super(UISettings, self).__init__(parent, model, 'Settings')

    def CreateUI(self, parent):
        pathFrame = UIFactory.AddFrame(parent, 0, 0)
        self.Row = 0
        self.AddSelectFileRow(pathFrame, 'DevEnv.com', 'DevEnvCom')
        self.AddSelectFileRow(pathFrame, 'DevEnv.exe', 'DevEnvExe')
        self.AddSelectPathRow(pathFrame, 'Git Bin', 'GitBin')
        self.AddSelectPathRow(pathFrame, 'VM ware WS', 'VMwareWS')
        self.AddSelectFileRow(pathFrame, 'Effort Log File', 'EffortLogFile')
        self.AddSelectPathRow(pathFrame, 'MMi Config Path', 'MMiConfigPath')
        self.AddSelectPathRow(pathFrame, 'MMi Setups Path', 'MMiSetupsPath')

        self.checkFrame = UIFactory.AddFrame(parent, 1, 0)
        self.Row = 0
        self.CheckBoxes = dict()
        self.AddCheckBoxRow('Show All Commands in KlaRunner', 'ShowAllButtons', self.OnShowAll)
        self.AddCheckBoxRow('Restart Slots while running MMi alone', 'RestartSlotsForMMiAlone', self.OnRestartSlotsForMMi)
        self.AddCheckBoxRow('Copy MMi to Icos On AutoTest', 'CopyMmi', self.OnCopyMMiToIcosOnTest)
        self.AddCheckBoxRow('Generate LicMgrConfig.xml On AutoTest', 'GenerateLicMgrConfigOnTest', self.OnGenerateLicMgrConfigOnTest)
        self.AddCheckBoxRow('Copy Mock License On AutoTest', 'CopyMockLicenseOnTest', self.OnCopyMockLicenseOnTest)
        self.AddCheckBoxRow('Copy xPort_IllumReference.xml on AutoTest', 'CopyExportIllumRefOnTest', self.OnCopyExportIllumRefOnTest)

        self.AddBackButton(parent, 2, 0)

    def AddSelectPathRow(self, parent, label, attrName):
        self.AddSelectItemRow(parent, label, attrName, False)

    def AddSelectFileRow(self, parent, label, attrName):
        self.AddSelectItemRow(parent, label, attrName, True)

    def AddSelectItemRow(self, parent, label, attrName, isFile):
        UIFactory.AddLabel(parent, label, self.Row, 0)
        text = getattr(self.model, attrName)
        if isFile:
            if not os.path.isfile(text):
                print "Given file doesn't exist : " + text
            cmd = self.SelectFile
        else:
            if not os.path.isdir(text):
                print "Given directory doesn't exist : " + text
            cmd = self.SelectPath
        textVar = UIFactory.AddLabel(parent, text, self.Row, 1)
        args = (textVar, attrName)
        UIFactory.AddButton(parent, ' ... ', self.Row, 2, cmd, args)
        self.Row += 1

    def SelectPath(self, textVar, attrName):
        folderSelected = tkFileDialog.askdirectory()
        if len(folderSelected) > 0:
            textVar.set(folderSelected)
            setattr(self.model, attrName, folderSelected)
            print '{} Path changed : {}'.format(attrName, folderSelected)

    def SelectFile(self, textVar, attrName):
        filename = tkFileDialog.askopenfilename(initialdir = "/", title = "Select file")
        if len(filename) > 0:
            textVar.set(filename)
            setattr(self.model, attrName, filename)
            print '{} Path changed : {}'.format(attrName, filename)

    def AddCheckBoxRow(self, txt, attrName, FunPnt):
        isChecked = getattr(self.model, attrName) # self.model.__dict__[modelVar] also works
        args = (FunPnt, attrName)
        self.CheckBoxes[attrName] = UIFactory.AddCheckBox(self.checkFrame, txt, isChecked, self.Row, 0, self.OnClickCheckBox, args)
        self.Row += 1

    def OnClickCheckBox(self, FunPnt, attrName):
        setattr(self.model, attrName, self.CheckBoxes[attrName].get())
        FunPnt()

    def OnShowAll(self):
        MessageBox.ShowMessage('You need to restart the application to update the UI.')

    def OnRestartSlotsForMMi(self):
        msg = 'The selected slots will {}be restarted while running MMi alone.'
        if self.model.RestartSlotsForMMiAlone:
            print msg.format('')
        else:
            print msg.format('NOT ')

    def OnCopyMMiToIcosOnTest(self):
        if not self.model.CopyMmi:
            MessageBox.ShowMessage('Do NOT copy the mmi built over the installation in C:/icos.\nThis is NOT RECOMMENDED.')
        else:
            print 'Copy the mmi built over the installation in C:/icos.'

    def OnGenerateLicMgrConfigOnTest(self):
        if self.model.GenerateLicMgrConfigOnTest:
            MessageBox.ShowMessage('The file LicMgrConfig.xml will be created while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file LicMgrConfig.xml will NOT be created while running auto test.'

    def OnCopyMockLicenseOnTest(self):
        if self.model.CopyMockLicenseOnTest:
            MessageBox.ShowMessage('The file mock License.dll will be copied while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file mock License.dll will NOT be copied while running auto test.'

    def OnCopyExportIllumRefOnTest(self):
        if self.model.CopyExportIllumRefOnTest:
            MessageBox.ShowMessage('The file xPort_IllumReference.xml will be copied while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file xPort_IllumReference.xml will NOT be copied while running auto test.'
