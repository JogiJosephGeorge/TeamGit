import msvcrt
import os
import subprocess


class OsOperations:
    @classmethod
    def Cls(cls):
        os.system('cls')

    @classmethod
    def System(cls, params, message = None):
        if message is None:
            print params
        else:
            print message
        os.system(params)

    @classmethod
    def GetProcessIds(cls, exeName):
        exeName = exeName.lower()
        params = [ 'TASKLIST', '/FI' ]
        params.append('IMAGENAME eq {}'.format(exeName))
        output = OsOperations.ProcessOpen(params)
        processIds = []
        for line in output.splitlines():
            parts = line.lower().split()
            if len(parts) > 2 and parts[0] == exeName:
                processIds.append(int(parts[1]))
        return processIds

    @classmethod
    def Timeout(cls, seconds):
        os.system('timeout ' + str(seconds))

    @classmethod
    def InputNumber(cls, message):
        userIn = cls.Input(message)
        while True:
            if userIn != '':
                return int(userIn)
            userIn = raw_input()

    @classmethod
    def FlushInput(cls):
        while msvcrt.kbhit():
            msvcrt.getch(),

    @classmethod
    def Input(cls, message):
        cls.FlushInput()
        return raw_input(message)

    @classmethod
    def Popen(cls, params, callPrint = None, returnOutput = False):
        if not callPrint and not returnOutput:
            print params
            subprocess.Popen(params)
            return
        process = subprocess.Popen(params, stdout=subprocess.PIPE)
        retVal = ''
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                outLine = output.strip()
                if callPrint:
                    callPrint(outLine)
                if returnOutput:
                    retVal += outLine + '\n'
        process.poll()
        return retVal

    @classmethod
    def ProcessOpen(cls, params):
        return subprocess.Popen(params, stdout=subprocess.PIPE, shell=True).communicate()[0]

    @classmethod
    def Call(cls, params):
        print params
        subprocess.call(params)

    @classmethod
    def ChDir(cls, path):
        os.chdir(path[:2])
        os.chdir(path)
