from Common.UIFactory import UIFactory
from UI.UISourceSelector import UISourceSelector


class UISourceGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler):
        self.window = UI.window
        self.model = UI.model
        self.VM = UI.VM
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler

        row1 = UI.AddRow()
        UIFactory.AddLabel(row1, 'Source', 0, 0)
        self.AddSourceDescription(row1, 0, 1)
        UIFactory.AddButton(row1, ' ... ', 0, 2, self.OnSelectSource)
        self.VM.lblBranch = UIFactory.AddLabel(row1, self.model.Branch, 0, 3)

    def AddSourceDescription(self, parent, r, c):
        source = self.VM.GetSource()
        self.VM.lblSource = UIFactory.AddLabel(parent, source, r, c)

    def OnSelectSource(self):
        UISourceSelector(self.window, self.model, self.klaRunner, self.vsSolutions, self.VM, self.threadHandler).Show()

    def AddParallelButton(self, label, FunPnt, InitFunPnt):
        self.threadHandler.AddButton(self.frame, label, 0, self.ColInx, FunPnt, None, InitFunPnt, None, 0)
        self.ColInx += 1
