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
    def SelectSlots(cls, model):
        fileName = 'C:/Icos/Mmi_Cnf.xml'
        if not os.path.isfile(fileName):
            MessageBox.ShowMessage('File does not exist: ' + fileName)
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
        slots = model.slots
        if len(slots) == 0:
            if showMessage:
                MessageBox.ShowMessage('Please select necessary slot(s).')
            return False
        vmRunExe = os.path.dirname(vmWareExe) + '/vmrun.exe'
        vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'
        par = [vmRunExe, '-vp', pwd, 'list']
        output = OsOperations.ProcessOpen(par)
        runningSlots = []
        searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
        for line in output.split():
            m = re.search(searchPattern, line, re.IGNORECASE)
            if m:
                runningSlots.append(int(m.group(1)))

        for slot in slots:
            vmxPath = vmxGenericPath.format(slot)
            slotName = 'VMware Slot ' + str(slot)
            if slot in runningSlots:
                print slotName + ' : Restarted.'
                subprocess.Popen([vmRunExe, '-vp', pwd, 'reset', vmxPath])
            else:
                if startSlot:
                    subprocess.Popen([vmWareExe, vmxPath])
                    if showMessage:
                        msg = 'Please start ' + slotName
                        MessageBox.ShowMessage(msg)
        return True

    @classmethod
    def TestSlots(cls, model):
        slots = model.slots
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
        dates = dict()
        for mvs in ['MVS6000', 'MVS7000', 'MVS8000', 'MVS8100']:
            mvsPath = 'C:/' + mvs
            if os.path.exists(mvsPath):
                for i in range(1, model.MaxSlots + 1):
                    licenseFileName = '{}/slot{}/license.dat'.format(mvsPath, i)
                    if os.path.exists(licenseFileName):
                        firstLine = FileOperations.ReadLine(licenseFileName)[0]
                        dt = firstLine.split(' ')[-2]
                        dates[dt] = '{} Slot{}'.format(mvs, i)
        if not len(dates) is 1:
            for dt in dates:
                print dates[dt] + ' expires on ' + dt
        else:
            dt = datetime.datetime.strptime(dates.keys()[0], '%Y-%b-%d')
            today = datetime.datetime.now()
            if dt < today:
                MessageBox.ShowMessage('MVS License expired')
            else:
                remainingDays = (dt - today).days
                print 'MVS License will expire in {} days'.format(remainingDays)
