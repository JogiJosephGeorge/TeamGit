# coding=utf-8
from collections import OrderedDict
import ctypes
from datetime import datetime
import itertools
import json
import threading
import os
import re
import subprocess
import sys
import shutil

class Menu:
	def __init__(self, klaRunner, model):
		self.klaRunner = klaRunner
		self.testRunner = TestRunner(model)
		self.settings = Settings(model)
		self.appRunner = AppRunner(model, self.testRunner)
		self.klaSourceBuilder = KlaSourceBuilder(model)

	def PrepareMainMenu(self):
		model = self.klaRunner.model
		seperator = ' : '
		menuData = [
			['Source', seperator, model.Source, ' '*5, 'Config', seperator, model.Config],
			['Branch', seperator, model.Branch, ' '*5, 'Platform', seperator, model.Platform],
			['Test', seperator, model.TestName, ' '*5, 'Copy MMI to Icos', seperator, model.CopyMmi]
		]
		PrettyTable().SetNoBorder('').PrintTable(menuData)

		testRunner = self.testRunner
		sourceBuilder = self.klaSourceBuilder
		settings = self.settings
		autoTest = ('', ' (attach MMi)')[model.DebugVision]
		activeSrcs = str([i + 1 for i in model.ActiveSrcs]).replace(' ', '') if len(model.ActiveSrcs) > 0 else ''
		group = [
		[
			[1, ['Open Python', self.klaRunner.OpenPython]],
			[2, ['Run test' + autoTest, testRunner.RunAutoTest, False]],
			[3, ['Start test' + autoTest, testRunner.RunAutoTest, True]],
			[4, ['Run Handler and MMi', self.appRunner.StartHandlerMMi]],
			[5, ['Run Handler alone', self.appRunner.StartHandler]],
			[6, ['Run MMi from Source', self.appRunner.StartMMi, True]],
			[7, ['Run MMi from C:Icos', self.appRunner.StartMMi, False]]
		],[
			[10, ['Open CIT100', sourceBuilder.OpenSolution, 0]],
			[11, ['Open Simulator', sourceBuilder.OpenSolution, 1]],
			[12, ['Open Mmi', sourceBuilder.OpenSolution, 2]],
			[14, ['Open MockLicense', sourceBuilder.OpenSolution, 3]],
			[15, ['Open Converters', sourceBuilder.OpenSolution, 4]],
		],[
			[20, ['Open Test Folder', self.klaRunner.OpenTestFolder]],
			[21, ['Open Local Diff', AppRunner.OpenLocalDif, model.Source]],
			[22, ['Open Git GUI', GitHelper.OpenGitGui, model.Source]],
			[23, ['Open Git Bash', GitHelper.OpenGitBash, (model.GitBin, model.Source)]],
			[24, ['Comment VisionSystem', testRunner.ModifyVisionSystem]],
			[25, ['Copy Mock License', testRunner.CopyMockLicense]],
			[26, ['Copy xPort xml', TestRunner.CopyIllumRef, model.ClearHistory]],
			[27, ['Print mmi.h IDs', self.klaRunner.PrintMissingIds]],
		],[
			[91, ['Build Source ' + activeSrcs, sourceBuilder.BuildSource]],
			[92, ['Clean Source ' + activeSrcs, sourceBuilder.CleanSource]],
			[93, ['Add Test', settings.AddTest]],
			[94, ['Change Test', settings.ChangeTest]],
			[95, ['Change Source', settings.ChangeSource]],
			[96, ['Change MMI Attach', settings.ChangeDebugVision]],
			[99, ['Stop All KLA Apps', AppRunner.StopTasks, True]],
			[0, 'EXIT']
		]]
		colCnt = model.MenuColCnt
		menuData = [ 
			['Num', 'Description'] * colCnt,
			['-']
		]
		return menuData + ArrayOrganizer().Transform(group, colCnt)

	def ReadUserInput(self):
		menuData = self.PrepareMainMenu()
		PrettyTable().SetDoubleLineBorder().PrintTable(menuData)
		userIn = OsOperations.InputNumber('Type the number then press ENTER: ')
		for row in menuData:
			for i in range(1, len(row)):
				if row[i - 1] == userIn:
					return row[i]
		print 'Wrong input is given !!!'
		return [-1]

