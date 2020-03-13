from collections import OrderedDict
import json
import os
import re
import subprocess
import sys
import shutil

class JAutomate:

	def __init__(self):
		self.model = Config()

	def StartLoop(self):
		self.model.ReadConfigFile()

		while True:
			userIn = self.PrintMenu()
			if userIn[0] == 0:
				break
			if len(userIn) != 3:
				print 'Wrong input !!!'
				continue;
			userIn[2]()

	def PrintMenu(self):
		mainMenu = [
			['Src', self.model.source],
			['Test', self.model.testName],
			['Branch', self.model.branch],
			['-'],
			[1, 'Open Python', self.OpenPython],
			[2, 'Run Auto test', self.RunAutoTest],
			[3, 'Run Handler alone', self.StartHandler],
			[4, 'Run MMi from Src', self.StartMMi],
			[5, 'Run Handler and MMi', self.StartHandlerMMi],
			[],
			[11, 'Open Solution CIT100', self.OpenCIT100Sln],
			[12, 'Open Solution CIT100Simulator', self.OpenCIT100SimulatorSln],
			[14, 'Open Solution Mmi', self.OpenMmiSln],
			[15, 'Open Solution MockLicense', self.OpenMockLicenseSln],
			[16, 'Open Solution Converters', self.OpenConvertersSln],
			[],
			[20, 'Open Test Folder', self.OpenTestFolder],
			[21, 'Open Local Differences', self.OpenLocalDif],
			[22, 'Change Test', self.SelectTest],
			[23, 'Print Missing IDs in mmi.h', self.PrintMissingIds],
			[24, 'Copy xPort_IllumReference.xml', self.CopyIllumRef],
			[25, 'Modify VisionSystem', self.ModifyVisionSystem],
			[26, 'Copy Mock License', self.CopyMockLicense],
			[27, 'Print All Branches', self.PrintBranches],
			[],
			#[91, 'Build'],
			#[92, 'Clean Build'],
			[99, 'Kill All', self.KillTask],
			[0, 'EXIT']
		]

		self.PrintTable(mainMenu, 2)
		userIn = input('Type the number then press ENTER: ')
		for item in mainMenu:
			if len(item) > 0 and item[0] == userIn:
				return item
		return [999]

	def OpenCIT100Sln(self):
		self.OpenSolution(0)

	def OpenCIT100SimulatorSln(self):
		self.OpenSolution(1)

	def OpenMmiSln(self):
		self.OpenSolution(2)

	def OpenMockLicenseSln(self):
		self.OpenSolution(3)

	def OpenConvertersSln(self):
		self.OpenSolution(4)

	def OpenSolution(self, index):
		param = [
			self.model.DevEnv,
			self.model.solutions[index]
		]
		subprocess.call(param)

	def CallBat(self, arr):
		buildAllBat = os.path.dirname(os.path.abspath(__file__)) + '\JBuildAll.bat'
		param = [buildAllBat] + arr
		print param
		subprocess.call(param)

	def OpenPython(self):
		subprocess.call(['python', '-i', self.model.source + '\\libs\\testing\\my.py'])

	def OpenTestFolder(self):
		self.CallBat(['JOpenTestFolder', self.model.source, self.model.testName])

	def PrintTable(self, data, colCnt = 0):
		try:
			calculateColCnt = colCnt == 0
			colWidths = []

			for line in data:
				i = 0
				for cell in line:
					if len(colWidths) > i:
						colWidths[i] = max(colWidths[i], len(str(cell)))
					else:
						colWidths.append(len(str(cell)))
					i = i + 1
					if calculateColCnt:
						colCnt = max(colCnt, i)
					else:
						if colCnt == i:
							break;

			chTopLef = chr(218)
			chTopMid = chr(194)
			chTopRig = chr(191)
			chMidLef = chr(195)
			chMidMid = chr(197)
			chMidRig = chr(180)
			chBotLef = chr(192)
			chBotMid = chr(193)
			chBotRig = chr(217)
			chVertic = chr(179)
			chHorizo = chr(196)

			self.PrintLine(colWidths, chTopLef, chTopMid, chTopRig, chHorizo)

			for line in data:
				if len(line) == 0:
					self.PrintLine(colWidths, chVertic, chVertic, chVertic, ' ')
				elif len(line) == 1 and line[0] == '-':
					self.PrintLine(colWidths, chMidLef, chMidMid, chMidRig, chHorizo)
				else:
					toPrint = chVertic
					for i in range(0, colCnt):
						cell = ''
						if i < len(line):
							cell = str(line[i])
						cell = cell.ljust(colWidths[i])
						toPrint += cell + ' ' + chVertic
					print toPrint
			self.PrintLine(colWidths, chBotLef, chBotMid, chBotRig, chHorizo)
		except Exception as ex:
			print(ex)

	def PrintLine(self, colWidths, left, mid, right, fill):
		line = left
		colCnt = len(colWidths)
		for i in range(0, colCnt - 1):
			line += fill * (colWidths[i] + 1) + mid
		line += fill * (colWidths[-1] + 1) + right
		print line

	def PrintTable1(self, data):
		try:
			for line in data:
				for cell in line:
					print cell,
				print ''
		except Exception as ex:
			print(ex)

	def SelectTest(self):
		data = [
			['Num', 'Test Name'],
			['-']
		]

		i = 1
		for line in self.model.tests:
			# print (str(i) + ' ' + line)
			data.append([i, line])
			i += 1

		self.PrintTable(data)

		number = input('Select number : ')
		self.model.testIndex = number - 1
		self.model.UpdateTest()
		self.model.WriteConfigFile()

	def OpenLocalDif(self):
		try:
			par = self.model.TortoiseBin + 'TortoiseGitProc.exe /command:diff /path:"' + self.model.source + '"'
			print 'par : ' + par
			os.system(par)
			# proc = subprocess.Popen([self.model.TortoiseBin + 'TortoiseGitProc.exe', '/command:diff', '/path:"' + self.model.source + '"'], stdin=subprocess.PIPE)
			# s,e = proc.communicate(None)
			# proc.poll()
			# print 'Out : ' + str(s)
			# print 'Err : ' + str(e)
		except Exception as ex:
			print(ex)

	def CopyDir(self, Src, Des):
		try:
			par = 'XCOPY /S /Y "' + Src + '" "' + Des + '"'
			print 'Src : ' + Src
			print 'Des : ' + Des
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def CopyMockLicense(self):
		LicenseFile = self.model.source + '\\mmi\\mmi\\mmi_stat\\integration\\code\\MockLicenseDll\\Win32\\Debug\\License.dll'
		Destin = self.model.source + '\\mmi\\mmi\\Bin\\Win32\\Debug'
		self.CopyFile(LicenseFile, Destin)
		#self.CopyFile(LicenseFile, 'C:\\icos')
	
	def CopyFile(self, Src, Des):
		try:
			par = 'COPY /Y "' + Src + '" "' + Des + '"'
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def ModifyVisionSystem(self):
		line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
		oldLine = ' ' + line
		newLine = ' #' + line
		fileName = self.model.source + '\\libs\\testing\\visionsystem.py'
		with open(fileName) as f:
			newText = f.read().replace(oldLine, newLine)
		with open(fileName, "w") as f:
			f.write(newText)

	def RunSlots(self):
		vmRunExe = self.model.VMwareWS + "vmrun.exe"
		vmWareExe = self.model.VMwareWS + "vmware.exe"
		vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'

		output = subprocess.Popen([vmRunExe, '-vp', '1', 'list'], stdout=subprocess.PIPE).communicate()[0]
		runningSlots = []
		searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
		for line in output.split():
			m = re.search(searchPattern, line, re.IGNORECASE)
			if m:
				runningSlots.append(int(m.group(1)))

		for slot in self.model.slots:
			vmxPath = vmxGenericPath.format(slot)
			if slot in runningSlots:
				print 'Slot : ' + str(slot) + ' restarted.'
				subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
			else:
				subprocess.Popen([vmWareExe, vmxPath])
				print 'Start Slot : ' + str(slot)
				raw_input("Press any key to continue...")
				print 'Slot : ' + str(slot) + ' started.'

	def RunAutoTest(self):

		self.KillTask()

		self.RunSlots()

		self.ModifyVisionSystem()

		sys.path.append(os.path.abspath(self.model.source + '\\libs\\testing'));
		import my

		my.c.startup = self.model.StartUp
		my.c.debugvision = self.model.DebugVision
		my.c.copymmi = self.model.CopyMmi
		JConfig1 = 'r' if self.model.config == 'Release' else 'd'
		my.c.console_config = JConfig1
		my.c.simulator_config = JConfig1

		if self.model.config == 'Release':
			if self.model.platform == 'Win32':
			  my.c.mmiBuildConfiguration = 'release'
			else:
			  my.c.mmiBuildConfiguration = 'releasex64'
		else:
			if self.model.platform == 'Win32':
			  my.c.mmiBuildConfiguration = 'debug'
			else:
			  my.c.mmiBuildConfiguration = 'debugx64'
		my.c.platform = self.model.platform
		my.c.mmiConfigurationsPath = self.model.MMiConfigPath
		my.c.mmiSetupsPath = self.model.MMiSetupsPath
		#print str(my.c)

		my.run(self.model.testName)

	def KillTask(self, exeName = ''):
		try:
			print 'exeName : ' + exeName
			par = 'KillAll ' + exeName
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def StartHandler(self):
		self.KillTask()

		consoleExe = self.model.source + '/handler/cpp/bin/Win32/debug/system/console.exe'
		testTempDir = self.model.source + '/handler/tests/' + self.model.testName + '~'
		par = 'start ' + consoleExe + ' ' + testTempDir
		print par
		os.system(par)

		simulatorExe = self.model.source + '/handler/Simulator/ApplicationFiles/bin/x86/Debug/CIT100Simulator.exe'
		handlerSysPath = self.model.source + '/handler/cpp/bin/Win32/debug/system'
		par = 'start ' + simulatorExe + ' ' + testTempDir + ' ' + handlerSysPath
		print par
		os.system(par)

	def StartMMi(self):
		self.KillTask('MMi.exe')
		self.RunSlots()

		MmiPath = self.model.source + '\\mmi\\mmi\\Bin\\' + self.model.platform + '\\' + self.model.config
		print 'MmiPath  :' + MmiPath
		MockPath = self.model.source + '\\mmi\\mmi\\mmi_stat\\integration\\code\\MockLicenseDll\\' + self.model.platform + '\\' + self.model.config
		print 'MockPath : ' + MockPath

		self.CopyFile(MockPath, MmiPath)
		self.CopyIllumRef()

		self.Timeout(8)

		mmiExe = MmiPath + '\\Mmi.exe'
		par = 'start ' + mmiExe
		print par
		os.system(par)

	def CopyIllumRef(self):
		self.CopyFile('xPort_IllumReference.xml', 'C:\\icos\\xPort')

	def StartHandlerMMi(self):
		self.StartHandler()
		self.StartMMi()

	def Timeout(self, seconds):
		try:
			par = 'timeout ' + str(seconds)
			print par
			os.system(par)
		except Exception as ex:
			print(ex)

	def PrintBranches(self, branchNums = ''):
		data = [
			['Source', 'Branch'],
			['-']
		]
		tempSources = []
		orgSources = self.model.GetSources()
		if branchNums == '':
			tempSources = orgSources
		else:
			for branchNum in branchNums.split():
				num = int(branchNum)
				if num > len(orgSources):
					print 'Wrong source index is given !!!'
				else:
					tempSources.append(orgSources[num - 1])
		for src in tempSources:
			data.append([src, GitHelper().GetBranch(src)])
		self.PrintTable(data)

	def PrintMissingIds(self):
		lastId = 1
		fileName = self.model.source + '\mmi\mmi\mmi_lang\mmi.h'
		print 'Missing IDs in ' + fileName
		singles = []
		sets = []
		with open(fileName) as file:
			lines = file.read().splitlines()
		for line in lines:
			parts = line.split()
			if len(parts) == 3:
				id = int(parts[2])
				if lastId + 1 < id:
					setStart = lastId + 1
					setEnd = id - 1
					if setStart == setEnd:
						singles.append(str(setStart).rjust(5))
					else:
						sets.append(('[' + str(setStart)).rjust(6) + ', ' + (str(setEnd) + ']').ljust(6))
				lastId = max(lastId, id)
		for i in range(0, len(singles)):
			if i % 15 == 0:
				print 
			print singles[i],
		for i in range(0, len(sets)):
			if i % 6 == 0:
				print 
			print sets[i],
		print 


