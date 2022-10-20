class VsVersions:
    def GetAll(self):
        return ['2017', '2022']

    def GetIndex(self, version):
        verInx = 0;
        vsVersions = self.GetAll()
        if version in vsVersions:
            verInx = vsVersions.index(version)
        return verInx

    def GetDevEnvCom(self, model, version):
        return model.DevEnvCom22 if version == '2022' else model.DevEnvCom

    def GetDevEnvExe(self, model, version):
        return model.DevEnvExe22 if version == '2022' else model.DevEnvExe
