import os

from Common.OsOperations import OsOperations


class MmiSpcTestRunner:
    def __init__(self, model):
        self.model = model

    def RunAllTests(self):
        os.chdir(self.model.Source)
        buildPath = 'mmi/mmi/bin/{}/{}'.format(self.model.Platform, self.model.Config)
        par = 'python libs/testing/testrunner.py'
        par += ' -t mmi/mmi/mmi_stat/integration/tests'
        par += ' -c ' + buildPath
        par += ' -s ' + buildPath
        par += ' -f ' + buildPath
        par += ' -n 1 -r 2'
        par += ' --mmiSetupExe ' + self.model.MMiSetupsPath
        OsOperations.System(par, 'Running Mmi SPC Tests')
        os.chdir(self.model.StartPath)
