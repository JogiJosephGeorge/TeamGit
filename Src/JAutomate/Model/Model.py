import json
import os
from collections import OrderedDict

from Common.PrettyTable import TableFormat, PrettyTable

class ConfigEncoder:
    Configs = ['Debug', 'Release']
    Platforms = ['Win32', 'x64']

    @classmethod
    def DecodeSource(cls, srcStr):
        source = srcStr[4:]
        config = cls.Configs[srcStr[0] == 'R']
        platform = cls.Platforms[srcStr[1:3] == '64']
        return (source, config, platform)

    @classmethod
    def EncodeSource(cls, srcSet):
        return srcSet[1][0] + srcSet[2][-2:] + ' ' + srcSet[0]

    @classmethod
    def GetBuildConfig(cls, model):
        debugConfigSet = ('debugx64', 'debug')
        releaseConfigSet = ('releasex64', 'release')
        configSet = (debugConfigSet, releaseConfigSet)[model.Config == cls.Configs[1]]
        # releasex64 is not working
        # return configSet[model.Platform == cls.Platforms[0]]
        return configSet[1]

    @classmethod
    def AddSrc(cls, model, newSrcPath):
        for srcSet in model.Sources:
            if newSrcPath == srcSet[0]:
                return
        model.Sources.append((newSrcPath, cls.Configs[0], cls.Platforms[0]))
        model.Source = newSrcPath
        if model.SrcIndex < 0:
            model.SrcIndex = 0

class AutoTestModel:
    def __init__(self):
        self.Tests = []

    def Read(self, testArray):
        self.Tests = []
        for item in testArray:
            nameSlot = self.Encode(item)
            if nameSlot is not None:
                self.Tests.append(nameSlot)

    def Write(self):
        return [self.Decode(item[0], item[1]) for item in self.Tests]

    def IsValidIndex(self, index):
        return index >= 0 and index < len(self.Tests)

    def GetNames(self):
        return [item[0] for item in self.Tests]

    def GetNameSlots(self, index):
        return self.Tests[index]

    def SetNameSlots(self, index, name, slots):
        self.Tests[index] = [name, slots]

    def Contains(self, testName):
        for inx, item in self.Tests:
            if testName in item[0]:
                return inx

    def AddTestToModel(self, testName):
        slots = [1, 2, 3, 4]
        for item in self.Tests:
            if item[0] == testName:
                return -1
        self.Tests.append([testName, slots])
        return len(self.Tests) - 1

    def Encode(self, testNameSlots):
        parts = testNameSlots.split()
        if len(parts) > 1:
            return (parts[0], map(int, parts[1].split('_')))
        elif len(parts) > 0:
            return (parts[0], [])

    def Decode(self, testName, slots):
        slotStrs = [str(slot) for slot in slots]
        return '{} {}'.format(testName, '_'.join(slotStrs))

    def ToString(self):
        data = []
        index = 0
        for item in self.Tests:
            data.append([ str(index), str(item[0]), str(item[1]) ])
            index += 1
        return PrettyTable(TableFormat().SetSingleLine()).ToString(data)

