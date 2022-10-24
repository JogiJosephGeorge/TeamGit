from Common.Test import Test

class PathOps:
    @classmethod
    def SplitFilePath(cls, filePath):
        filePath = filePath.replace('/', '\\')
        parts = filePath.split('\\')
        if len(parts) == 0:
            return ('', '')
        elif len(parts) == 1:
            return ('', parts[0])
        elif len(parts) == 2:
            return (parts[0], parts[1])
        path = '\\'.join(parts[:-1])
        return (path, parts[-1])

class TestPathOps:
    def __init__(self):
        self.DoTest('', '', '')
        self.DoTest('abc', '', 'abc')
        self.DoTest('C:/abc', 'C:', 'abc')
        self.DoTest('C:/abc/ba.txt', 'C:\\abc', 'ba.txt')

    def DoTest(self, fullPath, path, fileName):
        actualPath, actualFile = PathOps.SplitFilePath(fullPath)
        Test.Assert(actualPath, path)
        Test.Assert(actualFile, fileName)
