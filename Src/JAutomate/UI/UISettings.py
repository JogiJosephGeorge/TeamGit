import os
import tkFileDialog

from Common.UIFactory import UIFactory, CheckBoxCreator, TextBoxCreator
from UI.UIWindow import UIWindow


class UISettings(UIWindow):
    def __init__(self, parent, model):
        super(UISettings, self).__init__(parent, model, 'Settings')
        self.GrpRow = 0
        self.Row = 0

    def CreateUI(self, parent):
        self.checkBoxCreator = CheckBoxCreator()

        pathFrame = self.AddGroup(parent)
        self.AddSelectPathRow(pathFrame, 'MMi Setups Path', 'MMiSetupsPath')
        self.AddSelectPathRow(pathFrame, 'MMi Config Path', 'MMiConfigPath')
        self.AddSelectFileRow(pathFrame, 'Effort Log File', 'EffortLogFile')
        self.AddSelectFileRow(pathFrame, 'DevEnv.com', 'DevEnvCom')
        self.AddSelectFileRow(pathFrame, 'DevEnv.exe', 'DevEnvExe')
        self.AddSelectPathRow(pathFrame, 'Git Path', 'GitPath')
        self.AddSelectFileRow(pathFrame, 'VMware.exe', 'VMwareExe')
        self.AddSelectFileRow(pathFrame, 'Beyond Compare', 'BCompare')

        self.textBoxCreator = TextBoxCreator(self.model)
        textFrame = self.AddGroup(parent)
        self.AddTextRow(textFrame, 'VM Ware Password', 'VMwarePwd')
        self.AddTextRow(textFrame, 'Number of Slots', 'MaxSlots')

        checkFrame = self.AddGroup(parent)
        self.chkRow = 0
        def AddCheckBox(txt, modelParam, msgOn, msgOff, showMsgOn, showMsgOff):
            self.checkBoxCreator.AddCheckBox(checkFrame, self.chkRow, 0, txt, self.model, modelParam, msgOn, msgOff, showMsgOn, showMsgOff)
            self.chkRow += 1

        txt = 'Show All Commands in KlaRunner'
        msgOn = msgOff = 'You need to restart the application to update the UI.'
        AddCheckBox(txt, 'ShowAllButtons', msgOn, msgOff, True, True)

        txt = 'Run Host Cam while running Handler alone'
        msgOn = 'Run Host Cam while running Handler alone.'
        msgOff = 'Do NOT run Host Cam while running Handler alone.'
        AddCheckBox(txt, 'RunHostCam', msgOn, msgOff, False, False)

        txt = 'Restart Slots while running MMi alone'
        msgOn = 'The selected slots will be restarted while running MMi alone.'
        msgOff = 'The selected slots will NOT be restarted while running MMi alone.'
        AddCheckBox(txt, 'RestartSlotsForMMiAlone', msgOn, msgOff, False, False)

        txt = 'Copy MMi to Icos On AutoTest'
        msgOn = 'Copy the mmi built over the installation in C:/icos.'
        msgOff = 'Do NOT copy the mmi built over the installation in C:/icos.\nThis is NOT RECOMMENDED.'
        AddCheckBox(txt, 'CopyMmi', msgOn, msgOff, False, True)

        txt = 'Generate LicMgrConfig.xml On AutoTest'
        msgOn = 'The file LicMgrConfig.xml will be created while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file LicMgrConfig.xml will NOT be created while running auto test.'
        AddCheckBox(txt, 'GenerateLicMgrConfigOnTest', msgOn, msgOff, True, False)

        txt = 'Copy Mock License On AutoTest'
        msgOn = 'The file mock License.dll will be copied while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file mock License.dll will NOT be copied while running auto test.'
        AddCheckBox(txt, 'CopyMockLicenseOnTest', msgOn, msgOff, True, False)

        txt = 'Copy xPort_IllumReference.xml on AutoTest'
        msgOn = 'The file xPort_IllumReference.xml will be copied while running auto test.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file xPort_IllumReference.xml will NOT be copied while running auto test.'
        AddCheckBox(txt, 'CopyExportIllumRefOnTest', msgOn, msgOff, True, False)

        txt = 'Remove C:\icos\Started.txt on starting MMI'
        msgOn = 'The file C:\icos\Started.txt will be removed while running MMi.\nThis is NOT RECOMMENDED.'
        msgOff = 'The file C:\icos\Started.txt will NOT be removed while running MMi.'
        AddCheckBox(txt, 'RemoveStartedTXT', msgOn, msgOff, True, False)

        self.AddBackButton(parent, self.GrpRow, 0)

    def AddGroup(self, parent):
        frame = UIFactory.AddFrame(parent, self.GrpRow, 0)
        self.GrpRow += 1
        self.Row = 0
        return frame

    def OnClosing(self):
        self.textBoxCreator.UpdateModel()
        super(UISettings, self).OnClosing()

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

    def AddTextRow(self, parent, label, attrName):
        UIFactory.AddLabel(parent, label, self.Row, 0)
        self.textBoxCreator.Add(parent, self.Row, 1, attrName)
        self.Row += 1
