# coding=utf-8
from Common.Test import Test


class TableLineRow:
    def __init__(self, left, mid, fill, right):
        self.chLef = left
        self.chMid = mid
        self.chRig = right
        self.chFil = fill

    def __iter__(self):
        yield self.chLef
        yield self.chMid
        yield self.chRig
        yield self.chFil


class TableFormat:
    def SetSingleLine(self):
        self.Top = TableLineRow(u'┌', u'┬', u'─', u'┐')
        self.Mid = TableLineRow(u'├', u'┼', u'─', u'┤')
        self.Emt = TableLineRow(u'│', u'│', u' ', u'│')
        self.Ver = TableLineRow(u'│', u'│', u' ', u'│')
        self.Bot = TableLineRow(u'└', u'┴', u'─', u'┘')
        return self

    def SetDoubleLineBorder(self):
        self.Top = TableLineRow(u'╔', u'╤', u'═', u'╗')
        self.Mid = TableLineRow(u'╟', u'┼', u'─', u'╢')
        self.Emt = TableLineRow(u'║', u'│', u' ', u'║')
        self.Ver = TableLineRow(u'║', u'│', u' ', u'║')
        self.Bot = TableLineRow(u'╚', u'╧', u'═', u'╝')
        return self

    def SetDoubleLine(self):
        self.Top = TableLineRow(u'╔', u'╦', u'═', u'╗')
        self.Mid = TableLineRow(u'╠', u'╬', u'═', u'╣')
        self.Emt = TableLineRow(u'║', u'║', u' ', u'║')
        self.Ver = TableLineRow(u'║', u'║', u' ', u'║')
        self.Bot = TableLineRow(u'╚', u'╩', u'═', u'╝')
        return self

    def SetNoBorder(self, sep):
        self.Top = TableLineRow(u'', u'', u'', u'')
        self.Mid = TableLineRow(u'', u'', u'', u'')
        self.Emt = TableLineRow(u'', u'', u'', u'')
        self.Ver = TableLineRow(u'', sep, u'', u'')
        self.Bot = TableLineRow(u'', u'', u'', u'')
        return self


class PrettyTable:
    def __init__(self, format):
        self.Format = format

    def PrintTable(self, data):
        print self.ToString(data)

    def CalculateColWidths(self, data):
        colCnt = 0
        colWidths = []
        for line in data:
            colCnt = max(colCnt, len(line))
            for i, cell in enumerate(line):
                if isinstance(cell, list):
                    if len(cell) > 0:
                        celStr = str(cell[0])
                else:
                    celStr = str(cell)
                width = len(celStr)
                if len(colWidths) > i:
                    colWidths[i] = max(colWidths[i], width)
                else:
                    colWidths.append(width)
        return colCnt, colWidths

    def ToString(self, data):
        colCnt, colWidths = self.CalculateColWidths(data)
        outLines = []
        outLines.append(self.GetFormattedLine(colWidths, self.Format.Top))
        [left, mid, right, fill] = list(self.Format.Ver)
        for line in data:
            if len(line) == 0:
                outLines.append(self.GetFormattedLine(colWidths, self.Format.Emt))
            elif len(line) == 1 and line[0] == '-':
                outLines.append(self.GetFormattedLine(colWidths, self.Format.Mid))
            else:
                outLine = left
                for inx,colWidth in enumerate(colWidths):
                    cell = line[inx] if len(line) > inx else ''
                    alignMode = ('<', '^')[isinstance(cell, int) and not isinstance(cell, bool)]
                    if isinstance(cell, list) and len(cell) > 0:
                        cell = cell[0]
                    outLine += self.GetAligned(str(cell), colWidths[inx], alignMode)
                    outLine += (mid, right)[inx == colCnt - 1]
                outLines.append(outLine)
        outLines.append(self.GetFormattedLine(colWidths, self.Format.Bot))
        trimmedLines = []
        for line in outLines:
            if line:
                trimmedLines.append(line)
        return '\n'.join(trimmedLines)

    def GetAligned(self, message, width, mode):
        return '{{:{}{}}}'.format(mode, width).format(message)

    def GetFormattedLine(self, colWidths, formatRow):
        [left, mid, right, fill] = list(formatRow)
        colCnt = len(colWidths)
        getCell = lambda : fill * colWidth + (mid, right)[colCnt - 1 == inx]
        line = left + ''.join([getCell() for inx,colWidth in enumerate(colWidths)])
        #return (line + '\n', '')[line == '']
        return line

    def PrintTableNoFormat(self, data):
        for line in data:
            print ''.join(line)

    @classmethod
    def PrintArray(cls, arr, colCnt):
        for inx, item in enumerate(arr):
            if inx % colCnt == 0:
                print
            print item,


class TestPrettyTable:
    def __init__(self):
        self.TableLineRowToSet()
        self.SingleLine()
        self.DoubleLineBorder()
        self.DoubleLine()
        self.NoBorder()

    def TableLineRowToSet(self):
        pass

    def SingleLine(self):
        data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], [], ['ICOS', 12345, False]]
        expected = u'''
┌────┬─────┬─────┐
│ColA│Col B│Col C│
├────┼─────┼─────┤
│KLA │  2  │True │
│    │     │     │
│ICOS│12345│False│
└────┴─────┴─────┘
'''[1:]
        actual = PrettyTable(TableFormat().SetSingleLine()).ToString(data)
        #print actual
        Test.AssertMultiLines(actual, expected)

    def DoubleLineBorder(self):
        data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], ['ICOS', 12345, False]]
        expected = u'''
╔════╤═════╤═════╗
║ColA│Col B│Col C║
╟────┼─────┼─────╢
║KLA │  2  │True ║
║ICOS│12345│False║
╚════╧═════╧═════╝
'''[1:]
        actual = PrettyTable(TableFormat().SetDoubleLineBorder()).ToString(data)
        #print actual
        Test.AssertMultiLines(actual, expected)

    def DoubleLine(self):
        data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], ['ICOS', 12345, False]]
        expected = u'''
╔════╦═════╦═════╗
║ColA║Col B║Col C║
╠════╬═════╬═════╣
║KLA ║  2  ║True ║
║ICOS║12345║False║
╚════╩═════╩═════╝
'''[1:]
        actual = PrettyTable(TableFormat().SetDoubleLine()).ToString(data)
        #print actual
        Test.AssertMultiLines(actual, expected)

    def NoBorder(self):
        data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], ['ICOS', 12345, False]]
        expected = u'''
ColA,Col B,Col C
KLA ,  2  ,True 
ICOS,12345,False
'''[1:]
        actual = PrettyTable(TableFormat().SetNoBorder(',')).ToString(data)
        #print actual
        Test.AssertMultiLines(actual, expected)
