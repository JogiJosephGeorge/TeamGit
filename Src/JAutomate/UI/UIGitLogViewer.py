import os

from Common.Git import Git
from Common.OsOperations import OsOperations
from Common.UIFactory import UIFactory, TextBoxCreator, CheckBoxCreator
from UI.UIWindow import UIWindow


class GitLogModel:
    def __init__(self):
        self.BranchName = ''
        self.PrettyFormat = '%h - %p - %an, %ad : %s'
        self.DateFormat = '%Y-%m-%d %H:%M:%S'
        self.Number = 4
        self.Reverse = False
        self.Decorate = False
        self.Graph = False
        self.Oneline = True
        self.WriteToFile = False
        self.OutFile = 'D:/out.txt'

    def GetCmd(self):
        cmd = 'log '
        if len(self.BranchName) > 0:
            cmd += self.BranchName + ' '
        if self.Oneline:
            cmd += '--oneline '
        if len(self.PrettyFormat) > 0:
            cmd += '--pretty=format:"{}" '.format(self.PrettyFormat)
        if len(self.DateFormat) > 0:
            cmd += '--date=format:"{}" '.format(self.DateFormat)
        if self.Reverse:
            cmd += '--reverse '
        if self.Decorate:
            cmd += '--decorate '
        if self.Graph:
            cmd += '--graph '
        if self.Number > 0:
            cmd += '-n {} '.format(self.Number)
        if self.WriteToFile and len(self.OutFile) > 0:
            cmd += ' > {}" '.format(self.OutFile)
        return cmd

class UIGitLogViewer(UIWindow):
    def __init__(self, parent, model):
        self.model = model
        super(UIGitLogViewer, self).__init__(parent, model, 'Git Log Viewer')

    def CreateUI(self, parent):
        curSrc = self.model.Src.GetCur()
        OsOperations.ChDir(curSrc.Source)
        self.gitLogModel = GitLogModel()
        self.textBoxCreator = TextBoxCreator(self.gitLogModel)
        self.checkBoxCreator = CheckBoxCreator()

        self.CreateColumnFrame(parent, 0)
        self.AddTextRow('Branch Name', 'BranchName', 40)
        self.AddTextRow('--pretty=format:', 'PrettyFormat', 40)
        self.AddTextRow('--date=format:', 'DateFormat', 40)
        self.AddTextRow('-n', 'Number', 5)
        self.AddCheckBox('--reverse', 'Reverse')
        self.AddCheckBox('--decorate', 'Decorate')
        self.AddCheckBox('--graph', 'Graph')
        self.AddCheckBox('--oneline', 'Oneline')
        self.AddTextRow('Out File', 'OutFile', 40)

        self.CreateColumnFrame(parent, 1)
        self.AddButton('Print Log', self.PrintLog)
        self.AddButton('Write Log', self.WriteLog)

        self.CreateColumnFrame(parent, 2)
        self.AddButton('Clear Output', OsOperations.Cls)
        self.AddBackButton(self.RowFrame, self.Row, self.Col)

    def CreateColumnFrame(self, parent, r):
        self.Row = 0
        self.Col = 0
        self.RowFrame = UIFactory.AddFrame(parent, r, 0)

    def AddButton(self, txt, cmd):
        UIFactory.AddButton(self.RowFrame, txt, self.Row, self.Col, cmd, None, 19)
        self.Col += 1

    def PrintLog(self):
        self.gitLogModel.WriteToFile = False
        self.Log()

    def WriteLog(self):
        self.gitLogModel.WriteToFile = True
        self.Log()

    def Log(self):
        self.textBoxCreator.UpdateModel()
        cmd = self.gitLogModel.GetCmd()
        OsOperations.Call('git {}'.format(cmd))

    def AddTextRow(self, label, attrName, width):
        UIFactory.AddLabel(self.RowFrame, label, self.Row, 0)
        self.textBoxCreator.Add(self.RowFrame, self.Row, 1, attrName, None, width)
        self.Row += 1

    def AddCheckBox(self, label, attrName):
        self.checkBoxCreator.AddCheckBox(self.RowFrame, self.Row, 0, label, self.gitLogModel, attrName, '', '', False, False)
        self.Row += 1