class KlaRunner:
	def __init__(self):
		self.model = Model()
		self.model.ReadConfigFile()
		self.menu = Menu(self, self.model)

	def Start(self):
		if not ctypes.windll.shell32.IsUserAnAdmin():
			print 'Please run this application with Administrator privilates'
			OsOperations.Pause()
			return
		while True:
			if self.model.ClearHistory:
				OsOperations.Cls()
			else:
				print
			selItem = self.menu.ReadUserInput()
			if selItem == 'EXIT':
				break
			cnt = len(selItem)
			if cnt == 2:
				selItem[1]()
			elif cnt == 3:
				selItem[1](selItem[2])

	def OpenPython(self):
		fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
		par = 'start python -i ' + fileName
		print 'Starting my.py'
		os.system(par)

	def OpenTestFolder(self):
		dirPath = os.path.abspath(self.model.Source + '/handler/tests/' + self.model.TestName)
		subprocess.Popen(['Explorer', dirPath])
		print 'Open directory : ' + dirPath
		OsOperations.Pause(self.model.ClearHistory)

	def PrintMissingIds(self):
		fileName = os.path.abspath(self.model.Source + '/mmi/mmi/mmi_lang/mmi.h')
		ids = []
		with open(fileName) as file:
			for line in file.read().splitlines():
				parts = line.split()
				if len(parts) == 3:
					ids.append(int(parts[2]))
		print 'Missing IDs in ' + fileName
		singles = []
		sets = []
		lastId = 1
		for id in ids:
			if lastId + 2 == id:
				singles.append(lastId + 1)
			elif lastId + 2 < id:
				sets.append((lastId + 1, id - 1))
			lastId = max(lastId, id)
		PrettyTable.PrintArray([str(id).rjust(5) for id in singles], 15)
		pr = lambda st : '{:>6}, {:<6}'.format('[' + str(st[0]), str(st[1]) + ']')
		PrettyTable.PrintArray([pr(st) for st in sets], 6)
		print 
		OsOperations.Pause(self.model.ClearHistory)

class AppRunner:
	def __init__(self, model, testRunner):
		self.model = model
		self.testRunner = testRunner

	@classmethod
	def GetPlatform(self, platform, isSimulator = False):
		if isSimulator and 'Win32' == platform:
			platform = 'x86'
		return platform

	def StartHandler(self, doPause = True):
		self.StopTasks(False)

		config = self.model.Config
		platform = self.GetPlatform(self.model.Platform)
		handlerPath = '{}/handler/cpp/bin/{}/{}/system'.format(self.model.Source, platform, config)
		consoleExe = handlerPath + '/console.exe'
		testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'
		par = 'start ' + consoleExe + ' ' + testTempDir
		print par
		os.system(par)

		platform = self.GetPlatform(self.model.Platform, True)
		simulatorExe = '{}/handler/Simulator/ApplicationFiles/bin/{}/{}/CIT100Simulator.exe'
		simulatorExe = simulatorExe.format(self.model.Source, platform, config)
		par = 'start ' + simulatorExe + ' ' + testTempDir + ' ' + handlerPath
		print par
		os.system(par)
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def StartMMi(self, fromSrc, doPause = True):
		self.StopTask('MMi.exe')
		VMWareRunner.RunSlots(self.model.VMwareWS, self.model.slots)

		mmiPath = self.testRunner.CopyMockLicense(fromSrc, False)
		TestRunner.CopyIllumRef(False)

		OsOperations.Timeout(8)

		mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')

		par = 'start ' + mmiExe
		print par
		os.system(par)
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def StartHandlerMMi(self):
		self.StartHandler(False)
		self.StartMMi(True, False)
		OsOperations.Pause(self.model.ClearHistory)

	@classmethod
	def StopTasks(self, doPause):
		for exeName in [
			'Mmi.exe',
			'console.exe',
			'CIT100Simulator.exe',
			'HostCamServer.exe',
			'Ves.exe'
		]:
			AppRunner.StopTask(exeName)
		OsOperations.Pause(doPause)

	@classmethod
	def StopTask(self, exeName):
		if OsOperations.GetExeInstanceCount(exeName) > 0:
			print exeName
			OsOperations.Popen([ 'TASKKILL', '/IM', exeName, '/T', '/F' ])

	@classmethod
	def OpenLocalDif(self, source):
		par = [ 'TortoiseGitProc.exe' ]
		par.append('/command:diff')
		par.append('/path:' + source + '')
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)
		OsOperations.Pause()

