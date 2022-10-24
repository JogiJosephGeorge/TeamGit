# coding=utf-8
import os
import re
import shutil
import sys
from datetime import datetime

from Common.FileOperations import FileOperations
from Common.Git import Git
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from Common.PrettyTable import TableFormat, PrettyTable
from KLA.VMWareRunner import VMWareRunner
from KLA.VisualStudioSolutions import VisualStudioSolutions
from KlaModel.VsVersions import VsVersions


class KlaSourceBuilder:
    def __init__(self, model, vsSolutions):
        self.model = model
        self.vsSolutions = vsSolutions

    def NotifyClean(self):
        return self.NotifyUser('Clean')

    def NotifyBuild(self):
        return self.NotifyUser('Build')

    def NotifyReset(self):
        modifiedSrcs = []
        for srcData in self.model.Src.GetAllActiveSrcs():
            cnt = len(Git.ModifiedFiles(srcData.Source))
            if cnt > 0:
                modifiedSrcs.append(srcData.Source)
        if len(modifiedSrcs) > 0:
            msg = "The following source(s) contains local modifications. So can't reset"
            for src in modifiedSrcs:
                msg += '\n' + src
            MessageBox.ShowMessage(msg)
            return False
        return self.NotifyUser('Reset')

    def NotifyUser(self, message):
        activeSrcs = list(self.model.Src.GetAllActiveSrcs())
        if len(activeSrcs) == 0:
            MessageBox.ShowMessage('There are no active sources. Please select the required one.')
            return False
        title = message + ' Source'
        isAre = ' is'
        if len(activeSrcs) > 1:
            title += 's'
            isAre = 's are'
        fullMessage = 'The following source{} ready for {}ing.\n'.format(isAre, message)
        self.srcTuple = []
        for srcData in activeSrcs:
            branch = Git.GetBranch(srcData.Source)
            fullMessage += '\n{} ({} | {})\n{}\n'.format(srcData.Source, srcData.Platform, srcData.Config, branch)
            self.srcTuple.append([srcData.Source, branch, srcData.Config, srcData.Platform, srcData.VsVersion])
        fullMessage += '\nDo you want to continue {}ing?'.format(message)
        result = MessageBox.YesNoQuestion(title, fullMessage)
        print 'Yes' if result else 'No'
        return result

    def ResetSource(self):
        excludeDirs = [
            '/mmi/mmi/packages',
            '/Handler/FabLink/cpp/bin',
            '/Handler/FabLink/FabLinkLib/System32',
            ]
        if not self.model.CleanDotVsOnReset:
            excludeDirs += [
                '/mmi/mmi/.vs',
                '/handler/cpp/.vs',
            ]
        gitIgnoreHelper = GitIgnoreFilesHelper()
        for source, branch, config, srcPlatform, vsVersion in self.srcTuple:
            cnt = len(Git.ModifiedFiles(source))
            if cnt > 0:
                continue
                #Git.Commit(self.model, 'Temp')
            print 'Resetting files in ' + source
            gitIgnoreHelper.DeleteAllFiles(self.model, source)
            tempGitIgnoreFile = source + '/.gitignore'
            with open(tempGitIgnoreFile, 'w') as f:
                f.writelines(str.join('\n', excludeDirs))
            Git.Clean(source)
            print 'Reseting files in ' + source
            Git.ResetHard(source)
            #if cnt > 0:
            #    Git.RevertLastCommit(src)
            if self.model.UpdateSubmodulesOnReset:
                Git.SubmoduleUpdate(self.model)
            FileOperations.Delete(tempGitIgnoreFile)
            gitIgnoreHelper.RevertDeletedFiles()
            print 'Resetting completed for ' + source

    def CleanSource(self):
        self.CallDevEnv(True)

    def BuildSource(self):
        self.CallDevEnv(False)

    def CallDevEnv(self, ForCleaning):
        buildOption = '/Clean' if ForCleaning else '/build'
        buildLoger = BuildLoger(self.model, ForCleaning)
        for source, branch, config, srcPlatform, vsVersion in self.srcTuple:
            buildLoger.StartSource(source, branch)
            for sln, slnName in self.vsSolutions.GetSelectedSolutions():
                slnFile = os.path.abspath(source + '/' + sln)
                if not os.path.exists(slnFile):
                    print "Solution file doesn't exist : " + slnFile
                    continue
                platform = VisualStudioSolutions.GetPlatform(sln, srcPlatform)
                BuildConf = config + '|' + platform
                outFile = os.path.abspath(source + '/Out_' + slnName) + '.txt'

                buildLoger.StartSolution(sln, slnName, config, platform)
                devEnvCom = self.model.VsVersions.GetDevEnvCom(vsVersion)
                params = [devEnvCom, slnFile, buildOption, BuildConf, '/out', outFile]
                OsOperations.Popen(params, buildLoger.PrintMsg)
                buildLoger.EndSolution()
            buildLoger.EndSource(source)
        if len(self.srcTuple) > 1 and not ForCleaning:
            print buildLoger.ConsolidatedOutput


