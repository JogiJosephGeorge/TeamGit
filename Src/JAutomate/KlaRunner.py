# coding=utf-8
from collections import OrderedDict
from datetime import datetime
import itertools
import json
import os
import re
import subprocess
import sys
import shutil

class Menu:
	def __init__(self, klaRunner, testRunner):
		self.klaRunner = klaRunner
		self.testRunner = testRunner
		self.prettyTable = PrettyTable()
		self.settings = Settings(klaRunner.model)
		self.klaSourceBuilder = KlaSourceBuilder(klaRunner.model)
		self.appRunner = AppRunner(klaRunner.model, testRunner)

	def PrintMainMenu(self):
		model = self.klaRunner.model
		testRunner = self.testRunner
		sourceBuilder = self.klaSourceBuilder
		autoTest = ('Run Auto test', 'Startup Auto test') [model.StartUp]
		if model.DebugVision:
			autoTest += ' (attach MMi)'
		menuData = [
			['Src', model.Source],
			['Test', model.TestName],
			['Branch', model.Branch],
			['-'],
			[1, 'Open Python', self.klaRunner.OpenPython],
			[2, autoTest, testRunner.RunAutoTest],
			[3, 'Run Handler and MMi', self.appRunner.StartHandlerMMi],
			[4, 'Run Handler alone', self.appRunner.StartHandler],
			[5, 'Run MMi from Source', self.appRunner.StartMMi, True],
			[6, 'Run MMi from C:Icos', self.appRunner.StartMMi, False],
			[],
			[10, 'Open Solution CIT100', self.klaRunner.OpenSolution, 0],
			[11, 'Open Solution CIT100Simulator', self.klaRunner.OpenSolution, 1],
			[12, 'Open Solution Mmi', self.klaRunner.OpenSolution, 2],
			[14, 'Open Solution MockLicense', self.klaRunner.OpenSolution, 3],
			[15, 'Open Solution Converters', self.klaRunner.OpenSolution, 4],
			[16, 'Open Test Folder', self.klaRunner.OpenTestFolder],
			[17, 'Open Git GUI', GitHelper.OpenGitGui, model.Source],
			[18, 'Open Local Differences', OsOperations.OpenLocalDif, model.Source],
			[],
			[20, 'Comment Line in VisionSystem', testRunner.ModifyVisionSystem],
			[21, 'Copy Mock License', testRunner.CopyMockLicense],
			[22, 'Copy xPort_IllumReference.xml', self.appRunner.CopyIllumRef],
			[23, 'Print All Branches', self.klaRunner.PrintBranches],
			[24, 'Print Missing IDs in mmi.h', self.klaRunner.PrintMissingIds],
			[],
			[90, 'Settings', self.PrintSettingsMenu],
			[91, 'Build', sourceBuilder.BuildSource, [1]],
			[92, 'Clean Build', sourceBuilder.CleanSource, [1, 3]],
			[99, 'Stop All KLA Apps', OsOperations.StopTask],
			[0, 'EXIT']
		]
		userIn = self.PrintMenu(menuData, 2)
		return userIn

	def PrintSettingsMenu(self):
		settings = self.settings
		menuData = [
			['Num', 'Description'],
			['-'],
			[1, 'Change Test', settings.ChangeTest],
			[2, 'Change Source', settings.ChangeSource],
			[3, 'Change Startup / Run ', settings.ChangeStartup],
			[4, 'Change MMI Attach', settings.ChangeDebugVision],
		]
		userIn = self.PrintMenu(menuData, 2)
		cnt = len(userIn)
		if cnt == 3:
			userIn[2]()

	def PrintMenu(self, data, colCnt):
		self.prettyTable.SetDoubleLineBorder()
		self.prettyTable.PrintTable(data, colCnt)
		userIn = OsOperations.InputNumber('Type the number then press ENTER: ')
		for item in data:
			if len(item) > 0 and item[0] == userIn:
				return item
		print 'Wrong input is given !!!'
		return [-1]

