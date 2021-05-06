import json
import os
from collections import OrderedDict

from Common.Git import Git
from KlaModel.ConfigEncoder import ConfigEncoder


class ConfigInfo:
    def __init__(self, fileName):
        self.FileName = fileName

    def ReadIni(self):
        _model = {}
        if os.path.exists(self.FileName):
            try:
                with open(self.FileName) as f:
                    _model = json.load(f)
            except:
                print 'There are issues in reading ' + self.FileName
        return _model

    def Read(self, model):
        _model = self.ReadIni()
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
        model.GitPath = self.ReadField(_model, 'GitPath', 'C:/Program Files/Git')
        model.VMwareExe = self.ReadField(_model, 'VMwareExe', 'C:/Program Files (x86)/VMware/VMware Workstation/vmware.exe')
        model.VMwarePwd = self.ReadField(_model, 'VMwarePwd', '1')
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
        model.RemoveStartedTXT = self.ReadField(_model, 'RemoveStartedTXT', False)
        model.CleanDotVsOnReset = self.ReadField(_model, 'CleanDotVsOnReset', False)
        model.UpdateSubmodulesOnReset = self.ReadField(_model, 'UpdateSubmodulesOnReset', False)
        model.RunHostCam = self.ReadField(_model, 'RunHostCam', False)

        model.MMiConfigPath = model.MMiConfigPath.replace('/', '\\')

        Git.GitPath = self.GetShortPath(model.GitPath + '/cmd/git')
        Git.GitBin = self.GetShortPath(model.GitPath + '/bin')

    def GetShortPath(self, path):
        path = path.replace('Program Files (x86)', 'PROGRA~2')
        return path.replace('Program Files', 'PROGRA~1')

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
        _model['GitPath'] = model.GitPath
        _model['VMwareExe'] = model.VMwareExe
        _model['VMwarePwd'] = model.VMwarePwd
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
        _model['RemoveStartedTXT'] = model.RemoveStartedTXT
        _model['CleanDotVsOnReset'] = model.CleanDotVsOnReset
        _model['UpdateSubmodulesOnReset'] = model.UpdateSubmodulesOnReset
        _model['RunHostCam'] = model.RunHostCam

        with open(self.FileName, 'w') as f:
            json.dump(_model, f, indent=3)