class GitHelper:
	def GetBranch(self, source):
		try:
			params = ['git', '-C', source, 'branch']
			output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
			isCurrent = False
			for part in output.split():
				if isCurrent:
					return part
				if part == '*':
					isCurrent = True
		except Exception as ex:
			print(ex)


class Config:
	def __init__(self):
		self.sources = []
		self.srcIndex = -1
		self.tests = []
		self.testIndex = -1
		self.solutions = []
		self.DevEnv = ''
		self.TortoiseBin = ''
		self.VMwareWS = ''
		self.MMiConfigPath = ''
		self.MMiSetupsPath = ''
		self.config = 'Debug'
		self.platform = 'Win32'

		self.source = ''
		self.branch = ''
		self.testName = ''
		self.slots = []
		self.StartUp = True
		self.DebugVision = False
		self.CopyMmi = True

	def GetSources(self):
		return self.sources

	def ReadConfigFile(self):
		with open('JAutomate.ini') as f:
			_model = json.load(f)
		#print _model
		
		self.sources = _model['sources']
		self.srcIndex = _model['CurrentSrcIndex']
		self.tests = _model['tests']
		self.testIndex = _model['CurrentTestIndex']
		self.solutions = _model['Solutions']
		self.DevEnv = _model['DevEnv']
		self.TortoiseBin = _model['TortoiseBin']
		self.VMwareWS = _model['VMwareWS']
		self.MMiConfigPath = _model['MMiConfigPath']
		self.MMiSetupsPath = _model['MMiSetupsPath']
		self.config = _model['config']
		self.platform = _model['platform']
		
		self.UpdateSource()
		self.UpdateTest()

	def UpdateSource(self):
		self.source = self.sources[self.srcIndex]
		self.branch = GitHelper().GetBranch(self.source)
		
	def UpdateTest(self):
		testAndSlots = self.tests[self.testIndex].split()
		self.testName = testAndSlots[0]
		self.slots = map(int, testAndSlots[1].split('_'))

	def WriteConfigFile(self):
		_model = {}
		_model['sources'] = self.sources
		_model['CurrentSrcIndex'] = self.srcIndex
		_model['tests'] = self.tests
		_model['CurrentTestIndex'] = self.testIndex
		_model['Solutions'] = self.solutions
		_model['DevEnv'] = self.DevEnv
		_model['TortoiseBin'] = self.TortoiseBin
		_model['VMwareWS'] = self.VMwareWS
		_model['MMiConfigPath'] = self.MMiConfigPath
		_model['MMiSetupsPath'] = self.MMiSetupsPath
		_model['config'] = self.config
		_model['platform'] = self.platform

		with open('JAutomate.ini', 'w') as f:
			json.dump(_model, f, indent=3)
	
JAutomate().StartLoop()