class GitIgnoreFilesHelper:
    def DeleteAllFiles(self, model, dirName):
        self.srcPaths = []
        #if os.path.exists('{}/.gitignore'.format(dirName)):
        #    srcPaths.append('{}/.gitignore'.format(dirName))
        for root, dirs, files in os.walk(dirName):
            if '.gitignore' in files:
                self.srcPaths.append('{}/.gitignore'.format(root))

        tempPath = os.path.join(model.StartPath, model.TempDir) + '/GitIgnore/'
        if os.path.exists(tempPath):
            shutil.rmtree(tempPath)
        os.mkdir(tempPath)

        self.desPaths = []
        for i in range(1, len(self.srcPaths) + 1):
            self.desPaths.append(tempPath + str(i))
        movedFiles = FileOperations.MoveFiles(self.srcPaths, self.desPaths)
        if len(movedFiles) != len(self.srcPaths):
            movedSrc = [item[0] for item in movedFiles]
            movedDes = [item[1] for item in movedFiles]
            revertedFiles = FileOperations.MoveFiles(movedDes, movedSrc)
            if len(revertedFiles) == len(movedFiles):
                MessageBox.ShowMessage('Issues in moving .gitignore files')
            else:
                MessageBox.ShowMessage('.gitignore files are are moved partially')

    def RevertDeletedFiles(self):
        FileOperations.MoveFiles(self.desPaths, self.srcPaths)


