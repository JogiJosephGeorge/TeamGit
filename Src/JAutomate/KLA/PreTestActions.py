import os

from Common.FileOperations import FileOperations
from Common.PrettyTable import PrettyTable, TableFormat
from Common.OsOperations import OsOperations
from KlaModel.ConfigEncoder import Config, Platform
from KLA.IcosPaths import IcosPaths
from KLA.LicenseConfigWriter import LicenseConfigWriter
from KLA.TaskMan import TaskMan


class PreTestActions:
    @classmethod
    def CopyMockLicense(cls, model, toSrc = True, initWait = 0):
        curSrc = model.Src.GetCur()
        args = (curSrc.Source, curSrc.Platform, curSrc.Config)
        licenseFile = os.path.abspath(IcosPaths.GetMockLicensePath(*args))
        mmiPath = PreTestActions.GetMmiPath(model, toSrc)
        cls.DelayedCopy(licenseFile, mmiPath, 'MockLic', initWait)

    @classmethod
    def GetMmiPath(cls, model, toSrc = True):
        curSrc = model.Src.GetCur()
        args = (curSrc.Source, curSrc.Platform, curSrc.Config)
        if toSrc:
            mmiPath = os.path.abspath(IcosPaths.GetMmiPath(*args))
        else:
            mmiPath = 'C:/icos'
        return mmiPath

    @classmethod
    def PrintAvailableExes(cls, model):
        data = [['Source', 'Solutions', 'Platform', 'Config']]
        for srcData in model.Src.GetAllSrcs():
            data.append(['-'])
            src = srcData.Source
            exePaths = cls.GetPossibleExePathsOnSource(srcData.Source)
            for solName, exePath, pf, cfg in exePaths:
                if os.path.exists(exePath):
                    data.append([src, solName, pf, cfg])
                    src = ''
            if src:
                data.append([src])
        PrettyTable(TableFormat().SetSingleLine()).PrintTable(data)

    @classmethod
    def GetPossibleExePathsOnSource(cls, source):
        exePaths = []
        for pf in Platform.GetList():
            for cfg in Config.GetList():
                exePaths += cls.GetPossibleExePathsOnConfig(source, pf, cfg)
        return exePaths

    @classmethod
    def ConfigExistsOnSource(cls, source, pf, cfg):
        exePaths = cls.GetPossibleExePathsOnConfig(source, pf, cfg)
        for solName, exePath, pf, cfg in exePaths:
            if not os.path.exists(exePath):
                return False
        return True

    @classmethod
    def GetPossibleExePathsOnConfig(cls, source, pf, cfg):
        exePaths = []
        exePaths.append(('Mmi', IcosPaths.GetMmiExePath(source, pf, cfg), pf, cfg))
        exePaths.append(('Console', IcosPaths.GetConsolePath(source, pf, cfg, False), pf, cfg))
        exePaths.append(('Simulator', IcosPaths.GetSimulatorPath(source, pf, cfg, False), pf, cfg))
        exePaths.append(('MockLicense', IcosPaths.GetMockLicensePath(source, pf, cfg), pf, cfg))
        return exePaths

    @classmethod
    def GetExistingConfigs(cls, source):
        configPlatforms = []
        for pf in Platform.GetList():
            for cfg in Config.GetList():
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
        curSrc = model.Src.GetCur()
        return IcosPaths.GetTestPath(curSrc.Source, model.AutoTests.TestName)

    @classmethod
    def GenerateLicMgrConfig(cls, model):
        curSrc = model.Src.GetCur()
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        LicenseConfigWriter(curSrc.Source, src)

    @classmethod
    def CopyLicMgrConfig(cls, model, initWait = 0):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        #des = cls.GetTestPath(model) + '~/'
        des = 'C:/Icos'
        cls.DelayedCopy(src, des, 'LicMgr', initWait)

    @classmethod
    def CopyMVSDConversion(cls, model, initWait = 0):
        timer = FileOperations.LazyCreateDir('C:/icos/Tools/', 'MVSDConversions', initWait, 3)
        timer.name = 'MVSDDir'
        TaskMan.AddTimer(timer.name, timer)

        curSrc = model.Src.GetCur()
        src = IcosPaths.GetMVSDConversionsPath(curSrc.Source, curSrc.Platform)
        des = 'C:/icos/Tools/MVSDConversions/'
        cls.DelayedCopy(src, des, 'MVSDContents', initWait)

    @classmethod
    def DelayedCopy(cls, src, des, timerName='', initWait=0):
        if initWait > 0:
            timer = FileOperations.Copy(src, des, initWait, 3)
            timer.name = timerName
            TaskMan.AddTimer(timerName, timer)
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def CopyMmiSaveLogExe(cls, model):
        curSrc = model.Src.GetCur()
        destin = IcosPaths.GetTestPathTemp(curSrc.Source, model.AutoTests.TestName) + '/Icos'
        src = os.path.abspath(IcosPaths.GetMmiSaveLogsPath(curSrc.Source, curSrc.Platform, curSrc.Config))
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
        curSrc = model.Src.GetCur()
        linesToComment = [
            'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))',
            'self.copyFilesByType(os.path.join(sourceRoot, "MVSDConversions", platform), mvsdDestinationPath, [FileType.EXE, FileType.DLL])'
        ]
        fileName = os.path.abspath(curSrc.Source + '/libs/testing/visionsystem.py')
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
        curSrc = model.Src.GetCur()
        desDir = curSrc.Source + '/.git/hooks'
        if not os.path.exists(desDir):
            return
        desPath = 'pre-commit'
        cd1 = os.getcwd()
        OsOperations.ChDir(desDir)
        newPreCommit = curSrc.Source + '/tools/Clangformat/pre-commit'
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
