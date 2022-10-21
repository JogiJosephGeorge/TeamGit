class VsVersions:
    def __init__(self):
        self.DevEnvCom = ''
        self.DevEnvExe = ''
        self.DevEnvCom22 = ''
        self.DevEnvExe22 = ''

    def GetAll(self):
        return ['2017', '2022']

    def GetIndex(self, version):
        verInx = 0;
        vsVersions = self.GetAll()
        if version in vsVersions:
            verInx = vsVersions.index(version)
        return verInx

    def GetDevEnvCom(self, model, version):
        return self.DevEnvCom22 if version == '2022' else self.DevEnvCom

    def GetDevEnvExe(self, model, version):
        return self.DevEnvExe22 if version == '2022' else self.DevEnvExe

    def Read(self, iniFile):
        self.DevEnvCom = iniFile.ReadField('DevEnvCom', 'C:/Program Files (x86)/Microsoft Visual Studio 12.0/Common7/IDE/devenv.com')
        self.DevEnvExe = iniFile.ReadField('DevEnvExe', 'C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional/Common7/IDE/devenv.exe')
        self.DevEnvCom22 = iniFile.ReadField('DevEnvCom22', 'C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/devenv.com')
        self.DevEnvExe22 = iniFile.ReadField('DevEnvExe22', 'C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/devenv.exe')

    def Write(self, iniFile):
        iniFile.Write('DevEnvCom', self.DevEnvCom)
        iniFile.Write('DevEnvExe', self.DevEnvExe)
        iniFile.Write('DevEnvCom22', self.DevEnvCom22)
        iniFile.Write('DevEnvExe22', self.DevEnvExe22)
