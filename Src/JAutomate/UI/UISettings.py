import os
import tkFileDialog

from Common.MessageBox import MessageBox
from Common.UIFactory import UIFactory, CheckBoxCreator, TextBoxCreator
from UI.UIWindow import UIWindow


class UISettings(UIWindow):
    def __init__(self, parent, model, OnSettingsClosed):
        super(UISettings, self).__init__(parent, model, 'Settings', OnSettingsClosed)
        self.GrpRow = 0
        self.Row = 0

    def CreateUI(self, parent):
        self.checkBoxCreator = CheckBoxCreator()

        pathFrame = self.AddGroup(parent)
        self.AddSelectPathRow(pathFrame, 'MMi Setups Path', self.model, 'MMiSetupsPath')
        self.AddSelectPathRow(pathFrame, 'MMi Config Path', self.model, 'MMiConfigPath')
        if self.model.UserAccess.IsDeveloper():
            self.AddSelectFileRow(pathFrame, 'Effort Log File', self.model, 'EffortLogFile')
        self.AddSelectFileRow(pathFrame, 'DevEnv.com 2017', self.model.VsVersions, 'DevEnvCom')
        self.AddSelectFileRow(pathFrame, 'DevEnv.exe 2017', self.model.VsVersions, 'DevEnvExe')
        if self.model.UserAccess.IsExpertUser():
            self.AddSelectFileRow(pathFrame, 'DevEnv.com 2022', self.model.VsVersions, 'DevEnvCom22')
            self.AddSelectFileRow(pathFrame, 'DevEnv.exe 2022', self.model.VsVersions, 'DevEnvExe22')
        self.AddSelectPathRow(pathFrame, 'Git Path', self.model, 'GitPath')
        self.AddSelectFileRow(pathFrame, 'VMware.exe', self.model, 'VMwareExe')
        self.AddSelectFileRow(pathFrame, 'Beyond Compare', self.model, 'BCompare')

        self.textBoxCreator = TextBoxCreator(self.model)
        textFrame = self.AddGroup(parent)
        self.AddTextRow(textFrame, 'VM Ware Password', 'VMwarePwd', None)
        def ValidateMaxSlot(slot):
            return int(slot)

        if self.model.UserAccess.IsExpertUser():
            self.AddTextRow(textFrame, 'Number of Slots', 'MaxSlots', ValidateMaxSlot)
            self.AddTextRow(textFrame, 'DebugView Filter', 'LogName', None)

        checkFrame = self.AddGroup(parent)
        self.chkRow = 0
        def AddCheckBox(txt, modelParam, msgOn, msgOff, showMsgOn, showMsgOff):
            self.checkBoxCreator.AddCheckBox(checkFrame, self.chkRow, 0, txt, self.model, modelParam, msgOn, msgOff, showMsgOn, showMsgOff)
            self.chkRow += 1

        if self.model.UserAccess.IsDeveloper():
            txt = 'Prevent Running Auto Test'
            msgOn = 'Start/Run Test buttons will NOT be available for performing diagnostic setup.'
            msgOff = 'Start/Run Test buttons will be available.'
            AddCheckBox(txt, 'NoAutoTest', msgOn, msgOff, False, False)
        else:
            txt = 'Show All Commands in KlaRunner'
            isChecked = self.model.UserAccess.IsExpertUser()
            self.ShowAllChkBox = UIFactory.AddCheckBox(checkFrame, txt, isChecked, self.chkRow, 0, self.OnClickShowAllCheckBox)
            self.chkRow += 1

        if self.model.UserAccess.IsExpertUser():
            txt = 'Run Host Cam while running MMi alone'
            msgOn = 'Run Host Cam while running MMi alone.'
            msgOff = 'Do NOT run Host Cam while running MMi alone.'
            AddCheckBox(txt, 'RunHostCam', msgOn, msgOff, False, False)

            txt = 'Restart Slots while running MMi alone'
            msgOn = 'The selected slots will be restarted while running MMi alone.'
            msgOff = 'The selected slots will NOT be restarted while running MMi alone.'
            AddCheckBox(txt, 'RestartSlotsForMMiAlone', msgOn, msgOff, False, False)

            txt = 'Remove C:\icos\Started.txt on starting MMI'
            msgOn = 'The file C:\icos\Started.txt will be removed while running MMi. This is NOT RECOMMENDED.'
            msgOff = 'The file C:\icos\Started.txt will NOT be removed while running MMi.'
            AddCheckBox(txt, 'RemoveStartedTXT', msgOn, msgOff, True, False)

            txt = 'On AutoTest Copy MMi to Icos'
            msgOn = 'Copy the mmi built over the installation in C:/icos.'
            msgOff = 'Do NOT copy the mmi built over the installation in C:/icos. This is NOT RECOMMENDED.'
            AddCheckBox(txt, 'CopyMmi', msgOn, msgOff, False, True)

            txt = 'On AutoTest Remove old copies of the testcase'
            msgOn = 'Remove old copies of the testcase.'
            msgOff = 'Do NOT Remove old copies of the testcase. This is NOT RECOMMENDED.'
            AddCheckBox(txt, 'removeOldCopies', msgOn, msgOff, False, True)

            txt = 'On AutoTest Generate LicMgrConfig.xml'
            msgOn = 'The file LicMgrConfig.xml will be created while running auto test. This is NOT RECOMMENDED.'
            msgOff = 'The file LicMgrConfig.xml will NOT be created while running auto test.'
            AddCheckBox(txt, 'GenerateLicMgrConfigOnTest', msgOn, msgOff, True, False)

            txt = 'On AutoTest Copy LicMgrConfig.xml'
            msgOn = 'The file LicMgrConfig.xml will be copied while running auto test. This is NOT RECOMMENDED.'
            msgOff = 'The file LicMgrConfig.xml will NOT be copied while running auto test.'
            AddCheckBox(txt, 'CopyLicMgrConfigOnTest', msgOn, msgOff, True, False)

            txt = 'On AutoTest Copy Mock License'
            msgOn = 'The file mock License.dll will be copied while running auto test. This is NOT RECOMMENDED.'
            msgOff = 'The file mock License.dll will NOT be copied while running auto test.'
            AddCheckBox(txt, 'CopyMockLicenseOnTest', msgOn, msgOff, True, False)

            txt = 'On AutoTest Copy xPort_IllumReference.xml'
            msgOn = 'The file xPort_IllumReference.xml will be copied while running auto test. This is NOT RECOMMENDED.'
            msgOff = 'The file xPort_IllumReference.xml will NOT be copied while running auto test.'
            AddCheckBox(txt, 'CopyExportIllumRefOnTest', msgOn, msgOff, True, False)

            txt = 'On AutoTest Copy MVSD Conversion'
            msgOn = 'The files in MVSD Conversion will be copied while running auto test. This is NOT RECOMMENDED.'
            msgOff = 'The files in MVSD Conversion will NOT be copied while running auto test.'
            AddCheckBox(txt, 'CopyMVSDConversionOnTest', msgOn, msgOff, True, False)

            txt = 'On AutoTest Console Run from C:/handler/system'
            msgOn = 'On AutoTest, Console will be running from C:/handler/system. This is NOT RECOMMENDED.'
            msgOff = 'On AutoTest, Console will be running from build source'
            AddCheckBox(txt, 'ConsoleFromCHandler', msgOn, msgOff, True, False)

        if self.model.UserAccess.IsDeveloper():
            txt = 'On AutoTest do not proceed after changing source'
            msgOn = 'On AutoTest, user has to restart KlaRunner after changing source.'
            msgOff = 'This may not work for all auto tests. This is NOT RECOMMENDED.'
            AddCheckBox(txt, 'RestartAfterSrcChange', msgOn, msgOff, False, True)

        self.AddBackButton(parent, self.GrpRow, 0)

    def AddGroup(self, parent):
        frame = UIFactory.AddFrame(parent, self.GrpRow, 0)
        self.GrpRow += 1
        self.Row = 0
        return frame

    def OnClosing(self):
        self.textBoxCreator.UpdateModel()
        super(UISettings, self).OnClosing()

    def AddSelectPathRow(self, parent, label, attrObj, attrName, onPathChanged = None):
        self.AddSelectItemRow(parent, label, attrObj, attrName, False, onPathChanged)

    def AddSelectFileRow(self, parent, label, attrObj, attrName):
        self.AddSelectItemRow(parent, label, attrObj, attrName, True, None)

    def AddSelectItemRow(self, parent, label, attrObj, attrName, isFile, onItemChanged):
        UIFactory.AddLabel(parent, label, self.Row, 0)
        text = getattr(attrObj, attrName)
        if isFile:
            if not os.path.isfile(text):
                print "Given file doesn't exist : " + text
            cmd = self.SelectFile
        else:
            if not os.path.isdir(text):
                print "Given directory doesn't exist : " + text
            cmd = self.SelectPath
        textVar = UIFactory.AddLabel(parent, text, self.Row, 1)
        args = (textVar, attrObj, attrName, onItemChanged)
        UIFactory.AddButton(parent, ' ... ', self.Row, 2, cmd, args)
        self.Row += 1

    def SelectPath(self, textVar, attrObj, attrName, onItemChanged):
        folderSelected = tkFileDialog.askdirectory()
        if len(folderSelected) > 0:
            textVar.set(folderSelected)
            setattr(attrObj, attrName, folderSelected)
            print '{} Path changed : {}'.format(attrName, folderSelected)
            if onItemChanged:
                onItemChanged()

    def SelectFile(self, textVar, attrObj, attrName, onItemChanged):
        filename = tkFileDialog.askopenfilename(initialdir = "/", title = "Select file")
        if len(filename) > 0:
            textVar.set(filename)
            setattr(attrObj, attrName, filename)
            print '{} Path changed : {}'.format(attrName, filename)
            if onItemChanged:
                onItemChanged()

    def AddTextRow(self, parent, label, attrName, validate):
        UIFactory.AddLabel(parent, label, self.Row, 0)
        self.textBoxCreator.Add(parent, self.Row, 1, attrName, validate)
        self.Row += 1

    def OnClickShowAllCheckBox(self):
        if self.model.UserAccess.IsDeveloper():
            return
        isChecked = self.ShowAllChkBox.get()
        self.model.UserAccess.SetIsExpertUser(isChecked)
        msg = 'You need to restart the application to update the UI.'
        MessageBox.ShowMessage(msg)
