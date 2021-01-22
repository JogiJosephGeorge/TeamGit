import subprocess

class VisualStudioSolutions:
    def __init__(self, model):
        self.model = model
        self.Solutions = [
            '/handler/cpp/CIT100.sln',
            '/mmi/mmi/Mmi.sln'
        ]
        self.OtherSolutions = [
            '/handler/Simulator/CIT100Simulator/CIT100Simulator.sln',
            '/mmi/mmi/MockLicense.sln',
            '/mmi/mmi/Converters.sln',
            '/libs/DLStub/DLStub/DLStub.sln',
        ]

    def GetAllSlnFiles(self):
        #slnFiles = []
        #srcLen = len(self.model.Source) + 1
        #for root, dirs, files in os.walk(self.model.Source):
        #    path = root[srcLen:]
        #    fis = [[path, fi] for fi in files if fi.endswith('.sln')]
        #    slnFiles += fis
        #return slnFiles
        return self.Solutions + self.OtherSolutions

    def OpenSolutionIndex(self, index):
        self.OpenSolutionFile(self.GetSlnPath(index))

    def OpenSolutionFile(self, slnFileName):
        fileName = self.model.Source + slnFileName
        param = [
            self.model.DevEnvExe,
            fileName
        ]
        subprocess.Popen(param)
        print 'Open solution : ' + fileName
        if self.model.Config is not 'Debug' or self.model.Platform is not 'Win32':
            msg = 'Please check configuration and platform in Visual Studio'
            #MessageBox.ShowMessage(msg, 'Visual Studio')
            print msg

    def GetSelectedSolutions(self):
        retVal = []
        allSlns = self.GetAllSlnFiles()
        for inx,sln in enumerate(allSlns):
            if self.SelectedInxs[inx]:
                slnName = self.GetSlnName(sln)
                retVal.append((sln, slnName))
        return retVal

    def GetSlnPath(self, index):
        if index < len(self.Solutions):
            return self.Solutions[index]
        index -= len(self.Solutions)
        return self.OtherSolutions[index]

    def GetSlnName(self, slnFile):
        slnName = slnFile.split('/')[-1][:-4]
        if slnName == 'CIT100Simulator':
            return 'Simulator'
        return slnName

    def GetHandlerPath(self):
        platform = VisualStudioSolutions.GetPlatformStr(self.model.Platform)
        handlerPath = '{}/handler/cpp/bin/{}/{}/system'.format(self.model.Source, platform, self.model.Config)
        return (handlerPath, handlerPath + '/console.exe')

    def GetSimulatorPath(self):
        platform = VisualStudioSolutions.GetPlatformStr(self.model.Platform, True)
        simulatorExe = '{}/handler/Simulator/ApplicationFiles/bin/{}/{}/CIT100Simulator.exe'
        return simulatorExe.format(self.model.Source, platform, self.model.Config)

    @classmethod
    def GetPlatform(cls, slnFile, platform):
        isSimulator = slnFile.split('/')[-1] == 'CIT100Simulator.sln'
        return VisualStudioSolutions.GetPlatformStr(platform, isSimulator)

    @classmethod
    def GetPlatformStr(cls, platform, isSimulator = False):
        if isSimulator and 'Win32' == platform:
            platform = 'x86'
        return platform
