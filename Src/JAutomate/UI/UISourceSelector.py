import threading
import Tkinter as tk
import tkFileDialog

from Common.UIFactory import UIFactory
from Common.Git import Git
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from KLA.KlaSourceBuilder import KlaSourceBuilder
from KlaModel.ConfigEncoder import ConfigEncoder
from UI.UIWindow import UIWindow
from Common.PrettyTable import PrettyTable, TableFormat


class UISourceSelector(UIWindow):
    def __init__(self, parent, model, klaRunner, vsSolutions, VM, threadHandler):
        super(UISourceSelector, self).__init__(parent, model, 'Select Source')
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.VM = VM
        self.threadHandler = threadHandler
        self.srcBuilder = KlaSourceBuilder(self.model, self.klaRunner, self.vsSolutions)

    def CreateUI(self, parent):
        self.SelectedSrc = tk.IntVar()
        self.SelectedSrc.set(self.model.SrcIndex)
        self.lblBranches = []
        self.cboConfig = []
        self.cboPlatform = []
        self.chkActiveSrcs = []
        self.Row = 0
        self.mainFrame = parent
        frameGrid = self.AddRow()
        UIFactory.AddLabel(frameGrid, 'Is Active', 0, 0)
        UIFactory.AddLabel(frameGrid, 'Current Source', 0, 1)
        UIFactory.AddLabel(frameGrid, 'Branch', 0, 2)
        UIFactory.AddLabel(frameGrid, 'Configuration', 0, 3)
        UIFactory.AddLabel(frameGrid, 'Platform', 0, 4)
        r = 1
        for srcTuple in self.model.Sources:
            self.AddActive(frameGrid, r, 0)
            self.AddSource(frameGrid, r, 1, srcTuple[0])
            self.AddBranch(frameGrid, r, 2, srcTuple[0])
            self.AddConfig(frameGrid, r, 3, srcTuple[1])
            self.AddPlatform(frameGrid, r, 4, srcTuple[2])
            r += 1

        self.AddSolutions()
        self.AddFunctions()

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
        data = [['Source', 'Branch']]
        for srcTuple in self.model.Sources:
            data.append(['-'])
            branch = '' # Git.GetBranch(srcTuple[0])
            for brn1 in Git.GetLocalBranches(srcTuple[0]):
                if brn1.startswith('* '):
                    branch = brn1[2:]
                    data.append([srcTuple[0], branch])
                else:
                    data.append(['', brn1])
            self.lblBranches[index].set(branch)
            if index == self.model.SrcIndex:
                self.model.Branch = branch
            index += 1
        print PrettyTable(TableFormat().SetSingleLine()).ToString(data)

    def OnClosing(self):
        self.model.Branch = self.lblBranches[self.model.SrcIndex].get()
        if self.VM is not None:
            self.VM.UpdateSourceBranch()
        super(UISourceSelector, self).OnClosing()

    def AddSource(self, parent, r, c, source):
        rd = tk.Radiobutton(parent,
            text = source,
            variable = self.SelectedSrc,
            command = self.OnSelectSrc,
            value = r-1)
        rd.grid(row=r, column=c, sticky='w')

    def OnSelectSrc(self):
        SrcIndex = self.SelectedSrc.get()
        self.model.SrcCnf.UpdateSource(SrcIndex, False)
        print 'Source changed to : ' + self.model.Source
        Logger.Log('Source changed to : ' + self.model.Source)

    def AddBranch(self, parent, r, c, source):
        label = UIFactory.AddLabel(parent, 'Branch Name Updating...', r, c)
        self.lblBranches.append(label)

    def AddConfig(self, parent, r, c, config):
        configInx = ConfigEncoder.Configs.index(config)
        combo = UIFactory.AddCombo(parent, ConfigEncoder.Configs, configInx, r, c, self.OnConfigChanged, r-1, 10)
        self.cboConfig.append(combo)

    def OnConfigChanged(self, row):
        selectedInx = self.cboConfig[row].current()
        if self.model.UpdateConfig(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Config Changed to {} for source {}'.format(srcTuple[1], srcTuple[0])

    def AddPlatform(self, parent, r, c, platform):
        platformInx = ConfigEncoder.Platforms.index(platform)
        combo = UIFactory.AddCombo(parent, ConfigEncoder.Platforms, platformInx, r, c, self.OnPlatformChanged, r-1, 10)
        self.cboPlatform.append(combo)

    def OnPlatformChanged(self, row):
        selectedInx = self.cboPlatform[row].current()
        if self.model.UpdatePlatform(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Platform Changed to {} for source {}'.format(srcTuple[2], srcTuple[0])

    def AddActive(self, parent, r, c):
        Index = r - 1
        isActive = Index in self.model.ActiveSrcs
        chk = UIFactory.AddCheckBox(parent, '', isActive, r, c, self.OnActiveSrcChanged, (Index,), 'ew')
        self.chkActiveSrcs.append(chk)

    def OnActiveSrcChanged(self, Index):
        if self.chkActiveSrcs[Index].get():
            self.model.ActiveSrcs.append(Index)
            self.model.ActiveSrcs = list(set(self.model.ActiveSrcs))
            print 'Enabled the source : ' + str(self.model.Sources[Index][0])
        else:
            self.model.ActiveSrcs.remove(Index)
            print 'Disabled the source : ' + str(self.model.Sources[Index][0])

    def AddSolutions(self):
        allSlns = self.vsSolutions.GetAllSlnFiles()
        self.vsSolutions.SelectedInxs = [True] * len(allSlns)
        if self.klaRunner is None:
            return
        self.AddEmptyRow()
        selMsg = 'Select Solutions to build / clean on active sources'
        UIFactory.AddLabel(self.AddRow(), selMsg, 0, 0)
        self.slnChks = []
        row1 = self.AddRow()
        for inx,sln in enumerate(allSlns):
            slnName = self.vsSolutions.GetSlnName(sln)
            chk = UIFactory.AddCheckBox(row1, slnName, True, 0, inx, self.OnSelectSolution, (inx,))
            self.slnChks.append(chk)
        row2 = self.AddRow()
        self.threadHandler.AddButton(row2, ' Clean Solutions ', 0, 0, self.srcBuilder.CleanSource, None, self.srcBuilder.NotifyClean, 19)
        self.threadHandler.AddButton(row2, ' Build Solutions ', 0, 1, self.srcBuilder.BuildSource, None, self.srcBuilder.NotifyBuild, 19)

    def OnSelectSolution(self, inx):
        self.vsSolutions.SelectedInxs[inx] = self.slnChks[inx].get()

    def AddFunctions(self):
        if self.klaRunner is not None:
            if self.model.ShowAllButtons:
                self.AddEmptyRow()
                self.AddCleanDotVsOnReset(self.AddRow(), 0, 0)
                self.AddUpdateSubmodulesOnReset(self.AddRow(), 0, 0)
                self.threadHandler.AddButton(self.AddRow(), ' Reset Source ', 0, 0, self.srcBuilder.ResetSource, None, self.srcBuilder.NotifyReset, 19)

        self.AddEmptyRow()
        row2 = self.AddRow()
        UIFactory.AddButton(row2, 'Add Source', 0, 0, self.OnAddSource, None, 19)
        UIFactory.AddButton(row2, 'Remove Source', 0, 1, self.OnRemoveSource, None, 19)
        self.AddBackButton(row2, 0, 2)

    def AddCleanDotVsOnReset(self, parent, r, c):
        txt = 'Remove .vs directories on reseting source'
        isChecked = self.model.CleanDotVsOnReset
        self.ChkCleanDotVsOnReset = UIFactory.AddCheckBox(parent, txt, isChecked, r, c, self.OnCleanDotVsOnReset)

    def OnCleanDotVsOnReset(self):
        self.model.CleanDotVsOnReset = self.ChkCleanDotVsOnReset.get()
        if self.model.CleanDotVsOnReset:
            MessageBox.ShowMessage('All .vs directories in the source will be removed while reseting source.')
        else:
            print 'The .vs directories will NOT be affected while reseting source.'

    def AddUpdateSubmodulesOnReset(self, parent, r, c):
        txt = 'Update all submodules after reset'
        isChecked = self.model.UpdateSubmodulesOnReset
        self.ChkResetSubmodules = UIFactory.AddCheckBox(parent, txt, isChecked, r, c, self.OnResetSubmodules)

    def OnResetSubmodules(self):
        self.model.UpdateSubmodulesOnReset = self.ChkResetSubmodules.get()
        if self.model.UpdateSubmodulesOnReset:
            MessageBox.ShowMessage('All submodules will be updated after reseting source.')
        else:
            print 'The submodules will NOT be affected while reseting source.'

    def OnAddSource(self):
        folderSelected = tkFileDialog.askdirectory()
        if len(folderSelected) > 0:
            ConfigEncoder.AddSrc(self.model, folderSelected)
            row = len(self.model.Sources)
            self.AddRow(row, self.model.Sources[-1])
            print 'New source added : ' + folderSelected

    def OnRemoveSource(self):
        src = self.model.Sources[self.model.SrcIndex][0]
        if MessageBox.YesNoQuestion('Remove Source', 'Do you want to remove source ' + src):
            msg = 'The source ' + src + ' has been removed.'
            del self.model.Sources[self.model.SrcIndex]
            del self.cboConfig[self.model.SrcIndex]
            del self.cboPlatform[self.model.SrcIndex]
            self.model.SrcCnf.UpdateSource(self.model.SrcIndex - 1, False)
            print msg
