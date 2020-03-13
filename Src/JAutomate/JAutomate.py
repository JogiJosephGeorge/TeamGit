from collections import OrderedDict
import json
import os
import re
import subprocess
import sys
import shutil

class JAutomate:

	def __init__(self):
		self.model = Model()

	def StartLoop(self):
		self.model.ReadConfigFile()

		while True:
			userIn = self.PrintMenu()
			if userIn[0] == 0:
				break
			cnt = len(userIn)
			if cnt == 3:
				userIn[2]()
			elif cnt == 4:
				userIn[2](userIn[3])

	def PrintMenu(self):
		autoTest = ('Run Auto test', 'Startup Auto test') [self.model.StartUp]
		if self.model.DebugVision:
			autoTest += ' (attach MMi)'
		mainMenu = [
			['Src', self.model.Source],
			['Test', self.model.TestName],
			['Branch', self.model.Branch],
			['-'],
			[1, 'Open Python', self.OpenPython],
			[2, autoTest, self.RunAutoTest],
			[3, 'Run MMi alone', self.StartMMi],
			[4, 'Run Handler and MMi', self.StartHandlerMMi],
			[],
			[11, 'Open Solution CIT100', self.OpenSolution, 0],
			[12, 'Open Solution CIT100Simulator', self.OpenSolution, 1],
			[14, 'Open Solution Mmi', self.OpenSolution, 2],
			[15, 'Open Solution MockLicense', self.OpenSolution, 3],
			[16, 'Open Solution Converters', self.OpenSolution, 4],
			[],
			[20, 'Modify VisionSystem', self.ModifyVisionSystem],
			[21, 'Copy Mock License', self.CopyMockLicense],
			[22, 'Copy xPort_IllumReference.xml', self.CopyIllumRef],
			[23, 'Open Test Folder', self.OpenTestFolder],
			[24, 'Open Local Differences', self.OpenLocalDif],
			[27, 'Print All Branches', self.PrintBranches],
			[28, 'Print Missing IDs in mmi.h', self.PrintMissingIds],
			[30, 'Change Test', self.ChangeTest],
			[31, 'Change Source', self.ChangeSource],
			[32, 'Change Startup / Run ', self.ChangeStartup],
			[33, 'Change MMI Attach', self.ChangeDebugVision],
			[],
			#[91, 'Build'],
			#[92, 'Clean Build'],
			[99, 'Kill All', self.KillTask],
			[0, 'EXIT']
		]

		self.PrintTable(mainMenu, 2)
		userIn = self.InputNumber('Type the number then press ENTER: ')
		for item in mainMenu:
			if len(item) > 0 and item[0] == userIn:
				return item
		print 'Wrong input {} is given !!!'.format(userIn)
		return [999]

	def InputNumber(self, message):
		userIn = raw_input(message)
		while True:
			if userIn != '':
				return int(userIn)
			userIn = raw_input()

	def OpenSolution(self, index):
		param = [
			self.model.DevEnv,
			self.model.Source + self.model.Solutions[index]
		]
		subprocess.Popen(param)

	def OpenPython(self):
		fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
		subprocess.call(['python', '-i', fileName])

	def OpenTestFolder(self):
		dirPath = self.model.Source + '/handler/tests/' + self.model.TestName
		dirPath = os.path.abspath(dirPath)
		subprocess.call(['Explorer', dirPath])

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

	def SelectOption(self, name, arr, currentIndex = -1):
		data = [
			['Num', name],
			['-']
		]

		i = 0
		for item in arr:
			line = ('  ', '* ')[i == currentIndex] + item
			i += 1
			data.append([i, line])

		self.PrintTable(data)
		number = self.InputNumber('Select number : ')
		if number <= len(arr):
			return number - 1
		else:
			print 'Wrong input {} is given !!!'.format(number)
		return -1

	def ChangeTest(self):
		number = self.SelectOption('Test Name', self.model.Tests, self.model.TestIndex)
		if number >= 0:
			self.model.TestIndex = number
			self.model.UpdateTest()
			self.model.WriteConfigFile()

	def ChangeSource(self):
		number = self.SelectOption('Source', self.model.Sources, self.model.SrcIndex)
		if number >= 0:
			self.model.SrcIndex = number
			self.model.UpdateSource()
			self.model.WriteConfigFile()

	def ChangeStartup(self):
		arr = [ 'Startup only', 'Run test' ]
		index = 0 if self.model.StartUp else 1
		number = self.SelectOption('Options', arr, index)
		if number >= 0:
			self.model.StartUp = number == 0
			self.model.WriteConfigFile()

	def ChangeDebugVision(self):
		arr = [ 'Attach MMi', 'Do not attach' ]
		index = 0 if self.model.DebugVision else 1
		number = self.SelectOption('Options', arr, index)
		if number >= 0:
			self.model.DebugVision = number == 0
			self.model.WriteConfigFile()

	def OpenLocalDif(self):
		par = 'TortoiseGitProc.exe /command:diff /path:' + self.model.Source + ''
		print 'par : ' + par
		os.popen(par)

		#par = [ 'TortoiseGitProc.exe' ]
		#par.append('/command:diff /path:"' + self.model.Source + '"')
		#print 'par : ' + str(par)
		#subprocess.Popen(par)

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
		LicenseFile = self.model.Source + '/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/Win32/Debug/License.dll'
		LicenseFile = os.path.abspath(LicenseFile)
		Destin = self.model.Source + '/mmi/mmi/Bin/Win32/Debug'
		Destin = os.path.abspath(Destin)
		self.CopyFile(LicenseFile, Destin)
		#self.CopyFile(LicenseFile, 'C:/icos')
	
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
		fileName = os.path.abspath(self.model.Source + '/libs/testing/visionsystem.py')
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
		print 'Slots refreshed : ' + str(self.model.slots)

	def RunAutoTest(self):

		self.KillTask()

		self.RunSlots()

		self.ModifyVisionSystem()

		sys.path.append(os.path.abspath(self.model.Source + '\\libs\\testing'));
		import my

		my.c.startup = self.model.StartUp
		my.c.debugvision = self.model.DebugVision
		my.c.copymmi = self.model.CopyMmi
		JConfig1 = 'r' if self.model.Config == 'Release' else 'd'
		my.c.console_config = JConfig1
		my.c.simulator_config = JConfig1

		if self.model.Config == 'Release':
			if self.model.Platform == 'Win32':
			  my.c.mmiBuildConfiguration = 'release'
			else:
			  my.c.mmiBuildConfiguration = 'releasex64'
		else:
			if self.model.Platform == 'Win32':
			  my.c.mmiBuildConfiguration = 'debug'
			else:
			  my.c.mmiBuildConfiguration = 'debugx64'
		my.c.platform = self.model.Platform
		my.c.mmiConfigurationsPath = self.InQuotes(self.model.MMiConfigPath)
		my.c.mmiSetupsPath = self.model.MMiSetupsPath
		#print str(my.c)
		#raw_input('hi')

		my.run(self.model.TestName)

	def InQuotes(self, message):
		return '"' + message + '"'

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

		consoleExe = self.model.Source + '/handler/cpp/bin/Win32/debug/system/console.exe'
		testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'
		par = 'start ' + consoleExe + ' ' + testTempDir
		print par
		os.system(par)

		simulatorExe = self.model.Source + '/handler/Simulator/ApplicationFiles/bin/x86/Debug/CIT100Simulator.exe'
		handlerSysPath = self.model.Source + '/handler/cpp/bin/Win32/debug/system'
		par = 'start ' + simulatorExe + ' ' + testTempDir + ' ' + handlerSysPath
		print par
		os.system(par)

	def StartMMi(self):
		self.KillTask('MMi.exe')
		self.RunSlots()

		MmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(self.model.Source, self.model.Platform, self.model.Config))
		print 'MmiPath  :' + MmiPath
		MockPath = os.path.abspath('{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}'.format(self.model.Source, self.model.Platform, self.model.Config))
		print 'MockPath : ' + MockPath

		self.CopyFile(MockPath, MmiPath)
		self.CopyIllumRef()

		self.Timeout(8)

		mmiExe = os.path.abspath(MmiPath + '/Mmi.exe')
		par = 'start ' + mmiExe
		print par
		os.system(par)

	def CopyIllumRef(self):
		self.CopyFile('xPort_IllumReference.xml', 'C:/icos/xPort')

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
					print 'Wrong Source index is given !!!'
				else:
					tempSources.append(orgSources[num - 1])
		for src in tempSources:
			branch = GitHelper().GetBranch(src)
			if branch == self.model.Source:
				self.model.Branch = branch
			data.append([src, branch])
		self.PrintTable(data)

	def PrintMissingIds(self):
		lastId = 1
		fileName = os.path.abspath(self.model.Source + '/mmi/mmi/mmi_lang/mmi.h')
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
	def GetBranch(self, Source):
		try:
			params = ['git', '-C', Source, 'branch']
			output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
			isCurrent = False
			for part in output.split():
				if isCurrent:
					return part
				if part == '*':
					isCurrent = True
		except Exception as ex:
			print(ex)

