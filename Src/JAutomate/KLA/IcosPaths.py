from KLA.VisualStudioSolutions import VisualStudioSolutions


class IcosPaths:
    @classmethod
    def GetMmiPath(cls, source, platform, config):
        return '{}/mmi/mmi/Bin/{}/{}'.format(source, platform, config)

    @classmethod
    def GetMmiExePath(cls, source, platform, config):
        return cls.GetMmiPath(source, platform, config) + '/mmi.exe'

    @classmethod
    def GetHandlerPath(cls, source, platform, config, runFromCHandler):
        if runFromCHandler:
            return 'C:/handler/system'
        return '{}/handler/cpp/bin/{}/{}/system'.format(source, platform, config)

    @classmethod
    def GetConsolePath(cls, source, platform, config, runFromCHandler):
        return cls.GetHandlerPath(source, platform, config, runFromCHandler) + '/console.exe'

    @classmethod
    def GetSimulatorPath(cls, source, platform, config, runFromCHandler):
        if runFromCHandler:
            return 'C:/Handler/simulator/CIT100Simulator.exe'
        platform = VisualStudioSolutions.GetPlatformStr(platform, True)
        return '{}/handler/Simulator/ApplicationFiles/bin/{}/{}/CIT100Simulator.exe'.format(source, platform, config)

    @classmethod
    def GetMmiSaveLogsPath(cls, source, platform, config):
        return '{}/mmi/mmi/Bin/{}/{}/MmiSaveLogs.exe'.format(source, platform, config)

    @classmethod
    def GetMockLicensePath(cls, source, platform, config):
        return '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'.format(source, platform, config)

    @classmethod
    def GetMVSDConversionsPath(cls, source, platform):
        return '{}/mmi/mmi/MVSDConversions/{}'.format(source, platform)

    @classmethod
    def GetCommonTestPath(cls, source):
        return source + '/handler/tests'

    @classmethod
    def GetTestPath(cls, source, testName):
        return cls.GetCommonTestPath(source) + '/' + testName

    @classmethod
    def GetAutoplyPath(cls):
        return '\\\\10.230.8.202/autommi/Configurations/'

    @classmethod
    def GetTestPathTemp(cls, source, testName):
        return cls.GetTestPath(source, testName) + '~'
