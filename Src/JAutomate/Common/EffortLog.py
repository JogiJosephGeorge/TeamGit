from datetime import datetime, timedelta

from Common.DateTimeOps import DateTimeOps
from Common.FileOperations import FileOperations
from Common.NumValDict import NumValDict
from Common.OsOperations import OsOperations
from Common.PrettyTable import TableFormat, PrettyTable
from Common.Test import Test


class EffortReader:
    def __init__(self):
        self.LogFileEncode = 'UTF-16'
        self.DTFormat = '%d-%b-%Y %H:%M:%S'
        self.DayStarts = timedelta(hours=4) # 4am
        self.MaxReportDays = 90

    def ReadFile(self, logFile):
        self.content = []
        for line in FileOperations.ReadLine(logFile, self.LogFileEncode):
            if line[:7] == 'Current':
                continue
            lineParts = self.FormatText(line).split('$')
            if len(lineParts) > 2:
                self.content.append(lineParts)
            else:
                print 'Error: ' + line

    def GetDetailedEfforts(self, date):
        if len(self.content) is 0:
            return
        dictAppNameToTime = NumValDict()
        lastDt = None
        totalTime = timedelta()
        for lineParts in self.content:
            dt = datetime.strptime(lineParts[0], self.DTFormat)
            if not DateTimeOps.IsSameDate(dt, date, self.DayStarts):
                continue
            ts = (dt - lastDt) if lastDt is not None else (dt-dt)
            txt = self.PrepareDescription(lineParts[1], lineParts[2])
            dictAppNameToTime.Add(txt, ts)
            lastDt = dt
            totalTime += ts
        return dictAppNameToTime, totalTime

    def GetDailyLog(self):
        if len(self.content) is 0:
            return
        lastDt = None
        actualTime = None
        date = None
        data = []
        self.weeklyHours = timedelta()
        self.lastDay = 0
        def AddRow(d1, d2, t1, isLast):
            formattedDayStart = d1.strftime('%d-%b-%Y %a %H:%M')
            formattedDayEnd = d2.strftime('%H:%M')
            formattedTime = DateTimeOps.Strftime(t1, '{:02}:{:02}')
            todayInt = int(d1.strftime('%w'))
            if self.lastDay > todayInt:
                weeklyTotal = DateTimeOps.Strftime(self.weeklyHours, '{:02}:{:02}')
                data.append(['', '', '', weeklyTotal])
                self.weeklyHours = timedelta()
            self.weeklyHours += t1
            self.lastDay = todayInt
            data.append([formattedDayStart, formattedDayEnd, formattedTime, ''])
            if isLast:
                weeklyTotal = DateTimeOps.Strftime(self.weeklyHours, '{:02}:{:02}')
                data.append(['', '', '', weeklyTotal])
        startDate = datetime.now().today() - timedelta(days=self.MaxReportDays)
        for lineParts in self.content:
            dt = datetime.strptime(lineParts[0], self.DTFormat)
            if dt > startDate:
                if DateTimeOps.IsSameDate(dt, date, self.DayStarts):
                    ts = dt - lastDt
                    if len(lineParts[1] + lineParts[2]) > 0:
                        actualTime += ts
                else:
                    if date is not None:
                        AddRow(date, lastDt, actualTime, False)
                    date = dt
                    actualTime = timedelta()
            lastDt = dt
        AddRow(date, lastDt, actualTime, True)
        return data,actualTime

    def FormatText(self, message):
        return message.encode('ascii', 'ignore').decode('ascii')

    def PrepareDescription(self, message1, message2):
        groupNames = [
            'Google Chrome',
            'Internet Explorer',
            'explorer.exe',
            'OUTLOOK',
        ]
        for name in groupNames:
            if name in message1 or name in message2:
                return name
        message = message2 if len(message2) > 50 else message1 + '$' + message2
        message = message.replace('[Administrator]', '')
        return message

    def CheckApplication(self):
        if len(OsOperations.GetProcessIds('EffortCapture_2013.exe')) > 0:
            print 'Effort logger is running.'
        else:
            print 'Effort logger is not running !'


class EffortLogger:
    def __init__(self):
        self.ColWidth = 80
        self.MinMinutes = 3
        self.MinTime = timedelta(minutes=self.MinMinutes)
        self.ShowPrevDaysLogs = 1

    def PrintEffortLogInDetail(self, effortLogFile):
        reader = EffortReader()
        reader.ReadFile(effortLogFile)
        dateFormat = '%d-%b-%Y'
        for i in range(self.ShowPrevDaysLogs, 0, -1):
            prevDay = datetime.now() - timedelta(days=i)
            formattedDay = prevDay.strftime(dateFormat)
            self.PrintEffortTable(prevDay, formattedDay, reader)
        today = datetime.now()
        self.PrintEffortTable(today, 'Today', reader)
        reader.CheckApplication()

    def PrintEffortTable(self, date, message, reader):
        dictAppNameToTime, totalTime = reader.GetDetailedEfforts(date)
        if dictAppNameToTime is None:
            return
        data = []
        oneMinAppsTime = timedelta()
        dollarTime = timedelta()
        for k,v in dictAppNameToTime.items():
            if v > self.MinTime:
                data.append([self.Trim(k, self.ColWidth), v])
            else:
                oneMinAppsTime += v
            if k == '$':
                dollarTime = v
        minAppDesc = 'Other Apps Less Than {} Minute(s)'.format(self.MinMinutes)
        data.append([minAppDesc, oneMinAppsTime])
        data = sorted(data, key = lambda x : x[1], reverse=True)
        menuData = [[message, 'Time Taken'], ['-']] + data
        menuData += [['-'], ['Total Time', totalTime]]
        menuData += [['Actual Time', totalTime - dollarTime]]
        table = PrettyTable(TableFormat().SetSingleLine()).ToString(menuData)
        #table = datetime.now().strftime('%Y %b %d %H:%M:%S\n') + table
        #FileOperations.Append(logFile + '.txt', table)
        print table,

    def PrintDailyLog(self, effortLogFile):
        reader = EffortReader()
        reader.ReadFile(effortLogFile)
        data,todaysTime = reader.GetDailyLog()
        if data is None:
            return
        effortData = [['Daily Start Time', 'End Time', 'Log', 'Total'], ['-']] + data
        table = PrettyTable(TableFormat().SetDoubleLine()).ToString(effortData)
        print table,
        print (datetime.now() + timedelta(hours=9) - todaysTime).strftime('%H:%M')
        #csvTable = PrettyTable(TableFormat().SetNoBorder(u',')).ToString(effortData)
        #print csvTable,
        reader.CheckApplication()

    def Trim(self, message, width):
        if len(message) > width:
            return message[:width / 2 - 1] + '...' + message[2 - width / 2:]
        return message


class TestEffortLogger:
    def __init__(self):
        self.EL = EffortLogger()
        self.TestTrim()

    def TestTrim(self):
        Test.Assert(self.EL.Trim('India is my country', 10), 'Indi...try')
        Test.Assert(self.EL.Trim('India is my country', 15), 'India ...untry')
