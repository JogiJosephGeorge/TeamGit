from Common.Git import Git
from KlaModel.VsVersions import VsVersions


class ConfigInfo:
    def Read(self, model, iniFile):
        model.GitPath = iniFile.ReadField('GitPath', 'C:/Program Files/Git')
        model.VMwareExe = iniFile.ReadField('VMwareExe', 'C:/Program Files (x86)/VMware/VMware Workstation/vmware.exe')
        model.VMwarePwd = iniFile.ReadField('VMwarePwd', '1')
        model.EffortLogFile = iniFile.ReadField('EffortLogFile', 'D:/QuEST/Tools/EffortCapture_2013/timeline.log')
        model.BCompare = iniFile.ReadField('BCompare', 'C:/Program Files (x86)/Beyond Compare 4/BCompare.exe')
        model.MMiConfigPath = iniFile.ReadField('MMiConfigPath', 'D:\\')
        model.MMiSetupsPath = iniFile.ReadField('MMiSetupsPath', 'D:/MmiSetups')
        model.removeOldCopies = iniFile.ReadField('removeOldCopies', True)
        model.StartOnly = iniFile.ReadField('StartOnly', False)
        model.DebugVision = iniFile.ReadField('DebugVision', False)
        model.CopyMmi = iniFile.ReadField('CopyMmi', True)
        model.TempDir = iniFile.ReadField('TempDir', 'bin')
        model.LogFileName = iniFile.ReadField('LogFileName', 'bin/Log.txt')
        model.MaxSlots = iniFile.ReadInt('MaxSlots', 8)
        model.LogName = iniFile.ReadField('LogName', 'KLARunner> ')
        model.HostCamTakiRFileName = iniFile.ReadField('HostCamTakiRFileName', 'C:/HostCamTakiR')
        model.RestartSlotsForMMiAlone = iniFile.ReadField('RestartSlotsForMMiAlone', False)
        model.GenerateLicMgrConfigOnTest = iniFile.ReadField('GenerateLicMgrConfigOnTest', False)
        model.CopyLicMgrConfigOnTest = iniFile.ReadField('CopyLicMgrConfigOnTest', False)
        model.CopyMockLicenseOnTest = iniFile.ReadField('CopyMockLicenseOnTest', False)
        model.CopyExportIllumRefOnTest = iniFile.ReadField('CopyExportIllumRefOnTest', False)
        model.CopyMVSDConversionOnTest = iniFile.ReadField('CopyMVSDConversionOnTest', False)
        model.ConsoleFromCHandler = iniFile.ReadField('ConsoleFromCHandler', False)
        model.RestartAfterSrcChange = iniFile.ReadField('RestartAfterSrcChange', True)
        model.RemoveStartedTXT = iniFile.ReadField('RemoveStartedTXT', False)
        model.CleanDotVsOnReset = iniFile.ReadField('CleanDotVsOnReset', False)
        model.UpdateSubmodulesOnReset = iniFile.ReadField('UpdateSubmodulesOnReset', False)
        model.NoAutoTest = iniFile.ReadField('NoAutoTest', False)
        model.RunHostCam = iniFile.ReadField('RunHostCam', False)
        model.RunHostCamTakiR = iniFile.ReadField('RunHostCamTakiR', False)
        model.ShowBuildInProgress = iniFile.ReadField('ShowBuildInProgress', True)
        model.PromptOnTestFail = iniFile.ReadField('PromptOnTestFail', True)

        model.MMiConfigPath = model.MMiConfigPath.replace('/', '\\')

        Git.GitPath = self.GetShortPath(model.GitPath + '/cmd/git')
        Git.GitBin = self.GetShortPath(model.GitPath + '/bin')

    def GetShortPath(self, path):
        path = path.replace('Program Files (x86)', 'PROGRA~2')
        return path.replace('Program Files', 'PROGRA~1')

    def Write(self, iniFile, model):
        iniFile.Write('GitPath', model.GitPath)
        iniFile.Write('VMwareExe', model.VMwareExe)
        iniFile.Write('VMwarePwd', model.VMwarePwd)
        iniFile.Write('EffortLogFile', model.EffortLogFile)
        iniFile.Write('BCompare', model.BCompare)
        iniFile.Write('MMiConfigPath', model.MMiConfigPath)
        iniFile.Write('MMiSetupsPath', model.MMiSetupsPath)
        iniFile.Write('removeOldCopies', model.removeOldCopies)
        iniFile.Write('StartOnly', model.StartOnly)
        iniFile.Write('DebugVision', model.DebugVision)
        iniFile.Write('CopyMmi', model.CopyMmi)
        iniFile.Write('TempDir', model.TempDir)
        iniFile.Write('LogFileName', model.LogFileName)
        iniFile.Write('MaxSlots', model.MaxSlots)
        iniFile.Write('LogName', model.LogName)
        iniFile.Write('HostCamTakiRFileName', model.HostCamTakiRFileName)
        iniFile.Write('RestartSlotsForMMiAlone', model.RestartSlotsForMMiAlone)
        iniFile.Write('GenerateLicMgrConfigOnTest', model.GenerateLicMgrConfigOnTest)
        iniFile.Write('CopyLicMgrConfigOnTest', model.CopyLicMgrConfigOnTest)
        iniFile.Write('CopyMockLicenseOnTest', model.CopyMockLicenseOnTest)
        iniFile.Write('CopyExportIllumRefOnTest', model.CopyExportIllumRefOnTest)
        iniFile.Write('CopyMVSDConversionOnTest', model.CopyMVSDConversionOnTest)
        iniFile.Write('ConsoleFromCHandler', model.ConsoleFromCHandler)
        iniFile.Write('RestartAfterSrcChange', model.RestartAfterSrcChange)
        iniFile.Write('RemoveStartedTXT', model.RemoveStartedTXT)
        iniFile.Write('CleanDotVsOnReset', model.CleanDotVsOnReset)
        iniFile.Write('UpdateSubmodulesOnReset', model.UpdateSubmodulesOnReset)
        iniFile.Write('NoAutoTest', model.NoAutoTest)
        iniFile.Write('RunHostCam', model.RunHostCam)
        iniFile.Write('RunHostCamTakiR', model.RunHostCamTakiR)
        iniFile.Write('ShowBuildInProgress', model.ShowBuildInProgress)
        iniFile.Write('PromptOnTestFail', model.PromptOnTestFail)


class Geometry:
    def Read(self, model, iniFile):
        self.RawData = iniFile.ReadField('Geometry', {})

    def GetGeom(self, name):
        if name in self.RawData:
            return self.RawData[name]
        geomData = {'X' : 0, 'Y' : 0}
        self.RawData[name] = geomData
        return geomData

    def GetPos(self, name):
        WindowGeom = self.GetGeom(name)
        x = WindowGeom['X'] if 'X' in WindowGeom else 0
        y = WindowGeom['Y'] if 'Y' in WindowGeom else 0
        return (x, y)

    def SetPos(self, name, x, y):
        WindowGeom = self.GetGeom(name)
        WindowGeom['X'] = x
        WindowGeom['Y'] = y

    def ReadGeomInfo(self, window, name):
        posX, posY = self.GetPos(name)
        window.geometry('+{}+{}'.format(posX, posY))

    def WriteGeomInfo(self, window, name):
        posX = window.winfo_x()
        posY = window.winfo_y()
        self.SetPos(name, posX, posY)

    def Write(self, iniFile, model):
        iniFile.Write('Geometry', self.RawData)
