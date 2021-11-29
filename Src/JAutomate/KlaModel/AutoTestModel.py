from Common.PrettyTable import PrettyTable, TableFormat


class AutoTestModel:
    def __init__(self):
        self.Tests = []

    def Read(self, iniFile):
        testArray = iniFile.ReadField('Tests', [])
        self.Tests = []
        for item in testArray:
            nameSlot = self.Encode(item)
            if nameSlot is not None:
                self.Tests.append(nameSlot)

    def Write(self, iniFile):
        testArray = [self.Decode(item[0], item[1]) for item in self.Tests]
        iniFile.Write('Tests', testArray)

    def IsValidIndex(self, index):
        return index >= 0 and index < len(self.Tests)

    def GetNames(self):
        return [item[0] for item in self.Tests]

    def SetNameSlots(self, index, name, slots):
        if self.IsValidIndex(index):
            self.Tests[index] = [name, slots]

    def Contains(self, testName):
        for inx, item in self.Tests:
            if testName in item[0]:
                return inx

    def AddTestToModel(self, testName):
        slots = [1, 2]
        for item in self.Tests:
            if item[0] == testName:
                return -1
        self.Tests.append([testName, slots])
        return len(self.Tests) - 1

    def Encode(self, testNameSlots):
        parts = testNameSlots.split()
        if len(parts) > 1:
            return (parts[0], map(int, parts[1].split('_')))
        elif len(parts) > 0:
            return (parts[0], [])

    def Decode(self, testName, slots):
        slotStrs = [str(slot) for slot in slots]
        return '{} {}'.format(testName, '_'.join(slotStrs))

    def ToString(self):
        data = []
        index = 0
        for item in self.Tests:
            data.append([ str(index), str(item[0]), str(item[1]) ])
            index += 1
        return PrettyTable(TableFormat().SetSingleLine()).ToString(data)