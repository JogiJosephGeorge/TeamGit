from Common.Git import Git
from Common.UIFactory import UIFactory
from UI.UISourceSelector import UISourceSelector


class UISourceGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, OnSrcChanged):
        self.window = UI.window
        self.model = UI.model
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler
        self.OnSrcChanged = OnSrcChanged

        row1 = UI.AddRow()
        UIFactory.AddLabel(row1, 'Source', 0, 0)
        self.AddSourceDescription(row1, 0, 1)
        UIFactory.AddButton(row1, ' ... ', 0, 2, self.OnSelectSource)
        self.lblBranch = UIFactory.AddLabel(row1, self.model.Branch, 0, 3)

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