class BuildLoger:
    def __init__(self, model, ForCleaning):
        self.model = model
        if ForCleaning:
            self.fileName = model.StartPath + '/bin/BuildLog.txt'
        else:
            timeStamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.fileName = '{}/bin/BuildLog_{}.txt'.format(model.StartPath, timeStamp)
        self.ForCleaning = ForCleaning
        self.message = 'cleaning' if ForCleaning else 'building'
        if not os.path.exists(self.fileName):
            print "File created : " + self.fileName
            FileOperations.Write(self.fileName, '')
        self.ConsolidatedOutput = ''

    def AddOutput(self, message, doLog):
        self.ConsolidatedOutput += message
        self.ConsolidatedOutput += '\n'
        if doLog:
            self.Log(message)

    def StartSource(self, src, branch):
        self.srcStartTime = datetime.now()
        self.AddOutput('Source : ' + src, True)
        commitId = Git.GetCommitId(src)
        branchWithCommit = branch + ' (' + commitId + ')'
        self.AddOutput('Branch : ' + branchWithCommit, True)
        self.logDataTable = [
            [ 'Solution', 'Config', 'Platform', 'Succeeded', 'Failed', 'Up To Date', 'Skipped', 'Time Taken' ],
            ['-']
        ]

    def EndSource(self, src):
        timeDelta = self.TimeDeltaToStr(datetime.now() - self.srcStartTime)
        self.Log('Completed {} {} in {}'.format(self.message, src, timeDelta))
        if not self.ForCleaning:
            self.logDataTable.append(['-'])
            self.logDataTable.append([''] * 7 + [timeDelta])
            table = '\n' + PrettyTable(TableFormat().SetSingleLine()).ToString(self.logDataTable)
            self.AddOutput(table, False)
            FileOperations.Append(self.fileName, table)

    def StartSolution(self, slnFile, name, config, platform):
        self.Log('Start {} : {}'.format(self.message, slnFile))
        self.slnStartTime = datetime.now()
        self.logDataRow = [name, config, platform]

    def EndSolution(self):
        if len(self.logDataRow) == 3:
            self.logDataRow += [''] * 4
        timeDelta = self.TimeDeltaToStr(datetime.now() - self.slnStartTime)
        self.logDataRow.append(timeDelta)
        self.logDataTable.append(self.logDataRow)

    def Log(self, message):
        print message
        message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
        FileOperations.Append(self.fileName, message)

    def PrintMsg(self, message):
        if '>----' in message:
            if self.model.ShowBuildInProgress:
                print message
        elif '=====' in message:
            print message
            nums = self.GetBuildStatus(message)
            if nums:
                self.logDataRow += nums

    def GetBuildStatus(self, message):
        searchPattern = r'Build: (\d*) succeeded, (\d*) failed, (\d*) up-to-date, (\d*) skipped'
        m = re.search(searchPattern, message, re.IGNORECASE)
        if m:
            return [(int(m.group(i))) for i in range(1, 5)]

    @classmethod
    def TimeDeltaToStr(self, delta):
        s = delta.seconds
        t = '{:02}:{:02}:{:02}'.format(s // 3600, s % 3600 // 60, s % 60)
        return t


class KlaSourceCleaner:
    def __init__(self, model):
        self.model = model

    def DoOnAllActiveSrc(self, func):
        activeSrcs = list(self.model.Src.GetAllActiveSrcs())
        if len(activeSrcs) == 0:
            MessageBox.ShowMessage('There is no active source.')
        for activeSrc in activeSrcs:
            func(activeSrc.Source)

    def RemoveAllHandlerTemp(self):
        self.DoOnAllActiveSrc(self.RemoveHandlerTemp)
        print 'All temporary folders are removed.'

    def RemoveHandlerTemp(self, source):
        path = source + '/handler'
        print 'Removing temp files from : ' + path
        count = 0
        for file in FileOperations.GetAllFiles(path, self.CanDelete):
            os.remove(file)
            count += 1
        print '{} files have been removed'.format(count)

    def CanDelete(self, fileName):
        excludedPaths = [
            'handler\\FabLink\\FabLinkLib\\System32\\Release',
            'handler\\cpp\MiniZIP'
        ]
        if 'iniZIP' in fileName.lower():
            print fileName
        for path in excludedPaths:
            if path in fileName:
                return False
        for tempFileType in [
            '.pdb',
            '.obj',
            '.pch',
            '.exp',
            '.tlog'
        ]:
            if fileName.endswith(tempFileType):
                return True
        return False

    def RemoveAllTilt(self):
        self.DoOnAllActiveSrc(self.RemoveAllTiltOnSrc)
        print 'All temporary folders are removed.'

    def RemoveAllTiltOnSrc(self, source):
        filterFun = lambda d: d[-1] == '~'
        print 'Removing all auto test temporary folders on : ' + str(source)
        count = 0
        for dir in FileOperations.GetAllDirs(source, filterFun):
            print dir
            shutil.rmtree(dir)
            count += 1
        print '{} directories have been removed'.format(count)

    def RemoveMvsTemp(self):
        mvsPaths = VMWareRunner.GetAllMvsPaths()
        print 'Removing temp files from : ' + str(mvsPaths)

        filterDirFun = lambda f : f[:4] == 'logs'
        dirsToDelete = []
        for mvsPath in mvsPaths:
            for p in FileOperations.GetAllDirs(mvsPath, filterDirFun):
                dirsToDelete.append(p)
        for dir in dirsToDelete:
            shutil.rmtree(dir)

        tempFileTypes = [
            '.log',
            '.tga',
            '.dump'
        ]

        mvsPaths = VMWareRunner.GetAllMvsPaths()
        filterFun = lambda fileName : any(fileName.endswith(tempType) for tempType in tempFileTypes)
        filesToDelete = FileOperations.GetAllFilesFromList(mvsPaths, filterFun)
        for file in filesToDelete:
            os.remove(file)
        print '{} files have been removed'.format(len(filesToDelete))

def main():
    # This will not work with KLA Runner. Stop All apps will close this also.
    if __name__ == '__main__' and len(sys.argv) == 2:
        param1 = sys.argv[1].lower()
        if param1 == 'build':
            from KlaModel import Model
            from KLA import VisualStudioSolutions
            model = Model.Model()
            model.ReadFromFile()
            vsSolutions = VisualStudioSolutions.VisualStudioSolutions(model)
            vsSolutions.Init()
            builder = KlaSourceBuilder(model, vsSolutions)
            if builder.NotifyBuild():
                builder.BuildSource()

main()
