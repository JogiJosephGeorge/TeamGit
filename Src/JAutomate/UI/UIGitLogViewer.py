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
        OsOperations.ChDir(self.model.Source)
        self.gitLogModel = GitLogModel()
        self.textBoxCreator = TextBoxCreator(self.gitLogModel)
        self.checkBoxCreator = CheckBoxCreator()

        self.Row = 0
        self.AddTextRow(parent, 'Branch Name', 'BranchName', 40)
        self.AddTextRow(parent, '--pretty=format:', 'PrettyFormat', 40)
        self.AddTextRow(parent, '--date=format:', 'DateFormat', 40)
        self.AddTextRow(parent, '-n', 'Number', 5)
        self.AddCheckBox(parent, '--reverse', 'Reverse')
        self.AddCheckBox(parent, '--decorate', 'Decorate')
        self.AddCheckBox(parent, '--graph', 'Graph')
        self.AddCheckBox(parent, '--oneline', 'Oneline')
        #self.AddTextRow(parent, 'Out File', 'OutFile', 40)
        UIFactory.AddButton(parent, 'Print Log', self.Row, 0, self.PrintLog, None, 19)
        #UIFactory.AddButton(parent, 'Write Log', self.Row, 1, self.WriteLog)
        self.AddBackButton(parent, self.Row, 1)

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

    def AddTextRow(self, parent, label, attrName, width):
        UIFactory.AddLabel(parent, label, self.Row, 0)
        self.textBoxCreator.Add(parent, self.Row, 1, attrName, None, width)
        self.Row += 1

    def AddCheckBox(self, parent, label, attrName):
        self.checkBoxCreator.AddCheckBox(parent, self.Row, 0, label, self.gitLogModel, attrName, '', '', False, False)
        self.Row += 1
