from collections import OrderedDict
import json
import os
import re
import subprocess
import sys
import shutil

class KlaRunner:

	def __init__(self):
		self.model = Model()
		self.model.ReadConfigFile()

	def StartLoop(self):
		while True:
			userIn = self.PrintMainMenu()
			if userIn[0] == 0:
				break
			cnt = len(userIn)
			if cnt == 3:
				userIn[2]()
			elif cnt == 4:
				userIn[2](userIn[3])

	def PrintMainMenu(self):
		autoTest = ('Run Auto test', 'Startup Auto test') [self.model.StartUp]
		if self.model.DebugVision:
			autoTest += ' (attach MMi)'
		menuData = [
			['Src', self.model.Source],
			['Test', self.model.TestName],
			['Branch', self.model.Branch],
			['-'],
			[1, 'Open Python', self.OpenPython],
			[2, autoTest, self.RunAutoTest],
			[3, 'Run Handler and MMi', self.StartHandlerMMi],
			[4, 'Run Handler alone', self.StartHandler],
			[5, 'Run MMi from Source', self.StartMMi, True],
			[6, 'Run MMi from C:Icos', self.StartMMi, False],
			[],
			[11, 'Open Solution CIT100', self.OpenSolution, 0],
			[12, 'Open Solution CIT100Simulator', self.OpenSolution, 1],
			[14, 'Open Solution Mmi', self.OpenSolution, 2],
			[15, 'Open Solution MockLicense', self.OpenSolution, 3],
			[16, 'Open Solution Converters', self.OpenSolution, 4],
			[17, 'Open Test Folder', self.OpenTestFolder],
			[18, 'Open Git GUI', self.OpenGitGui],
			[19, 'Open Local Differences', osOper.OpenLocalDif, self.model.Source],
			[],
			[20, 'Comment Line in VisionSystem', self.ModifyVisionSystem],
			[21, 'Copy Mock License', self.CopyMockLicense],
			[22, 'Copy xPort_IllumReference.xml', self.CopyIllumRef],
			[23, 'Print All Branches', self.PrintBranches],
			[24, 'Print Missing IDs in mmi.h', self.PrintMissingIds],
			[],
			[90, 'Settings', self.PrintSettingsMenu],
			[91, 'Build', self.BuildSource],
			[92, 'Clean Build', self.CleanSource],
			[99, 'Kill All', osOper.KillTask],
			[0, 'EXIT']
		]
		userIn = self.PrintMenu(menuData, 2)
		return userIn

	def PrintSettingsMenu(self):
		menuData = [
			[1, 'Change Test', self.ChangeTest],
			[2, 'Change Source', self.ChangeSource],
			[3, 'Change Startup / Run ', self.ChangeStartup],
			[4, 'Change MMI Attach', self.ChangeDebugVision],
		]
		userIn = self.PrintMenu(menuData, 2)
		cnt = len(userIn)
		if cnt == 3:
			userIn[2]()

	def CleanSource(self):
		print 'Preparing directories to be deleted...'
		toDelete = []
		excludeList = []
		excludeList.append('libs\\external\\ezio')
		excludeList.append('handler\\scripts\\appy')
		excludeList.append('handler\\BNR\\CI_controller\\VS\\Devices\\BaseMotor')
		excludeList.append('handler\\BNR\\CI_controller\\VS\\Kito\\master')
		excludeList.append('handler\\BNR\\CI_controller\\VS\\PSM\\io_ctrl')
		excludeList.append('handler\\FabLink\\FabLinkLib\\lib')
		excludeList.append('tools\\ReportConfigurator\\ReportConfigurator.Tests\\bin')
		excludeList.append('tools\\ReportConfigurator\\ReportConfigurator.Tests')
		for root, dirs, files in os.walk(self.model.Source):
			relPath = os.path.relpath(root, self.model.Source)
			if relPath in excludeList:
				continue
			if relPath[:4] == 'libs':
				continue
			for dir in dirs:
				d = dir.lower()
				if d == 'obj' or d == 'bin' or d == 'debug':
					toDelete.append(os.path.abspath(root + '/' + dir))
		if len(toDelete) == 0:
			print 'Source is clean'
			return
		print 'The following directories will be deleted.'
		i = 1
		for dir in toDelete:
			print dir
			i += 1
			if i == 20:
				osOper.Pause()
		if raw_input('Do you want to continue (Yes/No) : ') == 'Yes':
			for dir in toDelete:
				shutil.rmtree(dir)

	def BuildSource(self):
		outFileNames = [ 'Handler', 'Simulator', 'MMi', 'Mock', 'Converters' ]
		i = 0
		branch = GitHelper().GetBranch(self.model.Source)
		print 'Build source : {} {}'.format(self.model.Source, branch)
		for sln in self.model.Solutions:
			platform = self.model.Platform
			if outFileNames[i] == 'Simulator':
				platform = 'x64' if self.model.Platform == 'x64' else 'x86'
			BuildConf = self.model.Config + '|' + platform
			slnFile = os.path.abspath(self.model.Source + '/' + sln)
			outFile = os.path.abspath(self.model.Source + '/' + outFileNames[i]) + '.txt'

			print 'Start building : ' + slnFile

			devEnvCom = 'C:/Program Files (x86)/Microsoft Visual Studio 12.0/Common7/IDE/devenv.com'
			params = [devEnvCom, slnFile, '/build', BuildConf, '/out', outFile]
			output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
			print str(output)

			i += 1

	def OpenSolution(self, index):
		param = [
			self.model.DevEnv,
			self.model.Source + self.model.Solutions[index]
		]
		subprocess.Popen(param)

	def OpenGitGui(self):
		param = [
			'git-gui',
			'--working-dir',
			self.model.Source
		]
		subprocess.Popen(param)

	def OpenPython(self):
		fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
		subprocess.call(['python', '-i', fileName])

	def OpenTestFolder(self):
		dirPath = self.model.Source + '/handler/tests/' + self.model.TestName
		dirPath = os.path.abspath(dirPath)
		subprocess.Popen(['Explorer', dirPath])

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
		PrettyTable().PrintTable(data)
		number = osOper.InputNumber('Select number : ')
		if number > 0 and number <= len(arr):
			return number - 1
		else:
			print 'Wrong input is given !!!'
		return -1

	def PrintMenu(self, data, colCnt):
		prettyTable.PrintTable(data, colCnt)
		userIn = osOper.InputNumber('Type the number then press ENTER: ')
		for item in data:
			if len(item) > 0 and item[0] == userIn:
				return item
		print 'Wrong input is given !!!'
		return [-1]

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

	def CopyMockLicense(self):
		LicenseFile = self.model.Source + '/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/Win32/Debug/License.dll'
		LicenseFile = os.path.abspath(LicenseFile)
		Destin = self.model.Source + '/mmi/mmi/Bin/Win32/Debug'
		Destin = os.path.abspath(Destin)
		osOper.CopyFile(LicenseFile, Destin)
		osOper.Pause()
		#self.CopyFile(LicenseFile, 'C:/icos')

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

		osOper.KillTask()

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
		my.c.mmiConfigurationsPath = self.model.MMiConfigPath
		my.c.mmiSetupsPath = self.model.MMiSetupsPath
		#print str(my.c)
		#raw_input('hi')

		my.run(self.model.TestName)

	def StartHandler(self):
		osOper.KillTask()

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

	def StartMMi(self, fromSrc):
		osOper.KillTask('MMi.exe')
		self.RunSlots()

		MmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(self.model.Source, self.model.Platform, self.model.Config))
		print 'MmiPath  :' + MmiPath
		MockPath = os.path.abspath('{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}'.format(self.model.Source, self.model.Platform, self.model.Config))
		print 'MockPath : ' + MockPath

		osOper.CopyFile(MockPath, MmiPath)
		self.CopyIllumRef()

		osOper.Timeout(8)

		if fromSrc:
			mmiExe = os.path.abspath(MmiPath + '/Mmi.exe')
		else:
			mmiExe = os.path.abspath('C:/Icos/Mmi.exe')

		par = 'start ' + mmiExe
		print par
		os.system(par)

	def CopyIllumRef(self):
		osOper.CopyFile('xPort_IllumReference.xml', 'C:/icos/xPort')
		osOper.Pause()

	def StartHandlerMMi(self):
		self.StartHandler()
		self.StartMMi(True)

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
		prettyTable.PrintTable(data)
		raw_input('Press any key to continue...')

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
		osOper.Pause()

