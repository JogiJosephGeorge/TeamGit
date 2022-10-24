from Common.Clipboard import Clipboard


class SpecialTextOperations:

    def ConvertStack(self):
        clipText = Clipboard.GetText()
        lines = self.SplitLines(clipText)
        newLines = []
        lines = lines[::-1]
        tabs = ''
        for line in lines:
            if self.IsValidLine(line):
                newLine = self.RemovePrefix(line)
                newLine = tabs + self.RemoveParams(newLine)
                newLines.append(newLine)
                if len(line) > 0:
                    tabs += '\t'
        newLines.append('')
        newClipText = ('\r\n').join(newLines)
        Clipboard.SetText(newClipText)

    def IsValidLine(self, line):
        if '[Frames below may be incorrect' in line:
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