class KlaRunner:
	def __init__(self):
		self.model = Model()
		self.model.ReadConfigFile()
		self.prettyTable = PrettyTable()
		testRunner = TestRunner(self.model)
		self.menu = Menu(self, testRunner)

	def Start(self):
		while True:
			userIn = self.menu.PrintMainMenu()
			if userIn[0] == 0:
				break
			cnt = len(userIn)
			if cnt == 3:
				userIn[2]()
			elif cnt == 4:
				userIn[2](userIn[3])

	def OpenSolution(self, index):
		param = [
			self.model.VisualStudioRun,
			self.model.Source + self.model.Solutions[index]
		]
		subprocess.Popen(param)

	def OpenPython(self):
		fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
		subprocess.call(['python', '-i', fileName])

	def OpenTestFolder(self):
		dirPath = self.model.Source + '/handler/tests/' + self.model.TestName
		dirPath = os.path.abspath(dirPath)
		subprocess.Popen(['Explorer', dirPath])

	def PrintBranches(self, branchNums = ''):
		data = [
			['Source', 'Branch'],
			['-']
		]
		tempSources = []
		orgSources = self.model.Sources
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
			branch = GitHelper.GetBranch(src)
			if branch == self.model.Source:
				self.model.Branch = branch
			data.append([src, branch])
		self.prettyTable.SetSingleLine()
		self.prettyTable.PrintTable(data)
		OsOperations.Pause()

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
		OsOperations.Pause()

class AppRunner:
	def __init__(self, model, testRunner):
		self.model = model
		self.prettyTable = PrettyTable()
		self.testRunner = testRunner

	def StartHandler(self):
		OsOperations.StopTask()

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
		OsOperations.StopTask('MMi.exe')
		self.testRunner.RunSlots()

		mmiPath = self.testRunner.CopyMockLicense(fromSrc, False)
		self.CopyIllumRef(False)

		OsOperations.Timeout(8)

		mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')

		par = 'start ' + mmiExe
		print par
		os.system(par)

	def StartHandlerMMi(self):
		self.StartHandler()
		self.StartMMi(True)

	def CopyIllumRef(self, doPause = True):
		OsOperations.CopyFile('xPort_IllumReference.xml', 'C:/icos/xPort')
		if doPause:
			OsOperations.Pause()

class TestRunner:
	def __init__(self, model):
		self.model = model

	def CopyMockLicense(self, fromSrc = True, doPause = True):
		if fromSrc:
			mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(self.model.Source, self.model.Platform, self.model.Config))
		else:
			mmiPath = 'C:/icos'
		licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
		licenseFile = os.path.abspath(licencePath.format(self.model.Source, self.model.Platform, self.model.Config))
		OsOperations.CopyFile(licenseFile, mmiPath)
		if doPause:
			OsOperations.Pause()
		return mmiPath

	def ModifyVisionSystem(self, doPause = True):
		line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
		oldLine = ' ' + line
		newLine = ' #' + line
		fileName = os.path.abspath(self.model.Source + '/libs/testing/visionsystem.py')
		with open(fileName) as f:
			newText = f.read().replace(oldLine, newLine)
		with open(fileName, "w") as f:
			f.write(newText)
		print 'The line for copying of slots in VisionSystem.py has been commented.'
		if doPause:
			OsOperations.Pause()

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
				OsOperations.Pause()
				print 'Slot : ' + str(slot) + ' started.'
		print 'Slots refreshed : ' + str(self.model.slots)

	def RunAutoTest(self):
		OsOperations.StopTask()

		self.RunSlots()

		self.ModifyVisionSystem(False)

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

		my.run(self.model.TestName)

class Settings:
	def __init__(self, model):
		self.model = model
		self.prettyTable = PrettyTable()

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
		self.prettyTable.SetSingleLine()
		self.prettyTable.PrintTable(data)
		number = OsOperations.InputNumber('Select number : ')
		if number > 0 and number <= len(arr):
			return number - 1
		else:
			print 'Wrong input is given !!!'
		return -1