class VMWareRunner:
	@classmethod
	def RunSlots(self, vMwareWS, slots):
		vmRunExe = vMwareWS + "vmrun.exe"
		vmWareExe = vMwareWS + "vmware.exe"
		vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'

		output = subprocess.Popen([vmRunExe, '-vp', '1', 'list'], stdout=subprocess.PIPE).communicate()[0]
		runningSlots = []
		searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
		for line in output.split():
			m = re.search(searchPattern, line, re.IGNORECASE)
			if m:
				runningSlots.append(int(m.group(1)))

		for slot in slots:
			vmxPath = vmxGenericPath.format(slot)
			if slot in runningSlots:
				print 'Slot : ' + str(slot) + ' restarted.'
				subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
			else:
				subprocess.Popen([vmWareExe, vmxPath])
				print 'Start Slot : ' + str(slot)
				OsOperations.Pause()
				print 'Slot : ' + str(slot) + ' started.'
		print 'Slots refreshed : ' + str(slots)

class TestRunner:
	def __init__(self, model):
		self.model = model

	def CopyMockLicense(self, fromSrc = True, doPause = True):
		if fromSrc:
			args = (self.model.Source, self.model.Platform, self.model.Config)
			mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(*args))
		else:
			mmiPath = 'C:/icos'
		licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
		args = (self.model.Source, self.model.Platform, self.model.Config)
		licenseFile = os.path.abspath(licencePath.format(*args))
		OsOperations.CopyFile(licenseFile, mmiPath)
		OsOperations.Pause(doPause and self.model.ClearHistory)
		return mmiPath

	@classmethod
	def CopyIllumRef(self, doPause = False):
		OsOperations.CopyFile('xPort_IllumReference.xml', 'C:/icos/xPort/')
		OsOperations.Pause(doPause)

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
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def GetBuildConfig(self):
		debugConfigSet = ('debugx64', 'debug')
		releaseConfigSet = ('releasex64', 'release')
		configSet = (debugConfigSet, releaseConfigSet)[self.model.Config == 'Release']
		return configSet[self.model.Platform == 'Win32']

	def RunAutoTest(self, startUp):
		AppRunner.StopTasks(False)
		VMWareRunner.RunSlots(self.model.VMwareWS, self.model.slots)
		self.ModifyVisionSystem(False)

		sys.path.append(os.path.abspath(self.model.Source + '\\libs\\testing'));
		import my
		my.c.startup = startUp
		my.c.debugvision = self.model.DebugVision
		my.c.copymmi = self.model.CopyMmi
		my.c.mmiBuildConfiguration = self.GetBuildConfig()
		my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
		my.c.platform = self.model.Platform
		my.c.mmiConfigurationsPath = self.model.MMiConfigPath
		my.c.mmiSetupsPath = self.model.MMiSetupsPath

		threading.Timer(15, self.CopyIllumRef).start()
		my.run(self.model.TestName)
		OsOperations.Pause(self.model.ClearHistory)

	@classmethod
	def GetTestName(self, source, number):
		print sys.path
		self.UpdateLibsTestingPath(source)
		print sys.path
		sys.stdout = stdOutRedirect = StdOutRedirect()
		from my import TestRunnerHelper
		TestRunnerHelper().l(number)
		msgs = stdOutRedirect.ResetOriginal()
		for msg in msgs.split('\n'):
			arr = msg.split(':')
			if len(arr) == 2 and arr[0].strip() == str(number):
				return arr[1].strip()
		return ''

	@classmethod
	def UpdateLibsTestingPath(self, source):
		libsTesting = '/libs/testing'
		index = OsOperations.ContainsInArray(libsTesting, sys.path)
		newPath = source + libsTesting
		if index >= 0:
			print 'Old path ({}) has been replaced with new path ({}).'.format(sys.path[index], newPath)
			sys.path[index] = newPath
		else:
			print 'New path ({}) has been added.'.format(newPath)
			sys.path.append(newPath)

