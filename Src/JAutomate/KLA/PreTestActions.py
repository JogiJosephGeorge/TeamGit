import os

from Common.FileOperations import FileOperations
from Common.PrettyTable import PrettyTable, TableFormat
from Common.OsOperations import OsOperations
from KlaModel.ConfigEncoder import ConfigEncoder
from KLA.IcosPaths import IcosPaths
from KLA.LicenseConfigWriter import LicenseConfigWriter
from KLA.TaskMan import TaskMan


class PreTestActions:
    @classmethod
    def CopyMockLicense(cls, model, toSrc = True, initWait = 0):
        args = (model.Source, model.Platform, model.Config)
        licenseFile = os.path.abspath(IcosPaths.GetMockLicensePath(*args))
        mmiPath = PreTestActions.GetMmiPath(model, toSrc)
        cls.DelayedCopy(licenseFile, mmiPath, 'MockLic', initWait)

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
        for src,c,p in model.Sources:
            data.append(['-'])
            data.append([src])
            exePaths = cls.GetPossibleExePathsOnSource(src)
            for exePath, pf, cfg in exePaths:
                if os.path.exists(exePath):
                    data.append(['', exePath, pf, cfg])
        PrettyTable(TableFormat().SetSingleLine()).PrintTable(data)

    @classmethod
    def GetPossibleExePathsOnSource(cls, source):
        exePaths = []
        for pf in ConfigEncoder.Platforms:
            for cfg in ConfigEncoder.Configs:
                exePaths += cls.GetPossibleExePathsOnConfig(source, pf, cfg)
        return exePaths

    @classmethod
    def ConfigExistsOnSource(cls, source, pf, cfg):
        exePaths = cls.GetPossibleExePathsOnConfig(source, pf, cfg)
        for exePath, pf, cfg in exePaths:
            if not os.path.exists(exePath):
                return False
        return True

    @classmethod
    def GetPossibleExePathsOnConfig(cls, source, pf, cfg):
        exePaths = []
        exePaths.append((IcosPaths.GetMmiExePath(source, pf, cfg), pf, cfg))
        exePaths.append((IcosPaths.GetConsolePath(source, pf, cfg), pf, cfg))
        exePaths.append((IcosPaths.GetSimulatorPath(source, pf, cfg), pf, cfg))
        exePaths.append((IcosPaths.GetMockLicensePath(source, pf, cfg), pf, cfg))
        return exePaths

    @classmethod
    def GetExistingConfigs(cls, source):
        configPlatforms = []
        for pf in ConfigEncoder.Platforms:
            for cfg in ConfigEncoder.Configs:
                if cls.ConfigExistsOnSource(source, pf, cfg):
                    configPlatforms.append((pf, cfg))
        return configPlatforms

    @classmethod
    def CopyxPortIllumRef(cls, model, initWait = 0):
        src = model.StartPath + '/DataFiles/xPort_IllumReference.xml'
        des = 'C:/icos/xPort/'
        cls.DelayedCopy(src, des, 'xport', initWait)

    @classmethod
    def GetTestPath(cls, model):
        return IcosPaths.GetTestPath(model.Source, model.TestName)

    @classmethod
    def GenerateLicMgrConfig(cls, model):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        LicenseConfigWriter(model.Source, src)

    @classmethod
    def CopyLicMgrConfig(cls, model, initWait = 0):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        #des = cls.GetTestPath(model) + '~/'
        des = 'C:/Icos'
        cls.DelayedCopy(src, des, 'LicMgr', initWait)

    @classmethod
    def DelayedCopy(cls, src, des, timerName='', initWait=0):
        if initWait > 0:
            TaskMan.AddTimer(timerName, FileOperations.Copy(src, des, initWait, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def CopyMmiSaveLogExe(cls, model):
        destin = IcosPaths.GetTestPathTemp(model.Source, model.TestName) + '/Icos'
        src = os.path.abspath(IcosPaths.GetMmiSaveLogsPath(model.Source, model.Platform, model.Config))
        FileOperations.Copy(src, destin)

    @classmethod
    def DownloadAutoPlayTestModelFiles(cls, testName, configPath):
        testName = testName.replace('\\', '/')
        if not testName.lower().startswith('mmi/autoplay'):
            print 'Selected test is NOT an auto play test : ' + testName
            return
        testName = testName[4:]
        print 'Downloading started : ' + testName
        remotePath = IcosPaths.GetAutoplyPath()
        src = remotePath + testName
        des = configPath + 'Configurations/' + testName
        if not os.path.exists(des):
            os.mkdir(des)
        FileOperations.Copy(src, des)
        print 'Completed Downloading : ' + testName


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
        desDir = model.Source + '/.git/hooks'
        if not os.path.exists(desDir):
            return
        desPath = 'pre-commit'
        cd1 = os.getcwd()
        OsOperations.ChDir(desDir)
        newPreCommit = model.Source + '/tools/Clangformat/pre-commit'
        if os.path.exists(newPreCommit):
            if os.path.exists(desPath):
                #if os.path.islink(desPath):  # This doesn't work at all
                if os.stat(desPath).st_size == 0:
                    return
                os.remove(desPath)
            params = u'mklink pre-commit ..\\..\\tools\\Clangformat\\pre-commit'
            os.system(params)
        else:
            src = model.StartPath + '/DataFiles/pre-commit'
            FileOperations.Copy(src, desDir)
        OsOperations.ChDir(cd1)

    @classmethod
    def PauseMmiAtInit(cls, model):
        fileName = 'D:/CI/Src1/libs/testing/handlerprocesses.py'
        # Find last import line
        # Insert this line after that import tkMessageBox

        # Find method def startDelayTesthost(
        # Find the line 'p.testhost.start()' after trimming
        # Insert the line before that
        # tkMessageBox.showinfo('KLA Runner', 'Press OK to start MMI.exe')

        # If tk is not working, we can try the old way
        #print "\n\nGoing to start MMI.exe"  # JJG
        #os.system("pause")

        pass
