import datetime
import os
import re
import subprocess
from xml.dom import minidom

from Common.FileOperations import FileOperations
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from KLA.TaskMan import TaskMan


class VMWareRunner:
    @classmethod
    def GetAllMvsPaths(cls):
        for mvs in ['MVS6000', 'MVS7000', 'MVS8000', 'MVS8100']:
            mvsPath = 'C:/' + mvs
            if os.path.exists(mvsPath):
                yield mvsPath

    @classmethod
    def GetVmxSlotInfo(cls):
        vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'
        searchPattern = vmxGenericPath.format('(\d*)').replace('.', '\\.')
        return vmxGenericPath, searchPattern

    @classmethod
    def SelectSlots(cls, model):
        fileName = 'C:/Icos/Mmi_Cnf.xml'
        if not os.path.isfile(fileName):
            print 'File does not exist: ' + fileName
            return False
        mydoc = minidom.parse(fileName)
        devices = mydoc.getElementsByTagName('Device')
        slots = []
        for device in devices:
            deviceName = device.firstChild.data
            slots.append(int(deviceName.split('_')[0][3:]))
        model.SelectSlots(slots)
        return True

    @classmethod
    def RunSlots(cls, model, startSlot = True, showMessage = True):
        vmWareExe = model.VMwareExe
        pwd = model.VMwarePwd
        slots = model.AutoTests.slots
        if len(slots) == 0:
            if showMessage:
                MessageBox.ShowMessage('Please select necessary slot(s).')
            return False
        vmRunExe = os.path.dirname(vmWareExe) + '/vmrun.exe'
        (vmxGenericPath, searchPattern) = cls.GetVmxSlotInfo()
        par = [vmRunExe, '-vp', pwd, 'list']
        output = OsOperations.ProcessOpen(par)
        runningSlots = []
        for line in output.split():
            m = re.search(searchPattern, line, re.IGNORECASE)
            if m:
                runningSlots.append(int(m.group(1)))

        errMsg = ''
        for slot in slots:
            vmxPath = vmxGenericPath.format(slot)
            slotName = 'VMware Slot ' + str(slot)
            if slot in runningSlots:
                print slotName + ' : Restarted.'
                par = [vmRunExe, '-vp', pwd, 'reset', vmxPath]
                output = OsOperations.Popen(par, None, True)
                for line in output.split('\n'):
                    if line.startswith('Error:'):
                        errMsg += line[7:] + '\n'
            else:
                if startSlot:
                    subprocess.Popen([vmWareExe, vmxPath])
                    if showMessage:
                        msg = 'Please start ' + slotName
                        MessageBox.ShowMessage(msg)
        if len(errMsg) > 0:
            MessageBox.ShowMessage(errMsg)
        return True

    @classmethod
    def TestSlots(cls, model):
        slots = model.AutoTests.slots
        if len(slots) == 0:
            MessageBox.ShowMessage('Please select necessary slot(s).')
            return

        if TaskMan.StopTask('MvxCmd.exe'):
            OsOperations.Timeout(5)
        cd1 = os.getcwd()
        OsOperations.ChDir('C:/MVS7000/slot1/')
        # Bug : only first slot is working.
        for slot in slots:
            os.chdir('../slot{}'.format(slot))
            cmd = 'slot{}.bat'.format(slot)
            OsOperations.System(cmd)
        OsOperations.ChDir(cd1)

    @classmethod
    def CheckLicense(cls, model):
        errMsg = None
        dates = dict()
        for mvsPath in cls.GetAllMvsPaths():
            for i in range(1, model.MaxSlots + 1):
                licenseFileName = '{}/slot{}/license.dat'.format(mvsPath, i)
                if os.path.exists(licenseFileName):
                    firstLine = FileOperations.ReadLine(licenseFileName)[0]
                    dt = firstLine.split(' ')[-2]
                    dates[dt] = '{} Slot{}'.format(mvsPath, i)
        if not len(dates) is 1:
            errMsg = [dates[dt] + ' expires on ' + dt for dt in dates]
            errMsg = '\n'.join(errMsg)
        else:
            dt = datetime.datetime.strptime(dates.keys()[0], '%Y-%b-%d')
            today = datetime.datetime.now()
            if dt < today:
                errMsg = 'MVS License expired'
            else:
                remainingDays = (dt - today).days
                msg = 'MVS License will expire in {} days'.format(remainingDays)
                if remainingDays < 7:
                    errMsg = msg
                else:
                    print msg
        if errMsg:
            MessageBox.ShowMessage(errMsg)