class Settings:
	def __init__(self, model):
		self.model = model

	def ChangeTest(self):
		index = self.SelectOption1('Test Name', self.model.Tests, self.model.TestIndex)
		self.model.UpdateTest(index, True)
		OsOperations.Pause(self.model.ClearHistory)

	def AddTest(self):
		number = OsOperations.InputNumber('Type the number of test then press ENTER: ')
		testName = TestRunner.GetTestName(self.model.Source, number)
		if testName == '':
			print 'There is no test exists for the number : ' + str(number)
			return
		if OsOperations.ContainsInArray(testName, self.model.Tests) >= 0:
			print 'The given test ({}) already exists'.format(testName)
			return
		slots = raw_input('Enter slots : ')
		testNameAndSlot = '{} {}'.format(testName, slots)
		self.model.Tests.append(testNameAndSlot)
		self.model.UpdateTest(len(self.model.Tests) - 1, True)
		OsOperations.Pause(self.model.ClearHistory)

	def ChangeSource(self):
		heading, data = KlaSourceBuilder(self.model).GetSourceInfo(None)
		index = self.SelectOption(heading, data, self.model.SrcIndex)
		self.model.UpdateSource(index, True)
		OsOperations.Pause(self.model.ClearHistory)

	def ChangeDebugVision(self):
		arr = [ 'Attach MMi', 'Do not attach' ]
		index = 0 if self.model.DebugVision else 1
		number = self.SelectOption1('Options', arr, index)
		if number >= 0:
			self.model.DebugVision = number == 0
			self.model.WriteConfigFile()
		OsOperations.Pause(self.model.ClearHistory)

	def SelectOption1(self, heading, arr, currentIndex):
		arrOfArr = [[item] for item in arr]
		return self.SelectOption([heading], arrOfArr, currentIndex)

	def SelectOption(self, heading, arrOfArr, currentIndex):
		data = [
			['Num'] + heading,
			['-']
		]
		for i,line in enumerate(arrOfArr):
			line[0] = ('  ', '* ')[i == currentIndex] + line[0]
			data.append([i + 1] + line)
		PrettyTable().SetSingleLine().PrintTable(data)
		number = OsOperations.InputNumber('Type the number then press ENTER: ')
		if number > 0 and number <= len(arrOfArr):
			return number - 1
		else:
			print 'Wrong input is given !!!'
		return -1

class KlaSourceBuilder:
	def __init__(self, model):
		self.model = model
		self.Solutions = [
			'/handler/cpp/CIT100.sln',
			'/handler/Simulator/CIT100Simulator/CIT100Simulator.sln',
			'/mmi/mmi/Mmi.sln',
			'/mmi/mmi/MockLicense.sln',
			'/mmi/mmi/Converters.sln'
		]
		self.SlnNames = ['CIT100', 'Simulator', 'MMi', 'Mock', 'Converters']

	def GetSourceInfo(self, activeSrcs):
		heading = ['Source', 'Branch', 'Config', 'Platform']
		if activeSrcs == None:
			sources = list(self.model.Sources)
		elif len(activeSrcs) == 0:
			sources = [self.model.Sources[self.model.SrcIndex]]
		else:
			sources = [self.model.Sources[inx] for inx in activeSrcs]
		menuData = []
		for src in sources:
			branch = GitHelper.GetBranch(src[0])
			if src[0] == self.model.Source:
				self.model.Branch = branch
			menuData.append([src[0], branch, src[1], src[2]])
		return (heading, menuData)

	def PrintBranches(self, activeSrcs = None):
		heading, data = self.GetSourceInfo(activeSrcs)
		menuData = [ heading, ['-'] ] + data
		PrettyTable().SetSingleLine().PrintTable(menuData)
		return data

	def VerifySources(self, message):
		isAre = (' is', 's are')[len(self.model.ActiveSrcs) > 1]
		print 'The following source{} ready for {}.'.format(isAre, message)
		sources = self.PrintBranches(self.model.ActiveSrcs)
		question = 'Please type "Yes" to continue {} : '.format(message)
		if raw_input(question) == 'Yes':
			print 'Started {}...'.format(message)
		else:
			print 'Cancelled {}.'.format(message)
			sources = []
		return sources

	def CleanSource(self):
		excludeDirs = [
			'/mmi/mmi/.vs',
			'/mmi/mmi/packages',
			'/handler/cpp/.vs',
			'/Handler/FabLink/cpp/bin',
			'/Handler/FabLink/FabLinkLib/System32',
			]
		gitIgnore = '.gitignore'
		for srcSet in self.VerifySources('cleaning'):
			src = srcSet[0]
			print 'Cleaning files in ' + src
			OsOperations.DeleteAllInTree(src, gitIgnore)
			with open(src + '/' + gitIgnore, 'w') as f:
				f.writelines(str.join('\n', excludeDirs))
			GitHelper.Clean(src, '-fd')
			print 'Reseting files in ' + src
			GitHelper.ResetHard(src)
			print 'Submodule Update'
			GitHelper.SubmoduleUpdate(src)
			print 'Cleaning completed for ' + src
		OsOperations.Pause(self.model.ClearHistory)

	def BuildSource(self):
		buildLoger = BuildLoger(self.model.LogFileName)
		for source, branch, config, srcPlatform in self.VerifySources('building'):
			buildLoger.StartSource(source)
			for inx,sln in enumerate(self.Solutions):
				slnFile = os.path.abspath(source + '/' + sln)
				if not os.path.exists(slnFile):
					print "Solution file doesn't exist : " + slnFile
					continue
				isSimulator = sln.split('/')[-1] == 'CIT100Simulator.sln'
				platform = AppRunner.GetPlatform(srcPlatform, isSimulator)
				BuildConf = config + '|' + platform
				outFile = os.path.abspath(source + '/Out_' + self.SlnNames[inx]) + '.txt'

				buildLoger.StartSolution(sln, self.SlnNames[inx], config, platform)
				params = [self.model.VisualStudioBuild, slnFile, '/build', BuildConf, '/out', outFile]
				OsOperations.Popen(params, buildLoger.PrintMsg)
				buildLoger.EndSolution()
			buildLoger.EndSource(source)
		OsOperations.Pause(self.model.ClearHistory)

	def OpenSolution(self, index):
		fileName = self.model.Source + self.Solutions[index]
		param = [
			self.model.VisualStudioRun,
			fileName
		]
		subprocess.Popen(param)
		print 'Open solution : ' + fileName
		OsOperations.Pause(self.model.ClearHistory)

