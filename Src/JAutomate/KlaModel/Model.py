from collections import OrderedDict
import json
import os

from KlaModel.AutoTestModel import AutoTestModel
from KlaModel.ConfigEncoder import ConfigEncoder
from KlaModel.ConfigInfo import ConfigInfo, Geometry


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

    def RemoveSource(self, index):
        srcCnt = len(self.model.Sources)
        if index < 0 or index >= srcCnt:
            return False
        del self.model.Sources[index]
        if index in self.model.ActiveSrcs:
            activeSrcInx = self.model.ActiveSrcs.index(index)
            del self.model.ActiveSrcs[activeSrcInx]
        for i in range(len(self.model.ActiveSrcs)):
            if self.model.ActiveSrcs[i] > index:
                self.model.ActiveSrcs[i] -= 1
        if index + 1 >= srcCnt:
            index -= 1
        self.model.SrcIndex = index
        if index >= 0:
            self.model.Source, self.model.Config, self.model.Platform = self.model.Sources[self.model.SrcIndex]
        else:
            self.model.Source = ''
        return True


class IniFile:
    def __init__(self, fileName):
        self.FileName = fileName

    def Open(self):
        self.IniData = {}
        if os.path.exists(self.FileName):
            try:
                with open(self.FileName) as f:
                    self.IniData = json.load(f)
            except:
                print 'There are issues in reading ' + self.FileName

    def ReadField(self, key, defValue):
        if key in self.IniData:
            return self.IniData[key]
        return defValue

    def ReadInt(self, key, defValue):
        value = self.ReadField(key, defValue)
        return int(value)

    def StartWriting(self):
        self.SaveData = OrderedDict()

    def Write(self, name, value):
        self.SaveData[name] = value

    def Save(self):
        with open(self.FileName, 'w') as f:
            json.dump(self.SaveData, f, indent=3)


class Model:
    def __init__(self):
        self.StartPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filePath = self.StartPath + '\\KlaRunner.ini'
        self.IniFile = IniFile(filePath)
        self.ConfigInfo = ConfigInfo()
        self.AutoTests = AutoTestModel()
        self.SrcCnf = SourceConfig(self)
        self.Config = ConfigEncoder.Configs[0]
        self.Platform = ConfigEncoder.Platforms[0]
        self.TestName = ''
        self.slots = []
        self.Geometry = Geometry()

    def ReadConfigFile(self):
        self.IniFile.Open()
        self.ConfigInfo.Read(self, self.IniFile)
        self.Geometry.Read(self, self.IniFile)

    def WriteConfigFile(self):
        self.IniFile.StartWriting()
        self.ConfigInfo.Write(self.IniFile, self)
        self.Geometry.Write(self.IniFile, self)
        self.IniFile.Save()

    def UpdateTest(self, index, writeToFile):
        if not self.AutoTests.IsValidIndex(index):
            return False
        if self.TestIndex == index:
            return False
        self.TestIndex = index
        [self.TestName, self.slots] = self.AutoTests.Tests[self.TestIndex]
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
