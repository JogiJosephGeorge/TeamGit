import os

from Common.OsOperations import OsOperations


class TaskMan:
    namedTimers = {}

    @classmethod
    def StopTasks(cls):
        cls.StopTimers()
        for exeName in [
            'Mmi.exe',
            'Mmi_spc.exe',
            'console.exe',
            'CIT100Simulator.exe',
            'HostCamServer.exe',
            'Ves.exe',
        ]:
            TaskMan.StopTask(exeName)
        TaskMan.StopTask('python.exe', os.getpid())

    @classmethod
    def StopTask(cls, exeName, exceptProcId = -1):
        processIds = OsOperations.GetProcessIds(exeName)
        if exceptProcId > 0:
            processIds.remove(exceptProcId)
        if len(processIds) == 0:
            return False
        '''
        wmic process where name="mmi.exe" call terminate
        wmic process where "name='mmi.exe'" delete
        taskkill /IM "mmi.exe" /T /F
        '''
        print '{} Process IDs : {}'.format(exeName, processIds)
        if exceptProcId < 0:
            OsOperations.Popen([ 'TASKKILL', '/IM', exeName, '/T', '/F' ])
        else:
            for proId in processIds:
                OsOperations.Popen([ 'TASKKILL', '/PID', str(proId), '/T', '/F' ])
        return True

    @classmethod
    def AddTimer(cls, name, timer):
        if name in cls.namedTimers:
            cls.StopTimer(name)
        cls.namedTimers[name] = timer

    @classmethod
    def StopTimer(cls, name):
        if cls.namedTimers[name] is not None:
            cls.namedTimers[name].stop()
            cls.namedTimers[name] = None

    @classmethod
    def StopTimers(cls):
        for name in cls.namedTimers:
            cls.StopTimer(name)