class ConfigInfo:
    def __init__(self, fileName):
        self.FileName = fileName

    def Read(self, model):
        if os.path.exists(self.FileName):
            with open(self.FileName) as f:
                _model = json.load(f)
        else:
            _model = {}

        model.Source = ''
        model.Branch = ''
        model.slots = []
        model.SrcIndex = -1
        model.TestIndex = -1
        Sources = self.ReadField(_model, 'Sources', [])
        model.Sources = [ConfigEncoder.DecodeSource(item) for item in Sources]
        SrcIndex = self.ReadField(_model, 'SrcIndex', -1)
        model.SrcCnf.UpdateSource(SrcIndex, False)
        Tests = self.ReadField(_model, 'Tests', [])
        model.AutoTests.Read(Tests)
        TestIndex = self.ReadField(_model, 'TestIndex', -1)
        if not model.UpdateTest(TestIndex, False):
            model.TestIndex = 0
        model.ActiveSrcs = self.ReadField(_model, 'ActiveSrcs', [])
        model.DevEnvCom = self.ReadField(_model, 'DevEnvCom', 'C:/Program Files (x86)/Microsoft Visual Studio 12.0/Common7/IDE/devenv.com')
        model.DevEnvExe = self.ReadField(_model, 'DevEnvExe', 'C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional/Common7/IDE/devenv.exe')
        model.GitBin = self.ReadField(_model, 'GitBin', 'C:/Program Files/Git/bin')
        model.VMwareWS = self.ReadField(_model, 'VMwareWS', 'C:/Program Files (x86)/VMware/VMware Workstation')
        model.EffortLogFile = self.ReadField(_model, 'EffortLogFile', 'D:/QuEST/Tools/EffortCapture_2013/timeline.log')
        model.BCompare = self.ReadField(_model, 'BCompare', 'C:/Program Files (x86)/Beyond Compare 4/BCompare.exe')
        model.MMiConfigPath = self.ReadField(_model, 'MMiConfigPath', 'D:\\')
        model.MMiSetupsPath = self.ReadField(_model, 'MMiSetupsPath', 'D:/MmiSetups')
        model.StartOnly = self.ReadField(_model, 'StartOnly', False)
        model.DebugVision = self.ReadField(_model, 'DebugVision', False)
        model.CopyMmi = self.ReadField(_model, 'CopyMmi', True)
        model.TempDir = self.ReadField(_model, 'TempDir', 'bin')
        model.LogFileName = self.ReadField(_model, 'LogFileName', 'bin/Log.txt')
        model.MenuColCnt = self.ReadField(_model, 'MenuColCnt', 4)
        model.MaxSlots = self.ReadField(_model, 'MaxSlots', 8)
        model.ShowAllButtons = self.ReadField(_model, 'ShowAllButtons', False)
        model.RestartSlotsForMMiAlone = self.ReadField(_model, 'RestartSlotsForMMiAlone', False)
        model.GenerateLicMgrConfigOnTest = self.ReadField(_model, 'GenerateLicMgrConfigOnTest', False)
        model.CopyMockLicenseOnTest = self.ReadField(_model, 'CopyMockLicenseOnTest', False)
        model.CopyExportIllumRefOnTest = self.ReadField(_model, 'CopyExportIllumRefOnTest', False)
        model.CleanDotVsOnReset = self.ReadField(_model, 'CleanDotVsOnReset', False)
        model.UpdateSubmodulesOnReset = self.ReadField(_model, 'UpdateSubmodulesOnReset', False)

        model.MMiConfigPath = model.MMiConfigPath.replace('/', '\\')

    def ReadField(self, model, key, defValue):
        if key in model:
            return model[key]
        return defValue

    def Write(self, model):
        _model = OrderedDict()
        _model['Sources'] = [ConfigEncoder.EncodeSource(item) for item in model.Sources]
        _model['SrcIndex'] = model.SrcIndex
        _model['ActiveSrcs'] = model.ActiveSrcs
        _model['Tests'] = model.AutoTests.Write()
        _model['TestIndex'] = model.TestIndex
        _model['DevEnvCom'] = model.DevEnvCom
        _model['DevEnvExe'] = model.DevEnvExe
        _model['GitBin'] = model.GitBin
        _model['VMwareWS'] = model.VMwareWS
        _model['EffortLogFile'] = model.EffortLogFile
        _model['BCompare'] = model.BCompare
        _model['MMiConfigPath'] = model.MMiConfigPath
        _model['MMiSetupsPath'] = model.MMiSetupsPath
        _model['StartOnly'] = model.StartOnly
        _model['DebugVision'] = model.DebugVision
        _model['CopyMmi'] = model.CopyMmi
        _model['TempDir'] = model.TempDir
        _model['LogFileName'] = model.LogFileName
        _model['MenuColCnt'] = model.MenuColCnt
        _model['MaxSlots'] = model.MaxSlots
        _model['ShowAllButtons'] = model.ShowAllButtons
        _model['RestartSlotsForMMiAlone'] = model.RestartSlotsForMMiAlone
        _model['GenerateLicMgrConfigOnTest'] = model.GenerateLicMgrConfigOnTest
        _model['CopyMockLicenseOnTest'] = model.CopyMockLicenseOnTest
        _model['CopyExportIllumRefOnTest'] = model.CopyExportIllumRefOnTest
        _model['CleanDotVsOnReset'] = model.CleanDotVsOnReset
        _model['UpdateSubmodulesOnReset'] = model.UpdateSubmodulesOnReset

        with open(self.FileName, 'w') as f:
            json.dump(_model, f, indent=3)

