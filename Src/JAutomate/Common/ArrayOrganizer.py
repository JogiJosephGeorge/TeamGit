import itertools


class ArrayOrganizer:
    def __init__(self):
        self.DefaultCell = ['', '']

    def Transform(self, arrOfArr, colCnt):
        newArrArr = []
        arLen = len(arrOfArr)
        for i in range(0, arLen, colCnt):
            group = []
            for j in range(i, i + colCnt):
                if j < arLen:
                    group.append(arrOfArr[j]),
            for tranGrp in itertools.izip_longest(*tuple(group)):
                row = []
                for item in tranGrp:
                    row += item if item else self.DefaultCell
                newArrArr.append(row)
        return newArrArr

    @classmethod
    def ContainsInArray(cls, str, strArray):
        for inx, item in enumerate(strArray):
            if str in item:
                return inx
        return -1
