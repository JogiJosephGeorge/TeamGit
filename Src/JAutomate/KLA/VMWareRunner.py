import os
import re
import subprocess
from xml.dom import minidom

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
        slots = model.slots
        if len(slots) == 0:
            if showMessage:
                MessageBox.ShowMessage('Please select necessary slot(s).')
            return False
        vmRunExe = os.path.dirname(vmWareExe) + '/vmrun.exe'
        vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'
        par = [vmRunExe, '-vp', '1', 'list']
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
                subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
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
