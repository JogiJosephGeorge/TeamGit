from Common.Clipboard import Clipboard


class SpecialTextOperations:
    def __init__(self):
        self.IgnoreTexts = [
            '[Frames below may be incorrect',
            'user32.dll!',
            'win32u.dll!',
            'gdi32full.dll!',
            'mfc140d.dll!',
            'comctl32.dll!',
            'clr.dll!',
            'mscoreei.dll!',
            'mscoree.dll!',
            'ntdll.dll!',
            'atlthunk.dll!'
        ]

    def ConvertStack(self):
        clipText = Clipboard.GetText()
        newClipText = ''
        for group in self.SplitGroups(clipText):
            tabs = ''
            newLines = []
            revGroup = group[::-1]
            for line in revGroup:
                if self.IsValidLine(line):
                    newLine = self.RemovePrefix(line)
                    newLine = tabs + self.RemoveParams(newLine)
                    newLines.append(newLine)
                    if len(line) > 0:
                        tabs += '\t'
            newClipText += ('\r\n').join(newLines)
            newClipText += '\r\n'
        Clipboard.SetText(newClipText)

    def SplitGroups(self, clipText):
        lines = self.SplitLines(clipText)
        lineGroup = []
        for line in lines:
            lineGroup.append(line)
            if len(line) == 0:
                yield  lineGroup
                lineGroup = []
        yield lineGroup

    def IsValidLine(self, line):
        for startTxt in self.IgnoreTexts:
            if startTxt == line[0:len(startTxt)]:
                return False
        return True

    def SplitLines(self, text):
        text = text.replace('\r\n', '\n')
        return text.split('\n')

    def RemovePrefix(self, text):
        index = text.find('!') + 1
        if index < 1:
            return text.strip()
        return text[index:]

    def RemoveParams(self, text):
        startIndex = text.find('(') + 1
        endIndex = text.find(') Line ')
        if startIndex < 0 or endIndex < 0 or startIndex >= endIndex:
            return text
        return text[:startIndex] + '...' + text[endIndex:]
