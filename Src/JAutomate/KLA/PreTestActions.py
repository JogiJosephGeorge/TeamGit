import os

from Common.FileOperations import FileOperations
from Common.PrettyTable import PrettyTable, TableFormat
from KlaModel.ConfigEncoder import ConfigEncoder
from KLA.IcosPaths import IcosPaths
from KLA.LicenseConfigWriter import LicenseConfigWriter
from KLA.TaskMan import TaskMan


class PreTestActions:
    @classmethod
    def CopyMockLicense(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        licenseFile = os.path.abspath(IcosPaths.GetMockLicensePath(*args))
        mmiPath = PreTestActions.GetMmiPath(model, toSrc)
        FileOperations.Copy(licenseFile, mmiPath)

    @classmethod
    def GetMmiPath(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        if toSrc:
            mmiPath = os.path.abspath(IcosPaths.GetMmiPath(*args))
        else:
            mmiPath = 'C:/icos'
        return mmiPath

    @classmethod
    def PrintAvailableExes(cls, model):
        data = [['Source', 'Available EXEs', 'Platform', 'Config']]
        for src,a,b in model.Sources:
            data.append(['-'])
            data.append([src])
            exePaths = []
            for pf in ConfigEncoder.Platforms:
                for cfg in ConfigEncoder.Configs:
                    exePaths.append((IcosPaths.GetMmiExePath(src, pf, cfg), pf, cfg))
                    exePaths.append((IcosPaths.GetConsolePath(src, pf, cfg), pf, cfg))
                    exePaths.append((IcosPaths.GetSimulatorPath(src, pf, cfg), pf, cfg))
                    exePaths.append((IcosPaths.GetMockLicensePath(src, pf, cfg), pf, cfg))
            for exePath, pf, cfg in exePaths:
                if os.path.exists(exePath):
                    data.append(['', exePath, pf, cfg])
        PrettyTable(TableFormat().SetSingleLine()).PrintTable(data)

    @classmethod
    def CopyxPortIllumRef(cls, model, delay = False):
        src = model.StartPath + '/DataFiles/xPort_IllumReference.xml'
        des = 'C:/icos/xPort/'
        if delay:
            TaskMan.AddTimer('xport', FileOperations.Copy(src, des, 8, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def GetTestPath(cls, model):
        return IcosPaths.GetTestPath(model.Source, model.TestName)

    @classmethod
    def GenerateLicMgrConfig(cls, model):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        LicenseConfigWriter(model.Source, src)

    @classmethod
    def CopyLicMgrConfig(cls, model, delay = False):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        #des = cls.GetTestPath(model) + '~/'
        des = 'C:/Icos'
        if delay:
            TaskMan.AddTimer('LicMgr', FileOperations.Copy(src, des, 9, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def CopyMmiSaveLogExe(cls, model):
        destin = IcosPaths.GetTestPathTemp(model.Source, model.TestName) + '/Icos'
        src = os.path.abspath(IcosPaths.GetMmiSaveLogsPath(model.Source, model.Platform, model.Config))
        FileOperations.Copy(src, destin)


class SourceCodeUpdater:
    @classmethod
    def ModifyVisionSystem(cls, model):
        linesToComment = [
            'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))',
            'self.copyFilesByType(os.path.join(sourceRoot, "MVSDConversions", platform), mvsdDestinationPath, [FileType.EXE, FileType.DLL])'
        ]
        fileName = os.path.abspath(model.Source + '/libs/testing/visionsystem.py')
        with open(fileName) as f:
            fileContent = f.read()
        fileModified = False
        for line in linesToComment:
            oldLine = ' ' + line
            newLine = ' #' + line
            if oldLine in fileContent:
                fileContent = fileContent.replace(oldLine, newLine)
                fileModified = True
        if fileModified:
            with open(fileName, "w") as f:
                f.write(fileContent)
            print fileName + ' has been modified.'
        else:
            print fileName + ' had already been modified.'

    @classmethod
    def CopyPreCommit(cls, model):
        des = model.Source + '/.git/hooks'
        if not os.path.exists(des + '/pre-commit'):
            src = model.StartPath + '/DataFiles/pre-commit'
            FileOperations.Copy(src, des)
