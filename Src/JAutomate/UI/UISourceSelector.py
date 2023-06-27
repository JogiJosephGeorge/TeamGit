import Tkinter as tk
import threading
import tkFileDialog

from Common.Git import Git
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from Common.PrettyTable import PrettyTable, TableFormat
from Common.UIFactory import UIFactory, CheckBoxCreator
from KLA.AppRunner import AppRunner
from KLA.KlaSourceBuilder import KlaSourceBuilder, KlaSourceCleaner
from KLA.PreTestActions import PreTestActions, SourceCodeUpdater
from KlaModel.ConfigEncoder import Config, Platform
from UI.UISolutionList import UISolutionList
from UI.UIWindow import UIWindow


class UISourceGrid:
    def __init__(self, model, parentFrame):
        self.model = model
        self.ParentFrame = parentFrame
        self.chkActiveSrcs = []
        self.radCurSrc = []
        self.lblBranches = []
        self.cboConfig = []
        self.cboPlatform = []
        self.txtDescription = []
        self.SelectedSrc = tk.IntVar()
        self.SelectedSrc.set(self.model.Src.SrcIndex)

    def CreateUI(self):
        self.AddHeader()
        r = 1
        for srcData in self.model.Src.GetAllSrcs():
            self.AddSrcRow(r, srcData)
            r += 1

    def AddHeader(self):
        UIFactory.AddLabel(self.ParentFrame, 'Is Active', 0, 0)
        UIFactory.AddLabel(self.ParentFrame, 'Current Source', 0, 1)
        UIFactory.AddLabel(self.ParentFrame, 'Branch', 0, 2)
        UIFactory.AddLabel(self.ParentFrame, 'Platform', 0, 3)
        UIFactory.AddLabel(self.ParentFrame, 'Configuration', 0, 4)
        UIFactory.AddLabel(self.ParentFrame, 'Description', 0, 5)

    def AddSrcRow(self, r, srcData):
        self.AddActive(r, 0)
        self.AddSource(r, 1, srcData.Source)
        self.AddBranch(r, 2)
        self.AddPlatform(r, 3, srcData.Platform)
        self.AddConfig(r, 4, srcData.Config)
        self.AddDescription(r, 5, srcData.Description)

    def AddActive(self, r, c):
        Index = r - 1
        isActive = self.model.Src.GetSrcAt(Index).IsActive
        chk = UIFactory.AddCheckBox(self.ParentFrame, '', isActive, r, c, self.OnActiveSrcChanged, (Index,), 'ew')
        self.chkActiveSrcs.append(chk)

    def OnActiveSrcChanged(self, Index):
        srcData = self.model.Src.GetSrcAt(Index)
        if self.IsSrcActive(Index):
            srcData.IsActive = True
            print 'Enabled the source : ' + srcData.Source
        else:
            srcData.IsActive = False
            print 'Disabled the source : ' + srcData.Source

    def IsSrcActive(self, index):
        return self.chkActiveSrcs[index].get()

    def AddSource(self, r, c, source):
        rd = tk.Radiobutton(self.ParentFrame,
            text = source,
            variable = self.SelectedSrc,
            command = self.OnSelectSrc,
            value = r-1)
        rd.grid(row=r, column=c, sticky='w')
        self.radCurSrc.append(rd)

    def OnSelectSrc(self):
        srcIndex = self.SelectedSrc.get()
        self.model.Src.UpdateSource(srcIndex, False)
        curSrc = self.model.Src.GetCur()
        print 'Source changed to : ' + curSrc.Source
        Logger.Log('Source changed to : ' + curSrc.Source)

    def AddBranch(self, r, c):
        label = UIFactory.AddLabel(self.ParentFrame, 'Branch Name Updating...', r, c)
        self.lblBranches.append(label)

    def SetBranch(self, index, branch):
        self.lblBranches[index].set(branch)

    def GetBranch(self, index):
        if len(self.lblBranches) == 0:
            return ''
        return self.lblBranches[index].get()

    def AddConfig(self, r, c, config):
        configs = Config.GetList()
        configInx = configs.index(config)
        combo = UIFactory.AddCombo(self.ParentFrame, configs, configInx, r, c, self.OnConfigChanged, r-1, 10)
        self.cboConfig.append(combo)

    def OnConfigChanged(self, row):
        selectedInx = self.GetConfigInx(row)
        if self.model.UpdateConfig(row, selectedInx):
            self.model.WriteToFile()
            srcData = self.model.Src.GetSrcAt(row)
            print 'Config Changed to {} for source {}'.format(srcData.Config, srcData.Source)

    def GetConfigInx(self, row):
        return self.cboConfig[row].current()

    def AddDescription(self, r, c, descr):
        textVar = UIFactory.AddTextBox(self.ParentFrame, descr, r, c, 50)
        self.txtDescription.append(textVar)

    def OnDescriptionChanged(self, input):
        print input
        self.model.Src.GetCur().Description = input

    def AddPlatform(self, r, c, platform):
        platforms = Platform.GetList()
        platformInx = platforms.index(platform)
        combo = UIFactory.AddCombo(self.ParentFrame, platforms, platformInx, r, c, self.OnPlatformChanged, r-1, 10)
        self.cboPlatform.append(combo)

    def OnPlatformChanged(self, row):
        selectedInx = self.GetPlatformInx(row)
        if self.model.UpdatePlatform(row, selectedInx):
            self.model.WriteToFile()
            srcData = self.model.Src.GetSrcAt(row)
            print 'Platform Changed to {} for source {}'.format(srcData.Platform, srcData.Source)

    def GetPlatformInx(self, row):
        return self.cboPlatform[row].current()

    def DeleteRow(self, row):
        del self.chkActiveSrcs[row]
        del self.radCurSrc[row]
        del self.lblBranches[row]
        del self.cboConfig[row]
        del self.cboPlatform[row]

    def OnClosing(self):
        row = 0
        for txtDesc in self.txtDescription:
            src = self.model.Src.GetSrcAt(row)
            if src is None:
                return
            src.Description = txtDesc.get()
            row += 1