class SourceConfig:
    def __init__(self, model):
        self.model = model

    def UpdateSource(self, index, writeToFile):
        if index < 0 or index >= len(self.model.Sources):
            return False
        if self.model.SrcIndex == index:
            return False
        self.model.SrcIndex = index
        self.model.Source, self.model.Config, self.model.Platform = self.model.Sources[self.model.SrcIndex]
        #self.model.Branch = Git.GetBranch(self.model.Source)
        if writeToFile:
            self.model.WriteConfigFile()
        return True

class Model:
    def __init__(self):
        self.StartPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filePath = self.StartPath + '\\KlaRunner.ini'
        self.ConfigInfo = ConfigInfo(filePath)
        self.AutoTests = AutoTestModel()
        self.SrcCnf = SourceConfig(self)
        self.Config = ConfigEncoder.Configs[0]
        self.Platform = ConfigEncoder.Platforms[0]

    def ReadConfigFile(self):
        self.ConfigInfo.Read(self)

    def WriteConfigFile(self):
        self.ConfigInfo.Write(self)

    def UpdateTest(self, index, writeToFile):
        if not self.AutoTests.IsValidIndex(index):
            return False
        if self.TestIndex == index:
            return False
        self.TestIndex = index
        [self.TestName, self.slots] = self.AutoTests.GetNameSlots(self.TestIndex)
        if writeToFile:
            self.WriteConfigFile()
        return True

    def UpdateConfig(self, row, index):
        if index < 0 or index >= len(ConfigEncoder.Configs):
            return False
        srcTuple = self.Sources[row]
        newConfig = ConfigEncoder.Configs[index]
        if self.SrcIndex == row and srcTuple[1] == newConfig:
            return False
        if self.SrcIndex == row:
            self.Config = newConfig
        srcTuple = srcTuple[0], newConfig, srcTuple[2]
        self.Sources[row] = srcTuple
        return True

    def UpdatePlatform(self, row, index):
        if index < 0 or index >= len(ConfigEncoder.Platforms):
            return False
        srcTuple = self.Sources[row]
        newPlatform = ConfigEncoder.Platforms[index]
        if self.SrcIndex == row and srcTuple[2] == newPlatform:
            return False
        if self.SrcIndex == row:
            self.Platform = newPlatform
        srcTuple = srcTuple[0], srcTuple[1], newPlatform
        self.Sources[row] = srcTuple
        return True

    def UpdateSlot(self, index, isSelected):
        slotNum = index + 1
        if isSelected:
            self.slots.append(slotNum)
            self.slots.sort()
        else:
            self.slots.remove(slotNum)
        self.AutoTests.SetNameSlots(self.TestIndex, self.TestName, self.slots)

    def SelectSlots(self, slots):
        self.slots = slots
        self.slots.sort()
        self.AutoTests.SetNameSlots(self.TestIndex, self.TestName, self.slots)

    def GetLibsTestPath(self):
        return self.Source + '/libs/testing'

    def TestInfoToString(self):
        msg  = 'Current Test Index : ' + str(self.TestIndex) + '\n'
        msg += 'Current Test Name  : ' + self.TestName + '\n'
        msg += 'Current Slots        : ' + str(self.slots) + '\n'
        return msg