class KlaSourceBuilder:
	def __init__(self, model):
		self.model = model
		self.prettyTable = PrettyTable()

	def CleanSource(self, srcIndices):
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
		sources = self.GetSources(srcIndices)
		for src in sources:
			print 'Preparing directories to be deleted in ' + src
			for root, dirs, files in os.walk(src):
				relPath = os.path.relpath(root, src)
				if relPath in excludeList:
					continue
				if relPath[:4] == 'libs':
					continue
				for dir in dirs:
					d = dir.lower()
					if d == 'obj' or d == 'bin' or d == 'debug':
						toDelete.append(os.path.abspath(root + '/' + dir))
			if len(toDelete) == 0:
				print src + ' is clean'
				OsOperations.Pause()
				continue
			print 'The following directories will be deleted.'
			i = 1
			for dir in toDelete:
				print dir
				i += 1
				if i == 20:
					OsOperations.Pause()
			if raw_input('Do you want to continue (Yes/No) : ') == 'Yes':
				for dir in toDelete:
					if os.path.isdir(dir):
						shutil.rmtree(dir)

	def BuildSource(self, srcIndices):
		outFileNames = [ 'Handler', 'Simulator', 'MMi', 'Mock', 'Converters' ]
		sources = self.GetSources(srcIndices)
		buildLoger = BuildLoger(self.model.LogFileName)
		for src in sources:
			buildLoger.StartSource(src)
			for sln, name in itertools.izip(self.model.Solutions, outFileNames):
				if name == 'Handler' or name == 'MMi':
					continue
				platform = self.model.Platform
				if name == 'Simulator':
					platform = 'x64' if self.model.Platform == 'x64' else 'x86'
				BuildConf = self.model.Config + '|' + platform
				slnFile = os.path.abspath(src + '/' + sln)
				outFile = os.path.abspath(src + '/Out_' + name) + '.txt'

				buildLoger.StartSolution(sln, name, self.model.Config, platform)
				params = [self.model.VisualStudioBuild, slnFile, '/build', BuildConf, '/out', outFile]
				OsOperations.Popen(params, buildLoger.PrintMsg)
				buildLoger.EndSolution()
			buildLoger.EndSource(src)
		OsOperations.Pause()

	def GetSources(self, srcIndices):
		sources = []
		if len(srcIndices) == 0:
			sources.append(self.model.Source)
		else:
			for index in srcIndices:
				if index < 0 or index >= len(self.model.Sources):
					print 'Wrong index has been given !!!'
					return
				sources.append(self.model.Sources[index - 1])
		return sources

class BuildLoger:
	def __init__(self, fileName):
		self.fileName = fileName
		self.prettyTable = PrettyTable()

	def StartSource(self, src):
		self.srcStartTime = datetime.now()
		self.Log('Source : ' + src)
		self.Log('Branch : ' + GitHelper.GetBranch(src))
		self.logDataTable = [
			[ 'Solution', 'Config', 'Platform', 'Succeeded', 'Failed', 'Up To Date', 'Skipped', 'Time Taken' ],
			['-']
		]

	def EndSource(self, src):
		timeDelta = OsOperations.TimeDeltaToStr(datetime.now() - self.srcStartTime)
		self.Log('Completed building : {} in {}'.format(src, timeDelta))
		self.prettyTable.SetSingleLine()
		table = self.prettyTable.ToString(self.logDataTable)
		print table
		OsOperations.Append(self.fileName, table)

	def StartSolution(self, slnFile, name, config, platform):
		self.Log('Start building : ' + slnFile)
		self.slnStartTime = datetime.now()
		self.logDataRow = []
		self.logDataRow.append(name)
		self.logDataRow.append(config)
		self.logDataRow.append(platform)

	def EndSolution(self):
		timeDelta = OsOperations.TimeDeltaToStr(datetime.now() - self.slnStartTime)
		self.logDataRow.append(timeDelta)
		self.logDataTable.append(self.logDataRow)

	def Log(self, message):
		print message
		message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
		OsOperations.Append(self.fileName, message)

	def PrintMsg(self, message):
		if '>----' in message:
			print message
		if '=====' in message:
			print message
			nums = self.GetBuildStatus(message)
			if len(nums) == 4:
				self.logDataRow.append(nums[0])
				self.logDataRow.append(nums[1])
				self.logDataRow.append(nums[2])
				self.logDataRow.append(nums[3])

	def GetBuildStatus(self, message):
		nums = []
		searchPattern = r'Build: (\d*) succeeded, (\d*) failed, (\d*) up-to-date, (\d*) skipped'
		m = re.search(searchPattern, message, re.IGNORECASE)
		if m:
			nums.append(int(m.group(1)))
			nums.append(int(m.group(2)))
			nums.append(int(m.group(3)))
			nums.append(int(m.group(4)))
		return nums

