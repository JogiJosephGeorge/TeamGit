import os

from Common.FileOperations import FileOperations
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from Common.PrettyTable import PrettyTable
from KlaModel.ConfigEncoder import ConfigEncoder


class KlaRunner:
    def __init__(self, model):
        self.model = model
        self.SetWorkingDir()

    def OpenPython(self):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = self.model.Src.GetCur()
        #FileOperations.Delete('{}/libs/testing/myconfig.py'.format(curSrc.Source))
        self.CreateMyConfig()
        relFilePath = '/libs/testing/my.py'
        fileName = os.path.abspath(curSrc.Source + relFilePath)
        par = 'start python -i ' + fileName
        OsOperations.System(par, 'Starting my.py')

    def OpenPython_CCR(self):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = self.model.Src.GetCur()
        relFilePath = '/mmi/classic_custom_reporters/integration'
        fileName = 'ccr.py'
        os.chdir(curSrc.Source + relFilePath)
        par = 'start python -i ' + fileName
        OsOperations.System(par, 'Starting ' + fileName)

    def CreateMyConfig(self):
        curSrc = self.model.Src.GetCur()
        config = ConfigEncoder.GetBuildConfig(self.model)
        data = 'version = 0\n'
        data += 'prompt = False\n'
        data += 'console_config = r"{}"\n'.format(config[0])
        data += 'simulator_config = r"{}"\n'.format(config[0])
        data += 'mmiBuildConfiguration = r"{}"\n'.format(config)
        data += 'mmiConfigurationsPath = "{}"\n'.format(self.model.MMiConfigPath.replace('\\', '/'))
        data += 'platform = r"{}"\n'.format(curSrc.Platform)
        data += 'mmiSetupsPath = "{}"'.format(self.model.MMiSetupsPath.replace('\\', '/'))
        FileOperations.Write('{}/libs/testing/myconfig.py'.format(curSrc.Source), data)

    def PrintMissingIds(self):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = self.model.Src.GetCur()
        fileNames = [
            os.path.abspath(curSrc.Source + '/mmi/mmi/mmi_lang/mmi.h'),
            os.path.abspath(curSrc.Source + '/mmi/mmi/env/env_stringtable.h')]
        for fileName in fileNames:
            ids = []
            with open(fileName) as file:
                for line in file.read().splitlines():
                    parts = line.split()
                    if len(parts) == 3:
                        ids.append(int(parts[2]))
            print 'Missing IDs in ' + fileName
            singles = []
            sets = []
            lastId = 1
            for id in ids:
                if lastId + 2 == id:
                    singles.append(lastId + 1)
                elif lastId + 2 < id:
                    sets.append((lastId + 1, id - 1))
                lastId = max(lastId, id)
            PrettyTable.PrintArray([str(id).rjust(5) for id in singles], 15)
            pr = lambda st : '{:>6}, {:<6}{:<7}'.format('[' + str(st[0]), str(st[1]) + ']', '(' + str(st[1] - st[0]) + ')')
            PrettyTable.PrintArray([pr(st) for st in sets], 5)
            print

    def SetWorkingDir(self):
        wd = os.path.join(self.model.StartPath, self.model.TempDir)
        if not os.path.isdir(wd):
            os.mkdir(wd)
        os.chdir(wd)