class Model:
	def __init__(self):
		self.Sources = []
		self.SrcIndex = -1
		self.Tests = []
		self.TestIndex = -1
		self.Solutions = []
		self.DevEnv = ''
		self.VMwareWS = ''
		self.MMiConfigPath = ''
		self.MMiSetupsPath = ''
		self.Config = ''
		self.Platform = ''
		self.StartUp = True
		self.DebugVision = False
		self.CopyMmi = True

		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []

	def GetSources(self):
		return self.Sources

	def ReadConfigFile(self):
		with open('JAutomate.ini') as f:
			_model = json.load(f)
		#print _model
		
		self.Sources = _model['Sources']
		self.SrcIndex = _model['SrcIndex']
		self.Tests = _model['Tests']
		self.TestIndex = _model['TestIndex']
		self.Solutions = _model['Solutions']
		self.DevEnv = _model['DevEnv']
		self.VMwareWS = _model['VMwareWS']
		self.MMiConfigPath = _model['MMiConfigPath']
		self.MMiSetupsPath = _model['MMiSetupsPath']
		self.Config = _model['Config']
		self.Platform = _model['Platform']
		self.StartUp = _model['StartUp']
		self.DebugVision = _model['DebugVision']
		self.CopyMmi = _model['CopyMmi']
		
		self.UpdateSource()
		self.UpdateTest()

	def UpdateSource(self):
		self.Source = self.Sources[self.SrcIndex]
		self.Branch = GitHelper().GetBranch(self.Source)
		
	def UpdateTest(self):
		testAndSlots = self.Tests[self.TestIndex].split()
		self.TestName = testAndSlots[0]
		self.slots = map(int, testAndSlots[1].split('_'))

	def WriteConfigFile(self):
		_model = {}
		_model['Sources'] = self.Sources
		_model['SrcIndex'] = self.SrcIndex
		_model['Tests'] = self.Tests
		_model['TestIndex'] = self.TestIndex
		_model['Solutions'] = self.Solutions
		_model['DevEnv'] = self.DevEnv
		_model['VMwareWS'] = self.VMwareWS
		_model['MMiConfigPath'] = self.MMiConfigPath
		_model['MMiSetupsPath'] = self.MMiSetupsPath
		_model['Config'] = self.Config
		_model['Platform'] = self.Platform
		_model['StartUp'] = self.StartUp
		_model['DebugVision'] = self.DebugVision
		_model['CopyMmi'] = self.CopyMmi

		with open('JAutomate.ini', 'w') as f:
			json.dump(_model, f, indent=3)
	
JAutomate().StartLoop()
