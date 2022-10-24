from Common.PrettyTable import PrettyTable, TableFormat


class AutoTestModel:
    def __init__(self):
        self.Tests = []
        self.TestIndex = -1
        self.TestName = ''
        self.slots = []

    def Read(self, iniFile):
        testArray = iniFile.ReadField('Tests', [])
        self.Tests = []
        for item in testArray:
            nameSlot = self.Encode(item)
            if nameSlot is not None:
                self.Tests.append(nameSlot)
        self.TestIndex = iniFile.ReadField('TestIndex', -1)
        [self.TestName, self.slots] = self.Tests[self.TestIndex]

    def Write(self, iniFile):
        testArray = [self.Decode(item[0], item[1]) for item in self.Tests]
        iniFile.Write('Tests', testArray)
        iniFile.Write('TestIndex', self.TestIndex)

    def IsValidIndex(self, index):
        return index >= 0 and index < len(self.Tests)

    def GetNames(self):
        return [item[0] for item in self.Tests]

    def SetNameSlots(self, name, slots):
        if self.IsValidIndex(self.TestIndex):
            self.Tests[self.TestIndex] = [name, slots]

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

    def UpdateTest(self, index):
        if not self.IsValidIndex(index):
            self.TestIndex = 0 if len(self.Tests) > 0 else -1
            return False
        if self.TestIndex == index:
            return False
        self.TestIndex = index
        [self.TestName, self.slots] = self.Tests[self.TestIndex]
        return True

    def UpdateSlot(self, index, isSelected):
        slotNum = index + 1
        if isSelected:
            self.slots.append(slotNum)
            self.slots.sort()
        else:
            self.slots.remove(slotNum)
        self.SetNameSlots(self.TestName, self.slots)

    def SelectSlots(self, slots):
        self.slots = slots
        self.slots.sort()
        self.SetNameSlots(self.TestName, self.slots)
