import os

from Common.FileOperations import FileOperations
from Common.OsOperations import OsOperations
from Common.PrettyTable import PrettyTable
from KlaModel.ConfigEncoder import ConfigEncoder


class KlaRunner:
    def __init__(self, model):
        self.model = model
        self.SetWorkingDir()

    def OpenPython(self):
        curSrc = self.model.CurSrc()
        #FileOperations.Delete('{}/libs/testing/myconfig.py'.format(curSrc.Source))
        self.CreateMyConfig()
        fileName = os.path.abspath(curSrc.Source + '/libs/testing/my.py')
        par = 'start python -i ' + fileName
        OsOperations.System(par, 'Starting my.py')

    def CreateMyConfig(self):
        curSrc = self.model.CurSrc()
        config = ConfigEncoder.GetBuildConfig(self.model)
        data = 'version = 0\n'
        data += 'console_config = r"{}"\n'.format(config[0])
        data += 'simulator_config = r"{}"\n'.format(config[0])
        data += 'mmiBuildConfiguration = r"{}"\n'.format(config)
        data += 'mmiConfigurationsPath = "{}"\n'.format(self.model.MMiConfigPath.replace('\\', '/'))
        data += 'platform = r"{}"\n'.format(curSrc.Platform)
        data += 'mmiSetupsPath = "{}"'.format(self.model.MMiSetupsPath.replace('\\', '/'))
        FileOperations.Write('{}/libs/testing/myconfig.py'.format(curSrc.Source), data)

    def PrintMissingIds(self):
        curSrc = self.model.CurSrc()
        fileName = os.path.abspath(curSrc.Source + '/mmi/mmi/mmi_lang/mmi.h')
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

