from collections import OrderedDict
import json
import os

from KlaModel.AutoTestModel import AutoTestModel
from KlaModel.ConfigEncoder import Config, Platform
from KlaModel.ConfigInfo import ConfigInfo, Geometry
from KlaModel.VsVersions import VsVersions


class SrcData:
    def __init__(self):
        self.Source = ''
        self.Config = Config.Debug
        self.Platform = Platform.Win32
        self.IsActive = False
        self.Description = ''
        self.MMiSetupVersion = ''
        self.VsVersion = ''

    @classmethod
    def CreateFromJson(cls, jsonData):
        srcData = SrcData()
        srcData.Source = cls.ReadField(jsonData, 'Source', '')
        srcData.Config = cls.ReadField(jsonData, 'Config', Config.Debug)
        srcData.Platform = cls.ReadField(jsonData, 'Platform', Platform.Win32)
        srcData.IsActive = cls.ReadField(jsonData, 'IsActive', False)
        srcData.Description = cls.ReadField(jsonData, 'Description', '')
        srcData.MMiSetupVersion = cls.ReadField(jsonData, 'MMiSetupVersion', '')
        srcData.VsVersion = cls.ReadField(jsonData, 'VsVersion', VsVersions().GetAll()[0])
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
        jsonData['MMiSetupVersion'] = self.MMiSetupVersion
        jsonData['VsVersion'] = self.VsVersion
        return jsonData


class SourceInfo:
    def __init__(self, model):
        self.model = model
        self.SrcArray = []
        self.SrcIndex = -1

    def Read(self, iniFile):
        self.SrcIndex = -1
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
        srcIndex = iniFile.ReadField('SrcIndex', -1)
        self.UpdateSource(srcIndex, False)
        self.ReadMMiSetupVersion(iniFile) # For old version

    def Write(self, iniFile):
        iniFile.Write('SrcIndex', self.SrcIndex)

        sourceInfo = []
        for src in self.SrcArray:
            srcItem = src.GetJsonData()
            sourceInfo.append(srcItem)
        iniFile.Write('SourceInfo', sourceInfo)

    def UpdateSource(self, index, writeToFile):
        if index < 0 or index >= len(self.SrcArray):
            return False
        if self.SrcIndex == index:
            return False
        self.SrcIndex = index
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
        if self.SrcIndex < 0:
            self.SrcIndex = 0
        return True

    def RemoveSource(self, index):
        srcCnt = len(self.SrcArray)
        if index < 0 or index >= srcCnt:
            return False
        del self.SrcArray[index]
        if index + 1 >= srcCnt:
            index -= 1
        self.SrcIndex = index
        return True

    def ReadMMiSetupVersion(self, iniFile):
        if iniFile.HasKey('MMiSetupVersion'):
            MMiSetupVersion = iniFile.ReadField('MMiSetupVersion', '')
            if MMiSetupVersion:
                for srcData in self.SrcArray:
                    srcData.MMiSetupVersion = MMiSetupVersion


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
                print('There are issues in reading ' + self.FileName)

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


class UserAccess:
    def SetIsExpertUser(self, isExpUser):
        self.UILevel = 2 if isExpUser else 3

    def IsDeveloper(self):
        return self.UILevel < 2

    def IsExpertUser(self):
        return self.UILevel < 3

    def Read(self, iniFile):
        self.UILevel = iniFile.ReadField('UILevel', 3)

    def Write(self, iniFile):
        iniFile.Write('UILevel', self.UILevel)

class Model:
    def __init__(self):
        self.StartPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filePath = self.StartPath + '\\KlaRunner.ini'
        self.IniFile = IniFile(filePath)
        self.AutoTests = AutoTestModel()
        self.SrcCnf = SourceInfo(self)
        self.Geometry = Geometry()
        self.UserAccess = UserAccess()
        self.VsVersions = VsVersions()

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
        if self.SrcCnf.SrcIndex >= 0 and len(self.SrcCnf.SrcArray) > self.SrcCnf.SrcIndex:
            return self.SrcCnf.SrcArray[self.SrcCnf.SrcIndex]
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
            self.AutoTests.TestIndex = 0 if len(self.AutoTests.Tests) > 0 else -1
            return False
        if self.AutoTests.TestIndex == index:
            return False
        self.AutoTests.TestIndex = index
        [self.AutoTests.TestName, self.AutoTests.slots] = self.AutoTests.Tests[self.AutoTests.TestIndex]
        if writeToFile:
            self.WriteConfigFile()
        return True

    def UpdateConfig(self, row, index):
        newConfig = Config.FromIndex(index)
        if not newConfig:
            return False
        srcData = self.GetSrcAt(row)
        if self.SrcCnf.SrcIndex == row and srcData.Config == newConfig:
            return False
        srcData.Config = newConfig
        return True

    def UpdatePlatform(self, row, index):
        newPlatform = Platform.FromIndex(index)
        if not newPlatform:
            return False
        srcData = self.GetSrcAt(row)
        if self.SrcCnf.SrcIndex == row and srcData.Platform == newPlatform:
            return False
        srcData.Platform = newPlatform
        return True

    def UpdateSlot(self, index, isSelected):
        slotNum = index + 1
        if isSelected:
            self.AutoTests.slots.append(slotNum)
            self.AutoTests.slots.sort()
        else:
            self.AutoTests.slots.remove(slotNum)
        self.AutoTests.SetNameSlots(self.AutoTests.TestName, self.AutoTests.slots)

    def SelectSlots(self, slots):
        self.AutoTests.slots = slots
        self.AutoTests.slots.sort()
        self.AutoTests.SetNameSlots(self.AutoTests.TestName, self.AutoTests.slots)
