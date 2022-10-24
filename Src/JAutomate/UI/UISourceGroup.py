from Common.Git import Git
from Common.OsOperations import OsOperations
from Common.UIFactory import UIFactory
from KlaModel.VsVersions import VsVersions
from UI.UISourceSelector import UISourceSelector


class UISourceGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, OnSrcChanged):
        self.window = UI.window
        self.model = UI.model
        self.VM = UI.VM
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler
        self.OnSrcChanged = OnSrcChanged

        row1 = UI.AddRow()
        UIFactory.AddLabel(row1, 'Source', 0, 0)
        self.AddSourceDescription(row1, 0, 1)
        UIFactory.AddButton(row1, ' ... ', 0, 2, self.OnSelectSource)
        self.lblBranch = UIFactory.AddLabel(row1, self.model.Branch, 0, 3)

        if self.model.UserAccess.IsExpertUser():
            row2 = UI.AddRow()
            self.col = 0
            self.AddSetupVersion(row2, 0)
            self.AddVSVersion(row2, 0)

    def AddSourceDescription(self, parent, r, c):
        source = self.GetSource()
        self.lblSource = UIFactory.AddLabel(parent, source, r, c)

    def OnSelectSource(self):
        UISourceSelector(self.window
                         , self.model
                         , self.klaRunner
                         , self.vsSolutions
                         , self.threadHandler
                         , self.OnSrcSelectorClosed
                         ).Show()

    def OnSrcSelectorClosed(self):
        sourceDec = self.GetSource()
        self.lblSource.set(sourceDec)
        self.UpdateBranch()
        self.OnSrcChanged()

    def UpdateBranch(self):
        branch = self.model.Branch
        curSrc = self.model.Src.GetCur()
        if len(curSrc.Description) > 0:
            commitId = Git.GetCommitId(curSrc.Source)
            branch = '{} ({}) {}'.format(self.model.Branch, commitId, curSrc.Description)
        self.lblBranch.set(branch)

    def GetSource(self):
        curSrc = self.model.Src.GetCur()
        return '{}     ({} | {})'.format(curSrc.Source, curSrc.Config, curSrc.Platform)

    def AddParallelButton(self, label, FunPnt, InitFunPnt):
        self.threadHandler.AddButton(self.frame, label, 0, self.ColInx, FunPnt, None, InitFunPnt, None, 0)
        self.ColInx += 1

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
