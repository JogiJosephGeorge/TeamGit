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
        self.AddSelectPathRow(pathFrame, 'MMi Setups Path', 'MMiSetupsPath')
        self.AddSelectPathRow(pathFrame, 'MMi Config Path', 'MMiConfigPath')
        self.AddSelectFileRow(pathFrame, 'Effort Log File', 'EffortLogFile')
        self.AddSelectFileRow(pathFrame, 'DevEnv.com', 'DevEnvCom')
        self.AddSelectFileRow(pathFrame, 'DevEnv.exe', 'DevEnvExe')
        self.AddSelectPathRow(pathFrame, 'Git Path', 'GitPath')
        self.AddSelectFileRow(pathFrame, 'VMware.exe', 'VMwareExe')
        self.AddSelectFileRow(pathFrame, 'Beyond Compare', 'BCompare')

        self.checkFrame = UIFactory.AddFrame(parent, 1, 0)
        self.Row = 0
        self.CheckBoxes = dict()
        self.AddCheckBoxRow('Show All Commands in KlaRunner', 'ShowAllButtons', True, True)
        self.AddCheckBoxRow('Restart Slots while running MMi alone', 'RestartSlotsForMMiAlone', False, False)
        self.AddCheckBoxRow('Copy MMi to Icos On AutoTest', 'CopyMmi', False, True)
        self.AddCheckBoxRow('Generate LicMgrConfig.xml On AutoTest', 'GenerateLicMgrConfigOnTest', True, False)
        self.AddCheckBoxRow('Copy Mock License On AutoTest', 'CopyMockLicenseOnTest', True, False)
        self.AddCheckBoxRow('Copy xPort_IllumReference.xml on AutoTest', 'CopyExportIllumRefOnTest', True, False)

        self.AddBackButton(parent, 2, 0)
        self.messages = {
            'ShowAllButtons': ['You need to restart the application to update the UI.'] * 2,
            'RestartSlotsForMMiAlone': [
                'The selected slots will be restarted while running MMi alone.',
                'The selected slots will NOT be restarted while running MMi alone.'],
            'CopyMmi': [
                'Copy the mmi built over the installation in C:/icos.',
                'Do NOT copy the mmi built over the installation in C:/icos.\nThis is NOT RECOMMENDED.'],
            'GenerateLicMgrConfigOnTest': [
                'The file LicMgrConfig.xml will be created while running auto test.\nThis is NOT RECOMMENDED.',
                'The file LicMgrConfig.xml will NOT be created while running auto test.'],
            'CopyMockLicenseOnTest': [
                'The file mock License.dll will be copied while running auto test.\nThis is NOT RECOMMENDED.',
                'The file mock License.dll will NOT be copied while running auto test.'],
            'CopyExportIllumRefOnTest': [
                'The file xPort_IllumReference.xml will be copied while running auto test.\nThis is NOT RECOMMENDED.',
                'The file xPort_IllumReference.xml will NOT be copied while running auto test.']
        }

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

    def AddCheckBoxRow(self, txt, attrName, showMsgOnEnable, showMsgOnDisable):
        isChecked = getattr(self.model, attrName) # self.model.__dict__[modelVar] also works
        args = (attrName, showMsgOnEnable, showMsgOnDisable)
        self.CheckBoxes[attrName] = UIFactory.AddCheckBox(self.checkFrame, txt, isChecked, self.Row, 0, self.OnClickCheckBox, args)
        self.Row += 1

    def OnClickCheckBox(self, attrName, showMsgOnEnable, showMsgOnDisable):
        isChecked = self.CheckBoxes[attrName].get()
        setattr(self.model, attrName, isChecked)
        msg = self.messages[attrName][not isChecked]
        if (isChecked and showMsgOnEnable) or ((not isChecked) and showMsgOnDisable):
            MessageBox.ShowMessage(msg)
        else:
            print msg