class BuildLoger:
	def __init__(self, fileName):
		self.fileName = fileName

	def StartSource(self, src):
		self.srcStartTime = datetime.now()
		self.Log('Source : ' + src)
		self.Log('Branch : ' + GitHelper.GetBranch(src))
		self.logDataTable = [
			[ 'Solution', 'Config', 'Platform', 'Succeeded', 'Failed', 'Up To Date', 'Skipped', 'Time Taken' ],
			['-']
		]

	def EndSource(self, src):
		timeDelta = self.TimeDeltaToStr(datetime.now() - self.srcStartTime)
		self.Log('Completed building : {} in {}'.format(src, timeDelta))
		table = PrettyTable().SetSingleLine().ToString(self.logDataTable)
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
		if len(self.logDataRow) == 3:
			self.logDataRow += [''] * 4
		timeDelta = self.TimeDeltaToStr(datetime.now() - self.slnStartTime)
		self.logDataRow.append(timeDelta)
		self.logDataTable.append(self.logDataRow)

	def Log(self, message):
		print message
		message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
		OsOperations.Append(self.fileName, message)

	def PrintMsg(self, message):
		if '>----' in message:
			print message
		elif '=====' in message:
			print message
			nums = self.GetBuildStatus(message)
			if nums:
				self.logDataRow += nums

	def GetBuildStatus(self, message):
		searchPattern = r'Build: (\d*) succeeded, (\d*) failed, (\d*) up-to-date, (\d*) skipped'
		m = re.search(searchPattern, message, re.IGNORECASE)
		if m:
			return [(int(m.group(i))) for i in range(1, 5)]

	@classmethod
	def TimeDeltaToStr(self, delta):
		s = delta.seconds
		t = '{:02}:{:02}:{:02}'.format(s // 3600, s % 3600 // 60, s % 60)
		return t

class OsOperations:
	@classmethod
	def Cls(self):
		os.system('cls')

	@classmethod
	def CopyFile(self, Src, Des):
		par = 'COPY /Y "' + Src + '" "' + Des + '"'
		print 'par : ' + par
		os.system(par)

	@classmethod
	def CopyDir(self, Src, Des):
		par = 'XCOPY /S /Y "' + Src + '" "' + Des + '"'
		print 'par : ' + par
		os.system(par)

	@classmethod
	def Pause(self, condition = True):
		if condition:
			raw_input('Press ENTER key to continue . . .')

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
		if not callPrint:
			print params
			subprocess.Popen(params)
			return
		process = subprocess.Popen(params, stdout=subprocess.PIPE)
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
				outLine = output.strip()
				callPrint(output.strip())
		process.poll()

	@classmethod
	def Call(self, params):
		print params
		subprocess.call(params)

	@classmethod
	def Append(self, fileName, message):
		with open(fileName, 'a') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def ContainsInArray(self, str, strArray):
		for inx, item in enumerate(strArray):
			if str in item:
				return inx
		return -1

	@classmethod
	def DeleteAllInTree(self, dirName, fileName):
		for root, dirs, files in os.walk(dirName):
			if fileName in files:
				os.remove('{}/{}'.format(root, fileName))

class PrettyTable:
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
		self.chVerLef = self.chVerMid = self.chVerRig = u'│'
		self.chHorLef = self.chHorMid = self.chHorRig = u'─'
		return self

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
		return self

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
		self.chVerLef = self.chVerMid = self.chVerRig = u'║'
		self.chHorLef = self.chHorMid = self.chHorRig = u'═'
		return self

	def SetNoBorder(self, seperator):
		self.chTopLef = ''
		self.chTopMid = ''
		self.chTopRig = ''
		self.chMidLef = ''
		self.chMidMid = ''
		self.chMidRig = ''
		self.chBotLef = ''
		self.chBotMid = ''
		self.chBotRig = ''
		self.chVerLef = ''
		self.chVerMid = seperator
		self.chVerRig = ''
		self.chHorLef = ''
		self.chHorMid = ''
		self.chHorRig = ''
		return self

	def PrintTable(self, data):
		print self.ToString(data),

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
		outMessage = self.PrintLine(colWidths, self.chTopLef, self.chTopMid, self.chTopRig, self.chHorLef)
		for line in data:
			if len(line) == 0:
				outMessage += self.PrintLine(colWidths, self.chVerLef, self.chVerMid, self.chVerRig, ' ')
			elif len(line) == 1 and line[0] == '-':
				outMessage += self.PrintLine(colWidths, self.chMidLef, self.chMidMid, self.chMidRig, self.chHorMid)
			else:
				outMessage += self.chVerLef
				for inx,colWidth in enumerate(colWidths):
					cell = line[inx] if len(line) > inx else ''
					alignMode = ('<', '^')[isinstance(cell, int) and not isinstance(cell, bool)]
					if isinstance(cell, list) and len(cell) > 0:
						cell = cell[0]
					outMessage += self.GetAligned(str(cell), colWidths[inx], alignMode)
					outMessage += (self.chVerMid, self.chVerRig)[inx == colCnt - 1]
				outMessage += '\n'
		outMessage += self.PrintLine(colWidths, self.chBotLef, self.chBotMid, self.chBotRig, self.chHorRig)
		return outMessage

	def GetAligned(self, message, width, mode):
		return '{{:{}{}}}'.format(mode, width).format(message)

	def PrintLine(self, colWidths, left, mid, right, fill):
		colCnt = len(colWidths)
		getCell = lambda : fill * colWidth + (mid, right)[colCnt - 1 == inx]
		line = left + ''.join([getCell() for inx,colWidth in enumerate(colWidths)])
		return (line + '\n', '')[line == '']

	def PrintTableNoFormat(self, data):
		for line in data:
			print ''.join(line)

	@classmethod
	def PrintArray(self, arr, colCnt):
		for inx, item in enumerate(arr):
			if inx % colCnt == 0:
				print
			print item,

class GitHelper:
	@classmethod
	def GetBranch(self, source):
		params = ['git', '-C', source, 'branch']
		output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
		isCurrent = False
		for part in output.split():
			if isCurrent:
				return part
			if part == '*':
				isCurrent = True

	@classmethod
	def Clean(self, source, options):
		OsOperations.Popen(['git', '-C', source, 'clean', options])

	@classmethod
	def ResetHard(self, source):
		OsOperations.Popen(['git', '-C', source, 'reset', '--hard'])

	@classmethod
	def SubmoduleUpdate(self, source):
		gitSubModule = ['git', '-C', source, 'submodule']
		OsOperations.Call(gitSubModule + ['update', '--init', '--recursive'])
		OsOperations.Call(gitSubModule + ['foreach', 'git', 'reset', '--hard'])

	@classmethod
	def OpenGitGui(self, source):
		param = [ 'git-gui', '--working-dir', source ]
		print 'Staring Git GUI'
		subprocess.Popen(param)
		OsOperations.Pause()

	@classmethod
	def OpenGitBash(self, args):
		print 'Staring Git Bash'
		par = 'start {}sh.exe --cd={}'.format(*args)
		os.system(par)
		OsOperations.Pause()

class StdOutRedirect(object):
	def __init__(self):
		self.messages = ''
		self.orig_stdout = sys.stdout

	def write(self, message):
		self.messages += message

	def ResetOriginal(self):
		sys.stdout = self.orig_stdout
		return self.messages

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

class Model:
	def __init__(self):
		self.fileName = os.path.dirname(os.path.abspath(__file__)) + '\\KlaRunner.ini'

		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []
		self.Config = ''
		self.Platform = ''

	def ReadConfigFile(self):
		with open(self.fileName) as f:
			_model = json.load(f)

		self.Sources = [self.DecodeSource(item) for item in _model['Sources']]
		self.SrcIndex = _model['SrcIndex']
		self.ActiveSrcs = _model['ActiveSrcs']
		self.Tests = _model['Tests']
		self.TestIndex = _model['TestIndex']
		self.VisualStudioBuild = _model['VisualStudioBuild']
		self.VisualStudioRun = _model['VisualStudioRun']
		self.GitBin = _model['GitBin']
		self.VMwareWS = _model['VMwareWS']
		self.MMiConfigPath = _model['MMiConfigPath']
		self.MMiSetupsPath = _model['MMiSetupsPath']
		self.DebugVision = _model['DebugVision']
		self.CopyMmi = _model['CopyMmi']
		self.LogFileName = _model['LogFileName']
		self.MenuColCnt = _model['MenuColCnt']
		self.ClearHistory = _model['ClearHistory']

		self.UpdateSource(self.SrcIndex, False)
		self.UpdateTest(self.TestIndex, False)

	def WriteConfigFile(self):
		_model = OrderedDict()
		_model['Sources'] = [self.EncodeSource(item) for item in self.Sources]
		_model['SrcIndex'] = self.SrcIndex
		_model['ActiveSrcs'] = self.ActiveSrcs
		_model['Tests'] = self.Tests
		_model['TestIndex'] = self.TestIndex
		_model['VisualStudioBuild'] = self.VisualStudioBuild
		_model['VisualStudioRun'] = self.VisualStudioRun
		_model['GitBin'] = self.GitBin
		_model['VMwareWS'] = self.VMwareWS
		_model['MMiConfigPath'] = self.MMiConfigPath
		_model['MMiSetupsPath'] = self.MMiSetupsPath
		_model['DebugVision'] = self.DebugVision
		_model['CopyMmi'] = self.CopyMmi
		_model['LogFileName'] = self.LogFileName
		_model['MenuColCnt'] = self.MenuColCnt
		_model['ClearHistory'] = self.ClearHistory

		with open(self.fileName, 'w') as f:
			json.dump(_model, f, indent=3)

	def DecodeSource(self, srcArr):
		source = srcArr[0]
		config = ('Debug', 'Release')[srcArr[1][0] == 'R']
		platform = ('Win32', 'x64')[srcArr[1][1:] == '64']
		return (source, config, platform)

	def EncodeSource(self, srcSet):
		return [srcSet[0], srcSet[1][0] + srcSet[2][-2:]]

	def UpdateSource(self, index, writeToFile):
		if index < 0 or index >= len(self.Sources):
			return
		self.SrcIndex = index
		self.Source, self.Config, self.Platform = self.Sources[self.SrcIndex]
		self.Branch = GitHelper.GetBranch(self.Source)
		if writeToFile:
			self.WriteConfigFile()

	def UpdateTest(self, index, writeToFile):
		if index < 0 or index >= len(self.Tests):
			return
		self.TestIndex = index
		testAndSlots = self.Tests[self.TestIndex].split()
		self.TestName = testAndSlots[0]
		self.slots = map(int, testAndSlots[1].split('_'))
		if writeToFile:
			self.WriteConfigFile()

	def GetSources(self, srcIndices = None):
		if None == srcIndices:
			return list(self.Sources)
		sources = []
		for index in srcIndices:
			if index < 0 or index >= len(self.Sources):
				print 'Wrong index has been given !!!'
				return []
			sources.append(self.Sources[index])
		return sources

if (__name__ == '__main__'):
	KlaRunner().Start()
