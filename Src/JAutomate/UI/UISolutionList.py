from Common.UIFactory import UIFactory
from UI.UIWindow import UIWindow

class UISolutionList(UIWindow):
    def __init__(self, parent, model, vsSolutions):
        super(UISolutionList, self).__init__(parent, model, 'Visutal Studio Solutions')
        self.vsSolutions = vsSolutions

    def CreateUI(self, parent):
        frame = UIFactory.AddFrame(parent, 0, 0, 50)

        row = 0
        col = 0
        maxRow = 5
        for sln in self.vsSolutions.GetAllSlnFiles():
            if row == maxRow:
                row = 0
                col += 1
            label = 'Open ' + self.vsSolutions.GetSlnName(sln)
            UIFactory.AddButton(frame, label, row, col, self.OnOpenSolution, (sln,), 19)
            row += 1

        row = maxRow
        UIFactory.AddLabel(frame, ' ', row, 0)

        row += 1
        self.AddBackButton(frame, row, col)

    def OnOpenSolution(self, sln):
        self.vsSolutions.OpenSolutionFile(sln)