class OsOperations:
	def CopyFile(self, Src, Des):
		par = 'COPY /Y "' + Src + '" "' + Des + '"'
		print 'par : ' + par
		os.system(par)

	def CopyDir(self, Src, Des):
		par = 'XCOPY /S /Y "' + Src + '" "' + Des + '"'
		print 'Src : ' + Src
		print 'Des : ' + Des
		print 'par : ' + par
		os.system(par)

	def Pause(self):
		raw_input('Press any key to continue...')

	def KillTask(self, exeName = ''):
		print 'exeName : ' + exeName
		par = 'KillAll ' + exeName
		print 'par : ' + par
		os.system(par)

	def OpenLocalDif(self, source):
		par = [ 'TortoiseGitProc.exe' ]
		par.append('/command:diff')
		par.append('/path:' + source + '')
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)

	def Timeout(self, seconds):
		par = 'timeout ' + str(seconds)
		os.system(par)

	def InputNumber(self, message):
		userIn = raw_input(message)
		while True:
			if userIn != '':
				return int(userIn)
			userIn = raw_input()

class PrettyTable:
	def SetSingleLineBorder(self):
		self.chTopLef = chr(218)
		self.chTopMid = chr(194)
		self.chTopRig = chr(191)
		self.chMidLef = chr(195)
		self.chMidMid = chr(197)
		self.chMidRig = chr(180)
		self.chBotLef = chr(192)
		self.chBotMid = chr(193)
		self.chBotRig = chr(217)
		self.chVertic = chr(179)
		self.chHorizo = chr(196)

	def SetDoubleLineBorder(self):
		self.chTopLef = chr(201)
		self.chTopMid = chr(203)
		self.chTopRig = chr(187)
		self.chMidLef = chr(204)
		self.chMidMid = chr(206)
		self.chMidRig = chr(185)
		self.chBotLef = chr(200)
		self.chBotMid = chr(202)
		self.chBotRig = chr(188)
		self.chVertic = chr(186)
		self.chHorizo = chr(205)

	def PrintTable(self, data, colCnt = 0):
		calculateColCnt = colCnt == 0
		colWidths = []

		if calculateColCnt:
			self.SetSingleLineBorder()
		else:
			self.SetDoubleLineBorder()

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

		self.PrintLine(colWidths, self.chTopLef, self.chTopMid, self.chTopRig, self.chHorizo)

		for line in data:
			if len(line) == 0:
				self.PrintLine(colWidths, self.chVertic, self.chVertic, self.chVertic, ' ')
			elif len(line) == 1 and line[0] == '-':
				self.PrintLine(colWidths, self.chMidLef, self.chMidMid, self.chMidRig, self.chHorizo)
			else:
				toPrint = self.chVertic
				for i in range(0, colCnt):
					cell = ''
					if i < len(line):
						cell = str(line[i])
					cell = cell.ljust(colWidths[i])
					toPrint += cell + ' ' + self.chVertic
				print toPrint
		self.PrintLine(colWidths, self.chBotLef, self.chBotMid, self.chBotRig, self.chHorizo)

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
		with open('KlaRunner.ini') as f:
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

		with open('KlaRunner.ini', 'w') as f:
			json.dump(_model, f, indent=3)

prettyTable = PrettyTable()
osOper = OsOperations()
KlaRunner().StartLoop()
