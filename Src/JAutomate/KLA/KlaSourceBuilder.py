from datetime import datetime
import os
import re

from Common.Git import Git
from Common.FileOperations import FileOperations
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from Common.PrettyTable import TableFormat, PrettyTable
from KLA.VisualStudioSolutions import VisualStudioSolutions


class KlaSourceBuilder:
    def __init__(self, model, klaRunner, vsSolutions):
        self.model = model
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions

    def NotifyClean(self):
        return self.NotifyUser('Clean')

    def NotifyBuild(self):
        return self.NotifyUser('Build')

    def NotifyReset(self):
        modifiedSrcs = []
        for activeSrc in self.model.ActiveSrcs:
            source, config, platform = self.model.Sources[activeSrc]
            cnt = len(Git.ModifiedFiles(source))
            if cnt > 0:
                modifiedSrcs.append(source)
        if len(modifiedSrcs) > 0:
            msg = "The following source(s) contains local modifications. So can't reset"
            for src in modifiedSrcs:
                msg += '\n' + src
            MessageBox.ShowMessage(msg)
            return False
        return self.NotifyUser('Reset')

    def NotifyUser(self, message):
        if len(self.model.ActiveSrcs) == 0:
            MessageBox.ShowMessage('There are no active sources. Please select the required one.')
            return False
        title = message + ' Source'
        isAre = ' is'
        if len(self.model.ActiveSrcs) > 1:
            title += 's'
            isAre = 's are'
        fullMessage = 'The following source{} ready for {}ing.\n'.format(isAre, message)
        self.srcTuple = []
        for activeSrc in self.model.ActiveSrcs:
            source, config, platform = self.model.Sources[activeSrc]
            branch = Git.GetBranch(source)
            fullMessage += '\n{} ({} | {})\n{}\n'.format(source, platform, config, branch)
            self.srcTuple.append([source, branch, config, platform])
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
        for srcSet in self.srcTuple:
            src = srcSet[0]
            cnt = len(Git.ModifiedFiles(self.model.Source))
            if cnt > 0:
                Git.Commit(self.model, 'Temp')
            print 'Cleaning files in ' + src
            self.DeleteAllGitIgnoreFiles(src)
            with open(src + '/.gitignore', 'w') as f:
                f.writelines(str.join('\n', excludeDirs))
            Git.Clean(src, '-fd')
            print 'Reseting files in ' + src
            Git.ResetHard(src)
            if cnt > 0:
                Git.RevertLastCommit(src)
            if self.model.UpdateSubmodulesOnReset:
                Git.SubmoduleUpdate(self.model)
            print 'Cleaning completed for ' + src

    def DeleteAllGitIgnoreFiles(self, dirName):
        os.remove('{}/.gitignore'.format(dirName))
        for root, dirs, files in os.walk(dirName):
            if '.gitignore' in files and '.git' not in files:
                os.remove('{}/.gitignore'.format(root))

    def CleanSource(self):
        self.CallDevEnv(True)

    def BuildSource(self):
        self.CallDevEnv(False)

    def CallDevEnv(self, ForCleaning):
        buildOption = '/Clean' if ForCleaning else '/build'
        buildLoger = BuildLoger(self.model, ForCleaning)
        for source, branch, config, srcPlatform in self.srcTuple:
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
                params = [self.model.DevEnvCom, slnFile, buildOption, BuildConf, '/out', outFile]
                OsOperations.Popen(params, buildLoger.PrintMsg)
                buildLoger.EndSolution()
            buildLoger.EndSource(source)
        if len(self.model.ActiveSrcs) > 1 and not ForCleaning:
            print buildLoger.ConsolidatedOutput


class BuildLoger:
    def __init__(self, model, ForCleaning):
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
        self.AddOutput('Branch : ' + branch, True)
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
            self.AddOutput(table, True)
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

    def RemoveHandlerTemp(self):
        path = self.model.Source + '/handler'
        print 'Removing remp files from : ' + path
        tempFileTypes3 = [
            '.pdb',
            '.obj',
            '.pch',
            '.exp'
        ]
        tempFileTypes4 = [
            '.tlog'
        ]
        filterFun = lambda f : f[-4:] in tempFileTypes3 or f[-5:] in tempFileTypes4
        filesToDelete = FileOperations.GetAllFiles(path, filterFun)
        for file in filesToDelete:
            os.remove(file)
        print '{} files have been removed'.format(len(filesToDelete))

    def RemoveMvsTemp(self):
        path = 'C:/MVS8000'
        print 'Removing remp files from : ' + path
        tempFileTypes3 = [
            '.log',
            '.obj',
            '.pch',
            '.exp'
        ]
        tempFileTypes4 = [
            '.tlog'
        ]
        filterFun = lambda f : f[-4:] in tempFileTypes3 or f[-5:] in tempFileTypes4
        filesToDelete = FileOperations.GetAllFiles(path, filterFun)
        for file in filesToDelete:
            print file
