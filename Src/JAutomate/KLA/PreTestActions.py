import os

from Common.FileOperations import FileOperations
from KLA.LicenseConfigWriter import LicenseConfigWriter
from KLA.TaskMan import TaskMan


class PreTestActions:
    @classmethod
    def CopyMockLicense(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
        licenseFile = os.path.abspath(licencePath.format(*args))
        mmiPath = PreTestActions.GetMmiPath(model, toSrc)
        FileOperations.Copy(licenseFile, mmiPath)

    @classmethod
    def GetMmiPath(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        if toSrc:
            mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(*args))
        else:
            mmiPath = 'C:/icos'
        return mmiPath

    @classmethod
    def CopyxPortIllumRef(cls, model, delay = False):
        src = model.StartPath + '/DataFiles/xPort_IllumReference.xml'
        des = 'C:/icos/xPort/'
        if delay:
            TaskMan.AddTimer('xport', FileOperations.Copy(src, des, 8, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def GetTestPath(cls, model):
        return os.path.abspath(model.Source + '/handler/tests/' + model.TestName)

    @classmethod
    def GenerateLicMgrConfig(cls, model):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        LicenseConfigWriter(model.Source, src)
        print 'LicMgrConfig.xml has been created from source and placed on ' + src

    @classmethod
    def CopyLicMgrConfig(cls, model, delay = False):
        src = model.StartPath + '/DataFiles/LicMgrConfig.xml'
        #des = cls.GetTestPath(model) + '~/'
        des = 'C:/Icos'
        if delay:
            TaskMan.AddTimer('LicMgr', FileOperations.Copy(src, des, 9, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def CopyMmiSaveLogExe(cls, model):
        destin = os.path.abspath("{}/handler/tests/{}~/Icos".format(
            model.Source, model.TestName))
        src = os.path.abspath('{}/mmi/mmi/Bin/{}/{}/MmiSaveLogs.exe'.format(
            model.Source, model.Platform, model.Config))
        FileOperations.Copy(src, destin)

    @classmethod
    def ModifyVisionSystem(cls, model):
        line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
        oldLine = ' ' + line
        newLine = ' #' + line
        fileName = os.path.abspath(model.Source + '/libs/testing/visionsystem.py')
        with open(fileName) as f:
            oldText = f.read()
        if oldLine in oldText:
            newText = oldText.replace(oldLine, newLine)
            with open(fileName, "w") as f:
                f.write(newText)
            print fileName + ' has been modified.'
        else:
            print fileName + ' had already been modified.'
