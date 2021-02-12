import os
import tkFileDialog

from Common.UIFactory import UIFactory, CheckBoxCreator
from UI.UIWindow import UIWindow


class UISettings(UIWindow):
    def __init__(self, parent, model):
        super(UISettings, self).__init__(parent, model, 'Settings')

    def CreateUI(self, parent):
        self.checkBoxCreator = CheckBoxCreator()
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

        checkFrame = UIFactory.AddFrame(parent, 1, 0)
        self.Row = 0
        msgOn = msgOff = 'You need to restart the application to update the UI.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 0, 0, 'Show All Commands in KlaRunner', self.model, 'ShowAllButtons', msgOn, msgOff, True, True)
        msgOn = 'The selected slots will be restarted while running MMi alone.'
        msgOff = 'The selected slots will NOT be restarted while running MMi alone.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 1, 0, 'Restart Slots while running MMi alone', self.model, 'RestartSlotsForMMiAlone', msgOn, msgOff, False, False)
        msgOn = 'Copy the mmi built over the installation in C:/icos.'
        msgOff = 'Do NOT copy the mmi built over the installation in C:/icos.\nThis is NOT RECOMMENDED.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 2, 0, 'Copy MMi to Icos On AutoTest', self.model, 'CopyMmi', msgOn, msgOff, False, True)
        msgOn = 'The file LicMgrConfig.xml will be created while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file LicMgrConfig.xml will NOT be created while running auto test.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 3, 0, 'Generate LicMgrConfig.xml On AutoTest', self.model, 'GenerateLicMgrConfigOnTest', msgOn, msgOff, True, False)
        msgOn = 'The file mock License.dll will be copied while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file mock License.dll will NOT be copied while running auto test.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 4, 0, 'Copy Mock License On AutoTest', self.model, 'CopyMockLicenseOnTest', msgOn, msgOff, True, False)
        msgOn = 'The file xPort_IllumReference.xml will be copied while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file xPort_IllumReference.xml will NOT be copied while running auto test.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 5, 0, 'Copy xPort_IllumReference.xml on AutoTest', self.model, 'CopyExportIllumRefOnTest', msgOn, msgOff, True, False)
        msgOn = 'The file C:\icos\Started.txt will be removed while running MMi.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file C:\icos\Started.txt will NOT be removed while running MMi.'
        self.checkBoxCreator.AddCheckBox(checkFrame, 5, 0, 'Remove C:\icos\Started.txt on starting MMI', self.model, 'RemoveStartedTXT', msgOn, msgOff, True, False)

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
