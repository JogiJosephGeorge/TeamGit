from collections import OrderedDict
import json
import os

from KlaModel.AutoTestModel import AutoTestModel
from KlaModel.ConfigEncoder import Config, Platform
from KlaModel.ConfigInfo import ConfigInfo, Geometry


class SrcData:
    def __init__(self):
        self.Source = ''
        self.Config = Config.Debug
        self.Platform = Platform.Win32
        self.IsActive = False
        self.Description = ''

    @classmethod
    def CreateFromJson(cls, jsonData):
        srcData = SrcData()
        srcData.Source = cls.ReadField(jsonData, 'Source', '')
        srcData.Config = cls.ReadField(jsonData, 'Config', Config.Debug)
        srcData.Platform = cls.ReadField(jsonData, 'Platform', Platform.Win32)
        srcData.IsActive = cls.ReadField(jsonData, 'IsActive', False)
        srcData.Description = cls.ReadField(jsonData, 'Description', '')
        return srcData

    @classmethod
    def ReadField(self, jsonData, key, defValue):
        if key in jsonData:
            return jsonData[key]
        return defValue

    def GetJsonData(self):
        jsonData = {}
        jsonData['Source'] = self.Source
        jsonData['Config'] = self.Config
        jsonData['Platform'] = self.Platform
        jsonData['IsActive'] = self.IsActive
        jsonData['Description'] = self.Description
        return jsonData


class SourceInfo:
    def __init__(self, model):
        self.model = model
        self.SrcArray = []

    def Read(self, iniFile):
        self.model.SrcIndex = -1
        if iniFile.HasKey('SourceInfo'):
            # Read New Data from New Version
            sourceInfo = iniFile.ReadField('SourceInfo', [])
            del self.SrcArray[:]
            for srcJson in sourceInfo:
                srcData = SrcData.CreateFromJson(srcJson)
                self.SrcArray.append(srcData)
        else:
            # Read New Data from Old Version
            ActiveSrcs = iniFile.ReadField('ActiveSrcs', [])
            del self.SrcArray[:]
            index = 0
            Sources = iniFile.ReadField('Sources', [])
            for srcStr in Sources:
                srcData = SrcData()
                srcData.Source = srcStr[4:]
                srcData.Config = Config.Release if srcStr[0] == 'R' else Config.Debug
                srcData.Platform = Platform.x64 if srcStr[1:3] == '64' else Platform.Win32
                srcData.IsActive = index in ActiveSrcs
                self.SrcArray.append(srcData)
                index += 1
        SrcIndex = iniFile.ReadField('SrcIndex', -1)
        self.UpdateSource(SrcIndex, False)

    def Write(self, iniFile):
        iniFile.Write('SrcIndex', self.model.SrcIndex)

        sourceInfo = []
        for src in self.SrcArray:
            srcItem = src.GetJsonData()
            sourceInfo.append(srcItem)
        iniFile.Write('SourceInfo', sourceInfo)

    def UpdateSource(self, index, writeToFile):
        if index < 0 or index >= len(self.SrcArray):
            return False
        if self.model.SrcIndex == index:
            return False
        self.model.SrcIndex = index
        if writeToFile:
            self.model.WriteConfigFile()
        return True

    def AddSource(self, newPath):
        for srcData in self.SrcArray:
            if newPath == srcData.Source:
                return False
        srcData = SrcData()
        srcData.Source = newPath
        self.SrcArray.append(srcData)
        if self.model.SrcIndex < 0:
            self.model.SrcIndex = 0
        return True

    def RemoveSource(self, index):
        srcCnt = len(self.SrcArray)
        if index < 0 or index >= srcCnt:
            return False
        del self.SrcArray[index]
        if index + 1 >= srcCnt:
            index -= 1
        self.model.SrcIndex = index
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

    def HasKey(self, key):
        return key in self.IniData

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
        self.AutoTests = AutoTestModel()
        self.SrcCnf = SourceInfo(self)
        self.TestName = ''
        self.slots = []
        self.Geometry = Geometry()

    def ReadConfigFile(self):
        self.IniFile.Open()
        ConfigInfo().Read(self, self.IniFile)
        self.Geometry.Read(self, self.IniFile)

    def WriteConfigFile(self):
        self.IniFile.StartWriting()
        ConfigInfo().Write(self.IniFile, self)
        self.Geometry.Write(self.IniFile, self)
        self.IniFile.Save()

    def CurSrc(self):
        if self.SrcIndex >= 0 and len(self.SrcCnf.SrcArray) > self.SrcIndex:
            return self.SrcCnf.SrcArray[self.SrcIndex]
        curSrcData = SrcData()
        return curSrcData

    def GetAllActiveSrcs(self):
        for src in self.SrcCnf.SrcArray:
            if src.IsActive:
                yield src

    def GetAllSrcs(self):
        for src in self.SrcCnf.SrcArray:
            yield src

    def GetSrcAt(self, index):
        return self.SrcCnf.SrcArray[index]

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
        newConfig = Config.FromIndex(index)
        if not newConfig:
            return False
        srcData = self.GetSrcAt(row)
        if self.SrcIndex == row and srcData.Config == newConfig:
            return False
        srcData.Config = newConfig
        return True

    def UpdatePlatform(self, row, index):
        newPlatform = Platform.FromIndex(index)
        if not newPlatform:
            return False
        srcData = self.GetSrcAt(row)
        if self.SrcIndex == row and srcData.Platform == newPlatform:
            return False
        srcData.Platform = newPlatform
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
        return self.CurSrc().Source + '/libs/testing'

    def TestInfoToString(self):
        msg  = 'Current Test Index : ' + str(self.TestIndex) + '\n'
        msg += 'Current Test Name  : ' + self.TestName + '\n'
        msg += 'Current Slots        : ' + str(self.slots) + '\n'
        return msg
