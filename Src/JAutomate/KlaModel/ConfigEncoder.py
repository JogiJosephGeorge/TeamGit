class ConfigEncoder:
    Configs = ['Debug', 'Release']
    Platforms = ['Win32', 'x64']

    @classmethod
    def DecodeSource(cls, srcStr):
        source = srcStr[4:]
        config = cls.Configs[srcStr[0] == 'R']
        platform = cls.Platforms[srcStr[1:3] == '64']
        return (source, config, platform)

    @classmethod
    def EncodeSource(cls, srcSet):
        return srcSet[1][0] + srcSet[2][-2:] + ' ' + srcSet[0]

    @classmethod
    def GetBuildConfig(cls, model):
        debugConfigSet = ('debugx64', 'debug')
        releaseConfigSet = ('releasex64', 'release')
        curSrc = model.CurSrc()
        configSet = (debugConfigSet, releaseConfigSet)[curSrc.Config == cls.Configs[1]]
        # releasex64 is not working
        # return configSet[curSrc.Platform == cls.Platforms[0]]
        return configSet[1]

    @classmethod
    def IsValidSource(cls, model, newSrcDir):
        if len(newSrcDir) == 0:
            return False
        for srcData in model.GetAllSrcs():
            if srcData.Source == newSrcDir:
                return False
        return True
