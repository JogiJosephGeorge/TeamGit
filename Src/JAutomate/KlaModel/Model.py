import json
import os
from collections import OrderedDict

from KlaModel.AutoTestModel import AutoTestModel
from KlaModel.ConfigEncoder import Config, Platform
from KlaModel.ConfigInfo import ConfigInfo, Geometry
from KlaModel.SourceInfo import SourceInfo
from KlaModel.VsVersions import VsVersions


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
        self.Src = SourceInfo(self)
        self.Geometry = Geometry()
        self.UserAccess = UserAccess()
        self.VsVersions = VsVersions()
        self.VsSolutions = []

    def ReadFromFile(self):
        self.IniFile.Open()
        self.Branch = ''
        self.Src.Read(self.IniFile)
        self.AutoTests.Read(self.IniFile)
        self.VsVersions.Read(self.IniFile)
        self.UserAccess.Read(self.IniFile)
        ConfigInfo().Read(self, self.IniFile)
        self.Geometry.Read(self, self.IniFile)
        self.VsSolutions = self.IniFile.ReadField('VsSolutions', [])

    def WriteToFile(self):
        self.IniFile.StartWriting()
        self.Src.Write(self.IniFile)
        self.AutoTests.Write(self.IniFile)
        self.VsVersions.Write(self.IniFile)
        self.UserAccess.Write(self.IniFile)
        ConfigInfo().Write(self.IniFile, self)
        self.Geometry.Write(self.IniFile, self)
        self.IniFile.Write('VsSolutions', self.VsSolutions)
        self.IniFile.Save()

    def UpdateConfig(self, row, index):
        newConfig = Config.FromIndex(index)
        if not newConfig:
            return False
        srcData = self.Src.GetSrcAt(row)
        if self.Src.SrcIndex == row and srcData.Config == newConfig:
            return False
        srcData.Config = newConfig
        return True

    def UpdatePlatform(self, row, index):
        newPlatform = Platform.FromIndex(index)
        if not newPlatform:
            return False
        srcData = self.Src.GetSrcAt(row)
        if self.Src.SrcIndex == row and srcData.Platform == newPlatform:
            return False
        srcData.Platform = newPlatform
        return True