class OsOperations:
	@classmethod
	def CopyFile(self, Src, Des):
		par = 'COPY /Y "' + Src + '" "' + Des + '"'
		print 'par : ' + par
		os.system(par)

	@classmethod
	def CopyDir(self, Src, Des):
		par = 'XCOPY /S /Y "' + Src + '" "' + Des + '"'
		print 'Src : ' + Src
		print 'Des : ' + Des
		print 'par : ' + par
		os.system(par)

	@classmethod
	def Pause(self):
		raw_input('Press any key to continue...')

	@classmethod
	def StopTask(self, exeName = ''):
		exeList = []
		if exeName is '':
			exeList = [
				'Mmi.exe',
				'console.exe',
				'CIT100Simulator.exe',
				'HostCamServer.exe',
				'Ves.exe'
			]
		else:
			exeList.append(exeName)

		params = [ 'TASKKILL', '/IM', '', '/T', '/F' ]
		for exe in exeList:
			if self.GetExeInstanceCount(exe) > 0:
				print exeName
				params[2] = exe
				OsOperations.Popen(params)

	@classmethod
	def GetExeInstanceCount(self, exeName):
		exeName = exeName.lower()
		params = [ 'TASKLIST', '/FI' ]
		params.append('IMAGENAME eq {}'.format(exeName))
		output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
		count = 0
		for line in output.splitlines():
			line = line.lower()
			if line[:len(exeName)] == exeName:
				count += 1
		return count

	@classmethod
	def OpenLocalDif(self, source):
		par = [ 'TortoiseGitProc.exe' ]
		par.append('/command:diff')
		par.append('/path:' + source + '')
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)

	@classmethod
	def Timeout(self, seconds):
		par = 'timeout ' + str(seconds)
		os.system(par)

	@classmethod
	def InputNumber(self, message):
		userIn = raw_input(message)
		while True:
			if userIn != '':
				return int(userIn)
			userIn = raw_input()

	@classmethod
	def Popen(self, params, callPrint = None):
		process = subprocess.Popen(params, stdout=subprocess.PIPE)
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
				outLine = output.strip()
				if callPrint is not None:
					callPrint(output.strip())
				else:
					print output.strip()
		return process.poll()

	@classmethod
	def Append(self, fileName, message):
		with open(fileName, 'a') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def TimeDeltaToStr(self, delta):
		s = delta.seconds
		t = '{:02}:{:02}:{:02}'.format(s // 3600, s % 3600 // 60, s % 60)
		return t

class PrettyTable:
	def __init__(self):
		self.SetSingleLine()

	def SetSingleLine(self):
		self.chTopLef = u'┌'
		self.chTopMid = u'┬'
		self.chTopRig = u'┐'
		self.chMidLef = u'├'
		self.chMidMid = u'┼'
		self.chMidRig = u'┤'
		self.chBotLef = u'└'
		self.chBotMid = u'┴'
		self.chBotRig = u'┘'
		self.chVerLef = u'│'
		self.chVerMid = u'│'
		self.chVerRig = u'│'
		self.chHorLef = u'─'
		self.chHorMid = u'─'
		self.chHorRig = u'─'

	def SetDoubleLineBorder(self):
		self.chTopLef = u'╔'
		self.chTopMid = u'╤'
		self.chTopRig = u'╗'
		self.chMidLef = u'╟'
		self.chMidMid = u'┼'
		self.chMidRig = u'╢'
		self.chBotLef = u'╚'
		self.chBotMid = u'╧'
		self.chBotRig = u'╝'
		self.chVerLef = u'║'
		self.chVerMid = u'│'
		self.chVerRig = u'║'
		self.chHorLef = u'═'
		self.chHorMid = u'─'
		self.chHorRig = u'═'

	def SetDoubleLine(self):
		self.chTopLef = u'╔'
		self.chTopMid = u'╦'
		self.chTopRig = u'╗'
		self.chMidLef = u'╠'
		self.chMidMid = u'╬'
		self.chMidRig = u'╣'
		self.chBotLef = u'╚'
		self.chBotMid = u'╩'
		self.chBotRig = u'╝'
		self.chVerLef = u'║'
		self.chVerMid = u'║'
		self.chVerRig = u'║'
		self.chHorLef = u'═'
		self.chHorMid = u'═'
		self.chHorRig = u'═'

	def PrintTable(self, data, colCnt = 0):
		print self.ToString(data, colCnt)

	def ToString(self, data, colCnt = 0):
		outMessage = ''
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

		outMessage += self.PrintLine(colWidths, self.chTopLef, self.chTopMid, self.chTopRig, self.chHorLef)

		for line in data:
			if len(line) == 0:
				outMessage += self.PrintLine(colWidths, self.chVerLef, self.chVerMid, self.chVerRig, ' ')
			elif len(line) == 1 and line[0] == '-':
				outMessage += self.PrintLine(colWidths, self.chMidLef, self.chMidMid, self.chMidRig, self.chHorMid)
			else:
				outMessage += self.chVerLef
				for i in range(0, colCnt):
					cell = ''
					alignMode = 1
					if i < len(line):
						if isinstance(line[i], int):
							alignMode = 2
						cell = str(line[i])
					outMessage += self.GetAligned(cell, colWidths[i], alignMode)
					if i == colCnt - 1:
						outMessage += self.chVerRig
					else:
						outMessage += self.chVerMid
				outMessage += '\n'
		outMessage += self.PrintLine(colWidths, self.chBotLef, self.chBotMid, self.chBotRig, self.chHorRig)
		return outMessage

	def GetAligned(self, message, width, mode):
		if mode == 2:
			return message.center(width)
		elif mode == 3:
			return message.rjust(width)
		return message.ljust(width)

	def PrintLine(self, colWidths, left, mid, right, fill):
		line = left
		colCnt = len(colWidths)
		for i in range(0, colCnt - 1):
			line += fill * colWidths[i] + mid
		line += fill * colWidths[-1] + right
		return line + '\n'

	def PrintTable1(self, data):
		try:
			for line in data:
				for cell in line:
					print cell,
				print ''
		except Exception as ex:
			print(ex)

class GitHelper:
	@classmethod
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

	@classmethod
	def OpenGitGui(self, source):
		param = [
			'git-gui',
			'--working-dir',
			source
		]
		subprocess.Popen(param)

class Model:
	def __init__(self):
		self.fileName = 'KlaRunner.ini'

		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []

	def ReadConfigFile(self):
		with open(self.fileName) as f:
			_model = json.load(f)
		
		self.Sources = _model['Sources']
		self.SrcIndex = _model['SrcIndex']
		self.Tests = _model['Tests']
		self.TestIndex = _model['TestIndex']
		self.Solutions = _model['Solutions']
		self.VisualStudioBuild = _model['VisualStudioBuild']
		self.VisualStudioRun = _model['VisualStudioRun']
		self.VMwareWS = _model['VMwareWS']
		self.MMiConfigPath = _model['MMiConfigPath']
		self.MMiSetupsPath = _model['MMiSetupsPath']
		self.Config = _model['Config']
		self.Platform = _model['Platform']
		self.StartUp = _model['StartUp']
		self.DebugVision = _model['DebugVision']
		self.CopyMmi = _model['CopyMmi']
		self.LogFileName = _model['LogFileName']
		
		self.UpdateSource()
		self.UpdateTest()

	def UpdateSource(self):
		self.Source = self.Sources[self.SrcIndex]
		self.Branch = GitHelper.GetBranch(self.Source)
		
	def UpdateTest(self):
		testAndSlots = self.Tests[self.TestIndex].split()
		self.TestName = testAndSlots[0]
		self.slots = map(int, testAndSlots[1].split('_'))

	def WriteConfigFile(self):
		_model = OrderedDict()
		_model['Sources'] = self.Sources
		_model['SrcIndex'] = self.SrcIndex
		_model['Tests'] = self.Tests
		_model['TestIndex'] = self.TestIndex
		_model['Solutions'] = self.Solutions
		_model['VisualStudioBuild'] = self.VisualStudioBuild
		_model['VisualStudioRun'] = self.VisualStudioRun
		_model['VMwareWS'] = self.VMwareWS
		_model['MMiConfigPath'] = self.MMiConfigPath
		_model['MMiSetupsPath'] = self.MMiSetupsPath
		_model['Config'] = self.Config
		_model['Platform'] = self.Platform
		_model['StartUp'] = self.StartUp
		_model['DebugVision'] = self.DebugVision
		_model['CopyMmi'] = self.CopyMmi
		_model['LogFileName'] = self.LogFileName

		with open(self.fileName, 'w') as f:
			json.dump(_model, f, indent=3)

KlaRunner().Start()
