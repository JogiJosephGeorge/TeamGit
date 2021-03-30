import threading
import Tkinter as tk
import tkFileDialog

from Common.UIFactory import UIFactory, CheckBoxCreator
from Common.Git import Git
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from KLA.KlaSourceBuilder import KlaSourceBuilder, KlaSourceCleaner
from KLA.PreTestActions import PreTestActions
from KlaModel.ConfigEncoder import ConfigEncoder
from UI.UIWindow import UIWindow
from Common.PrettyTable import PrettyTable, TableFormat


class UISourceGrid:
    def __init__(self, model, parentFrame):
        self.model = model
        self.ParentFrame = parentFrame
        self.chkActiveSrcs = []
        self.radCurSrc = []
        self.lblBranches = []
        self.cboConfig = []
        self.cboPlatform = []
        self.SelectedSrc = tk.IntVar()
        self.SelectedSrc.set(self.model.SrcIndex)

    def CreateUI(self):
        self.AddHeader()
        r = 1
        for srcTuple in self.model.Sources:
            self.AddSrcRow(r, srcTuple)
            r += 1

    def AddHeader(self):
        UIFactory.AddLabel(self.ParentFrame, 'Is Active', 0, 0)
        UIFactory.AddLabel(self.ParentFrame, 'Current Source', 0, 1)
        UIFactory.AddLabel(self.ParentFrame, 'Branch', 0, 2)
        UIFactory.AddLabel(self.ParentFrame, 'Platform', 0, 3)
        UIFactory.AddLabel(self.ParentFrame, 'Configuration', 0, 4)

    def AddSrcRow(self, r, srcTuple):
        self.AddActive(r, 0)
        self.AddSource(r, 1, srcTuple[0])
        self.AddBranch(r, 2)
        self.AddPlatform(r, 3, srcTuple[2])
        self.AddConfig(r, 4, srcTuple[1])

    def AddActive(self, r, c):
        Index = r - 1
        isActive = Index in self.model.ActiveSrcs
        chk = UIFactory.AddCheckBox(self.ParentFrame, '', isActive, r, c, self.OnActiveSrcChanged, (Index,), 'ew')
        self.chkActiveSrcs.append(chk)

    def OnActiveSrcChanged(self, Index):
        if self.IsSrcActive(Index):
            self.model.ActiveSrcs.append(Index)
            self.model.ActiveSrcs = list(set(self.model.ActiveSrcs))
            print 'Enabled the source : ' + str(self.model.Sources[Index][0])
        else:
            self.model.ActiveSrcs.remove(Index)
            print 'Disabled the source : ' + str(self.model.Sources[Index][0])

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
        SrcIndex = self.SelectedSrc.get()
        self.model.SrcCnf.UpdateSource(SrcIndex, False)
        print 'Source changed to : ' + self.model.Source
        Logger.Log('Source changed to : ' + self.model.Source)

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
        configInx = ConfigEncoder.Configs.index(config)
        combo = UIFactory.AddCombo(self.ParentFrame, ConfigEncoder.Configs, configInx, r, c, self.OnConfigChanged, r-1, 10)
        self.cboConfig.append(combo)

    def OnConfigChanged(self, row):
        selectedInx = self.GetConfigInx(row)
        if self.model.UpdateConfig(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Config Changed to {} for source {}'.format(srcTuple[1], srcTuple[0])

    def GetConfigInx(self, row):
        return self.cboConfig[row].current()

    def AddPlatform(self, r, c, platform):
        platformInx = ConfigEncoder.Platforms.index(platform)
        combo = UIFactory.AddCombo(self.ParentFrame, ConfigEncoder.Platforms, platformInx, r, c, self.OnPlatformChanged, r-1, 10)
        self.cboPlatform.append(combo)

    def OnPlatformChanged(self, row):
        selectedInx = self.GetPlatformInx(row)
        if self.model.UpdatePlatform(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Platform Changed to {} for source {}'.format(srcTuple[2], srcTuple[0])

    def GetPlatformInx(self, row):
        return self.cboPlatform[row].current()

    def DeleteRow(self, row):
        del self.chkActiveSrcs[row]
        del self.radCurSrc[row]
        del self.lblBranches[row]
        del self.cboConfig[row]
        del self.cboPlatform[row]


class UISourceSelector(UIWindow):
    def __init__(self, parent, model, klaRunner, vsSolutions, VM, threadHandler):
        super(UISourceSelector, self).__init__(parent, model, 'Source Manager')
        self.checkBoxCreator = CheckBoxCreator()
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.VM = VM
        self.threadHandler = threadHandler
        self.srcBuilder = KlaSourceBuilder(self.model, self.klaRunner, self.vsSolutions)
        self.srcCleaner = KlaSourceCleaner(self.model)

    def CreateUI(self, parent):
        self.Row = 0
        self.mainFrame = parent
        self.SourceGrid = UISourceGrid(self.model, self.AddRow())
        self.SourceGrid.CreateUI()
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
            self.SourceGrid.SetBranch(index, branch)
            if index == self.model.SrcIndex:
                self.model.Branch = branch
            index += 1
        print PrettyTable(TableFormat().SetSingleLine()).ToString(data)

    def OnClosing(self):
        self.model.Branch = self.SourceGrid.GetBranch(self.model.SrcIndex)
        self.VM.UpdateSourceBranch()
        super(UISourceSelector, self).OnClosing()

    def AddSolutions(self):
        allSlns = self.vsSolutions.GetAllSlnFiles()
        self.vsSolutions.SelectedInxs = [True] * len(allSlns)
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
        self.threadHandler.AddButton(row2, ' Clean Solutions ', 0, 0, self.srcBuilder.CleanSource, None, self.srcBuilder.NotifyClean, None, 19)
        self.threadHandler.AddButton(row2, ' Build Solutions ', 0, 1, self.srcBuilder.BuildSource, None, self.srcBuilder.NotifyBuild, None, 19)
        if self.model.ShowAllButtons:
            UIFactory.AddButton(row2, 'Available MMI', 0, 2, PreTestActions.GetAllMmiPaths, (self.model,), 19)

            row3 = self.AddRow()
            self.threadHandler.AddButton(row3, ' Remove Handler Temps ', 0, 0, self.srcCleaner.RemoveHandlerTemp, None, None, None, 19)

    def OnSelectSolution(self, inx):
        self.vsSolutions.SelectedInxs[inx] = self.slnChks[inx].get()

    def AddFunctions(self):
        if self.model.ShowAllButtons:
            self.AddEmptyRow()
            self.AddCleanDotVsOnReset(self.AddRow(), 0, 0)
            self.AddUpdateSubmodulesOnReset(self.AddRow(), 0, 0)
            self.threadHandler.AddButton(self.AddRow(), ' Reset Source ', 0, 0, self.srcBuilder.ResetSource, None, self.srcBuilder.NotifyReset, None, 19)

        self.AddEmptyRow()
        row2 = self.AddRow()
        UIFactory.AddButton(row2, 'Add Source', 0, 0, self.OnAddSource, None, 19)
        UIFactory.AddButton(row2, 'Remove Source', 0, 1, self.OnRemoveSource, None, 19)
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
        if ConfigEncoder(self.model, folderSelected):
            row = len(self.model.Sources)
            srcTuple = self.model.Sources[row - 1]
            self.SourceGrid.AddSrcRow(row, srcTuple)
            branch = Git.GetBranch(srcTuple[0])
            self.SourceGrid.SetBranch(row - 1, branch)

    def OnRemoveSource(self):
        if self.model.SrcIndex < 0:
            return
        src = self.model.Sources[self.model.SrcIndex][0]
        if MessageBox.YesNoQuestion('Remove Source', 'Do you want to remove source ' + src):
            if self.model.SrcCnf.UpdateSource(self.model.SrcIndex - 1, False):
                msg = 'The source ' + src + ' has been removed.'
                del self.model.Sources[self.model.SrcIndex]
                self.SourceGrid.DeleteRow(self.model.SrcIndex)
                print msg
            else:
                print 'The source can not be removed.'
