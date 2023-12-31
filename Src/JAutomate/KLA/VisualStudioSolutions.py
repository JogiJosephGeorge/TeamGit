import subprocess

from Common.MessageBox import MessageBox
from KlaModel.ConfigEncoder import Config, Platform


class VisualStudioSolutions:
    def __init__(self, model):
        self.model = model
        self.Solutions = [
            '/handler/cpp/CIT100.sln',
            '/mmi/mmi/Mmi.sln',

            '/handler/Simulator/CIT100Simulator/CIT100Simulator.sln',
            '/mmi/mmi/MockLicense.sln',
            '/mmi/mmi/Converters.sln',
        ]

    def Init(self):
        self.SelectedInxs = [True] * len(self.Solutions) + [False] * len(self.model.VsSolutions)

    def GetAllSlnFiles(self):
        #slnFiles = []
        #curSrc = self.model.Src.GetCur()
        #srcLen = len(curSrc.Source) + 1
        #for root, dirs, files in os.walk(curSrc.Source):
        #    path = root[srcLen:]
        #    fis = [[path, fi] for fi in files if fi.endswith('.sln')]
        #    slnFiles += fis
        #return slnFiles
        return self.Solutions + self.model.VsSolutions

    def OpenSolutionIndex(self, index):
        self.OpenSolutionFile(self.GetSlnPath(index))

    def OpenSolutionFile(self, slnFileName):
        if self.model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = self.model.Src.GetCur()
        fileName = curSrc.Source + slnFileName
        devEnvExe = self.model.VsVersions.GetDevEnvExe(curSrc.VsVersion)
        param = [
            devEnvExe,
            fileName
        ]
        subprocess.Popen(param)
        print 'Open solution : ' + fileName
        if curSrc.Config is not Config.Debug or curSrc.Platform is not Platform.Win32:
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
        return self.model.VsSolutions[index]

    def GetSlnName(self, slnFile):
        slnName = slnFile.split('/')[-1][:-4]
        if slnName == 'CIT100Simulator':
            return 'Simulator'
        return slnName

    @classmethod
    def GetPlatform(cls, slnFile, platform):
        isSimulator = slnFile.split('/')[-1] == 'CIT100Simulator.sln'
        return VisualStudioSolutions.GetPlatformStr(platform, isSimulator)

    @classmethod
    def GetPlatformStr(cls, platform, isSimulator = False):
        if isSimulator and Platform.Win32 == platform:
            platform = Platform.x86
        return platform
