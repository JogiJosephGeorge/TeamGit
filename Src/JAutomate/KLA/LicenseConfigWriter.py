from Common.FileOperations import FileOperations

class LicenseConfigWriter:
    class LineType:
        Initial = 1
        StaticConst = 2
        Constru = 3
        Modules = 4
        Rest = 5

    def __init__(self, source, xmlFileName):
        fileName = source + '/mmi/mmi/env/LicenseComponents.cpp'
        self.ReadLicense(fileName)
        keyNameMap = self.MixMap()
        self.WriteXmlFile(xmlFileName, keyNameMap)
        modCnt = len(keyNameMap)
        msg = 'LicMgrConfig.xml with {} modules has been created as {}'
        print msg.format(modCnt, xmlFileName)

    def ReadLicense(self, fileName):
        self.IdNameMap = {}
        self.IdKeyMap = {}
        lines = FileOperations.ReadLine(fileName, 'utf-8')
        lineType = self.LineType.Initial
        for line in lines:
            if lineType == self.LineType.Initial:
                if self.IsStaticConst(line):
                    lineType = self.LineType.StaticConst
            if lineType == self.LineType.StaticConst:
                if not self.ReadStaticConst(line):
                    lineType = self.LineType.Constru
            elif lineType == self.LineType.Constru:
                if self.IsModules(line):
                    lineType = self.LineType.Modules
            if lineType == self.LineType.Modules:
                if not self.ReadModules(line):
                    return

    def IsStaticConst(self, line):
        return line.startswith('static const LPCSTR')

    def ReadStaticConst(self, line):
        if not self.IsStaticConst(line):
            return False
        parts = line[20:-1].replace('"', '').split(' = ')
        if len(parts) < 2:
            return False
        self.IdNameMap[parts[0]] = parts[1]
        return True

    def IsModules(self, line):
        return line.lstrip().startswith('m_Modules[')

    def ReadModules(self, line):
        if not self.IsModules(line):
            return False
        parts = line[13:-2].split('] = "')
        if len(parts) < 2:
            return False
        self.IdKeyMap[parts[0]] = parts[1]
        return True

    def MixMap(self):
        keyNameMap = {}
        for id in self.IdKeyMap:
            keyNameMap[self.IdKeyMap[id]] = self.IdNameMap[id]
        return keyNameMap

    def WriteXmlFile(self, fileName, keyNameMap):
        strArr = []
        strArr.append('<?xml version="1.0" encoding="utf-8"?>')
        strArr.append('<LicMgr xmlns="http://schemas.icos.be/global/LicMgrConfigFile-1.0">')
        strArr.append('    <Department name="Component Inspector MMI">')
        strArr.append('        <Modules>')
        for key in keyNameMap:
            strArr.append('            <Add name="{}" id="{}" />'.format(keyNameMap[key], key))
        strArr.append('        </Modules>')
        strArr.append('    </Department>')
        strArr.append('</LicMgr>')

        with open(fileName, 'w') as f:
            f.write('\n'.join(strArr))
