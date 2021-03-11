from Common.UIFactory import UIFactory


class UIGrid:
    def __init__(self, parent, threadHandler):
        self.Col = 0
        self.parent = parent
        self.threadHandler = threadHandler

    def CreateColumnFrame(self):
        self.ColFrame = UIFactory.AddFrame(self.parent, 0, self.Col, sticky='n')
        self.Col += 1
        self.RowInx = 0

    def AddParallelButton(self, label, FunPnt, args = None, InitFunPnt = None):
        self.threadHandler.AddButton(self.ColFrame, label, self.RowInx, 0, FunPnt, args, InitFunPnt, None)
        self.RowInx += 1

    def AddButton(self, label, FunPnt, args = None):
        but = UIFactory.AddButton(self.ColFrame, label, self.RowInx, 0, FunPnt, args, 19)
        self.RowInx += 1