class UISourceSelector(UIWindow):
    def __init__(self, parent, model, klaRunner, vsSolutions, threadHandler, onClosed):
        super(UISourceSelector, self).__init__(parent, model, 'Source Manager', onClosed)
        self.checkBoxCreator = CheckBoxCreator()
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler
        self.srcBuilder = KlaSourceBuilder(self.model, self.vsSolutions)
        self.srcCleaner = KlaSourceCleaner(self.model)

    def CreateUI(self, parent):
        self.Row = 0
        self.mainFrame = parent
        self.SourceGrid = UISourceGrid(self.model, self.AddRow())
        self.SourceGrid.CreateUI()
        self.AddGitActions()
        self.AddSolutions()
        self.AddFunctions()

        if self.model.Src.SrcIndex >= 0:
            threading.Thread(target=self.LazyUiInit).start()

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddEmptyRow(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, '', 0, 0)

    def LazyUiInit(self):
        index = 0
        data = [['Source', 'Commit ID', 'Branch', 'Available Configs']]
        data += [['', '', '', '(* Without Handler)']]
        data += [['', '', '', '(+ Only Handler)']]
        for srcData in self.model.Src.GetAllSrcs():
            data.append(['-'])
            branch = '' # Git.GetBranch(src)
            configs = ''
            for pf,cfg,HasConsole,HasOthers in PreTestActions.GetExistingConfigs(srcData.Source):
                if HasConsole and HasOthers:
                    configs += '{}|{} '.format(pf, cfg).upper()
                elif HasConsole:
                    configs += '{}|{}+ '.format(pf, cfg)
                elif HasOthers:
                    configs += '{}|{}* '.format(pf, cfg)
            for brn1 in Git.GetLocalBranches(srcData.Source):
                if brn1.startswith('* '):
                    commitId = Git.GetCommitId(srcData.Source, brn1[2:])
                    branch = brn1[2:]
                    data.append([srcData.Source, commitId, branch, configs])
                else:
                    if brn1 != 'master':
                        commitId = Git.GetCommitId(srcData.Source, brn1)
                        data.append(['', commitId, brn1, ''])
            self.SourceGrid.SetBranch(index, branch)
            if index == self.model.Src.SrcIndex:
                self.model.Branch = branch
            index += 1
        PrettyTable(TableFormat().SetDoubleLineBorder()).PrintTable(data)

    def OnClosing(self):
        self.SourceGrid.OnClosing()
        self.model.Branch = self.SourceGrid.GetBranch(self.model.Src.SrcIndex)
        SourceCodeUpdater.CopyPreCommit(self.model)
        super(UISourceSelector, self).OnClosing()

    def AddGitActions(self):
        self.AddEmptyRow()
        row1 = self.AddRow()
        UIFactory.AddButton(row1, 'Tortoise Git Diff', 0, 0, AppRunner.OpenLocalDif, (self.model,), 19)
        if self.model.UserAccess.IsExpertUser():
            UIFactory.AddButton(row1, 'Git GUI', 0, 1, Git.OpenGitGui, (self.model,), 19)
        UIFactory.AddButton(row1, 'Git Submodule Update', 0, 2, Git.SubmoduleUpdate, (self.model,), 19)
        UIFactory.AddButton(row1, 'Nuget Restore', 0, 3, self.NugetRestore, (self.model,), 19)

    def AddSolutions(self):
        allSlns = self.vsSolutions.GetAllSlnFiles()
        self.vsSolutions.Init()
        selMsg = 'Select Solutions to build / clean on active sources'
        UIFactory.AddLabel(self.AddRow(), selMsg, 0, 0)
        self.slnChks = []
        row1 = self.AddRow()
        for inx,sln in enumerate(allSlns):
            slnName = self.vsSolutions.GetSlnName(sln)
            isChecked = self.vsSolutions.SelectedInxs[inx]
            chk = UIFactory.AddCheckBox(row1, slnName, isChecked, 0, inx, self.OnSelectSolution, (inx,))
            self.slnChks.append(chk)
        rowBuildSettings = self.AddRow()
        self.checkBoxCreator.AddCheckBox(rowBuildSettings, 0, 0, 'Show Build In Progress', self.model, 'ShowBuildInProgress', '', '', False, False)
        row2 = self.AddRow()
        self.threadHandler.AddButton(row2, ' Clean Solutions ', 0, 0, self.srcBuilder.CleanSource, None, self.srcBuilder.NotifyClean, None, 19)
        self.threadHandler.AddButton(row2, ' Build Solutions ', 0, 1, self.srcBuilder.BuildSource, None, self.srcBuilder.NotifyBuild, None, 19)
        if self.model.UserAccess.IsExpertUser():
            UIFactory.AddButton(row2, 'Available Sources', 0, 2, PreTestActions.PrintAvailableExes, (self.model,), 19)
            UIFactory.AddButton(row2, 'Open Solutions', 0, 3, self.ShowOpenSolutionDlg, None, 19)

            row3 = self.AddRow()
            self.threadHandler.AddButton(row3, ' Remove Handler Temps ', 0, 0, self.srcCleaner.RemoveAllHandlerTemp, None, None, None, 19)
            self.threadHandler.AddButton(row3, ' Remove All ~', 0, 1, self.srcCleaner.RemoveAllTilt, None, None, None, 19)
            self.threadHandler.AddButton(row3, ' Remove MVS Temps ', 0, 2, self.srcCleaner.RemoveMvsTemp, None, None, None, 19)

    def ShowOpenSolutionDlg(self):
        UISolutionList(self.window, self.model, self.vsSolutions).Show()

    def OnSelectSolution(self, inx):
        self.vsSolutions.SelectedInxs[inx] = self.slnChks[inx].get()

    def AddFunctions(self):
        if self.model.UserAccess.IsExpertUser():
            self.AddEmptyRow()
            self.AddCleanDotVsOnReset(self.AddRow(), 0, 0)
            self.AddUpdateSubmodulesOnReset(self.AddRow(), 0, 0)
            self.threadHandler.AddButton(self.AddRow(), ' Reset Source ', 0, 0, self.srcBuilder.ResetSource, None, self.srcBuilder.NotifyReset, None, 19)

        self.AddEmptyRow()
        row2 = self.AddRow()
        UIFactory.AddButton(row2, 'Add Source', 0, 0, self.OnAddSource, None, 19)
        UIFactory.AddButton(row2, 'Remove Current Source', 0, 1, self.OnRemoveSource, None, 19)
        self.AddBackButton(row2, 0, 2)

    def AddCleanDotVsOnReset(self, parent, r, c):
        txt = 'Remove .vs directories on reseting source'
        msgOn = 'All .vs directories in the source will be removed while reseting source.'
        msgOff = 'The .vs directories will NOT be affected while reseting source.'
        self.checkBoxCreator.AddCheckBox(parent, r, c, txt, self.model, 'CleanDotVsOnReset', msgOn, msgOff, True, False)

    def AddUpdateSubmodulesOnReset(self, parent, r, c):
        txt = 'Update all submodules after reset'
        msgOn = 'All submodules will be updated after reseting source.'
        msgOff = 'The submodules will NOT be affected while reseting source.'
        self.checkBoxCreator.AddCheckBox(parent, r, c, txt, self.model, 'UpdateSubmodulesOnReset', msgOn, msgOff, True, False)

    def OnAddSource(self):
        folderSelected = tkFileDialog.askdirectory()
        if self.model.Src.AddSource(folderSelected):
            print 'New source added : ' + folderSelected
            srcs = list(self.model.Src.GetAllSrcs())
            row = len(srcs)
            srcData = self.model.Src.GetSrcAt(row - 1)
            self.SourceGrid.AddSrcRow(row, srcData)
            branch = Git.GetBranch(srcData.Source)
            self.SourceGrid.SetBranch(row - 1, branch)

    def OnRemoveSource(self):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        src = self.model.Src.GetSrcAt(self.model.Src.SrcIndex).Source
        if MessageBox.YesNoQuestion('Remove Source', 'Do you want to remove source ' + src):
            if self.model.Src.RemoveSource(self.model.Src.SrcIndex):
                msg = 'The source ' + src + ' has been removed.'
                self.SourceGrid.DeleteRow(self.model.Src.SrcIndex)
                print msg
                self.OnClosing() # After removing grid row, this line can be omitted
            else:
                print 'The source can not be removed.'

    def NugetRestore(self, model):
        curSrc = model.Src.GetCur()
        if not curSrc.Source:
            MessageBox.ShowMessage('No source available.')
            return
        par = 'nuget restore {}\mmi\mmi\Mmi.sln'.format(curSrc.Source)
        OsOperations.System(par, 'Restore Nuget Packages for MMI.sln')
        par = 'nuget restore {}\handler\Simulator\CIT100Simulator\CIT100Simulator.sln'.format(curSrc.Source)
        OsOperations.System(par, 'Restore Nuget Packages for CIT100Simulator.sln')