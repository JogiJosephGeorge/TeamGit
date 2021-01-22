from Common.UIFactory import UIFactory
from UI.UIWindow import UIWindow


class UISolutionList(UIWindow):
    def __init__(self, parent, model, vsSolutions):
        super(UISolutionList, self).__init__(parent, model, 'Visutal Studio Solutions')
        self.vsSolutions = vsSolutions

    def CreateUI(self, parent):
        frame = UIFactory.AddFrame(parent, 0, 0, 50)

        for inx,sln in enumerate(self.vsSolutions.OtherSolutions):
            label = 'Open ' + self.vsSolutions.GetSlnName(sln)
            UIFactory.AddButton(frame, label, inx, 0, self.OnOpenSolution, (sln,), 19)
        self.AddBackButton(frame, 8, 0)

    def OnOpenSolution(self, sln):
        self.vsSolutions.OpenSolutionFile(sln)
