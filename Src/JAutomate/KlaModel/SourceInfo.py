import os

from Common.Git import Git
from Common.MessageBox import MessageBox
from KlaModel.ConfigEncoder import Config, Platform
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
            self.model.WriteToFile()
        return True

    def AddSource(self, newPath):
        if not newPath:
            return False
        if not os.path.isdir(newPath):
            MessageBox.ShowMessage('The path is not valid.')
            return False
        for srcData in self.SrcArray:
            if newPath == srcData.Source:
                MessageBox.ShowMessage('The source is added already.')
                return False
        branch = Git.GetBranch(newPath)
        if not branch:
            MessageBox.ShowMessage('The selected path is not a valid git directory.')
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

    def GetCur(self):
        if self.SrcIndex >= 0 and len(self.SrcArray) > self.SrcIndex:
            return self.SrcArray[self.SrcIndex]
        curSrcData = SrcData()
        return curSrcData

    def GetAllActiveSrcs(self):
        for src in self.SrcArray:
            if src.IsActive:
                yield src

    def GetAllSrcs(self):
        for src in self.SrcArray:
            yield src

    def GetSrcAt(self, index):
        if index < len(self.SrcArray):
            return self.SrcArray[index]
        return None

    def IsEmpty(self):
        return self.SrcIndex < 0
