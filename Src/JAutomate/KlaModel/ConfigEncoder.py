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
        configSet = (debugConfigSet, releaseConfigSet)[model.Config == cls.Configs[1]]
        # releasex64 is not working
        # return configSet[model.Platform == cls.Platforms[0]]
        return configSet[1]

    @classmethod
    def AddSrc(cls, model, newSrcPath):
        for srcSet in model.Sources:
            if newSrcPath == srcSet[0]:
                return
        model.Sources.append((newSrcPath, cls.Configs[0], cls.Platforms[0]))
        model.Source = newSrcPath
        if model.SrcIndex < 0:
            model.SrcIndex = 0