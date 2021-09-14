
class Config:
    Debug = 'Debug'
    Release = 'Release'

    @classmethod
    def GetList(cls):
        return [
            Config.Debug,
            Config.Release,
        ]

    @classmethod
    def FromIndex(cls, index):
        if index < 0 or index > 1:
            return ''
        return cls.GetList()[index]


class Platform:
    Win32 = 'Win32'
    x64 = 'x64'

    @classmethod
    def GetList(cls):
        return [
            Platform.Win32,
            Platform.x64,
            ]

    @classmethod
    def FromIndex(cls, index):
        if index < 0 or index > 1:
            return ''
        return cls.GetList()[index]


class ConfigEncoder:
    @classmethod
    def GetBuildConfig(cls, model):
        debugConfigSet = ('debugx64', 'debug')
        releaseConfigSet = ('releasex64', 'release')
        curSrc = model.CurSrc()
        configSet = (debugConfigSet, releaseConfigSet)[curSrc.Config == Config.Release]
        # releasex64 is not working
        # return configSet[curSrc.Platform == Platforms.Win32]
        return configSet[1]
