# coding=utf-8
from collections import OrderedDict
import ctypes
from datetime import datetime, timedelta
from functools import partial
import time
import inspect
import itertools
import json
import threading
import os
import re
import subprocess
import sys
import shutil
import threading
import Tkinter as tk
import ttk

class UIFactory:
	@classmethod
	def AddButton(cls, parent, text, r, c, cmd, arg, width = 0):
		if arg is None:
			action = cmd
		else:
			action = lambda: cmd(arg)
		but = tk.Button(parent, text = text, command=action)
		if width > 0:
			but['width'] = width
		but.grid(row=r, column=c, padx=5, pady=5)
		but.config(activebackground='red')
		return but

	@classmethod
	def AddLabel(cls, parent, text, r, c):
		labelVar = tk.StringVar()
		labelVar.set(text)
		label = tk.Label(parent, textvariable=labelVar)
		label.grid(row=r, column=c, sticky='w')
		return (label, labelVar)

	@classmethod
	def AddCombo(cls, parent, values, inx, r, c, cmd, width = 0):
		var = tk.StringVar()
		combo = ttk.Combobox(parent, textvariable=var)
		combo['state'] = 'readonly'
		combo['values'] = values
		if width > 0:
			combo['width'] = width
		combo.current(inx)
		combo.grid(row=r, column=c)
		combo.bind("<<ComboboxSelected>>", cmd)
		return (combo,var)

	@classmethod
	def AddCheckBox(cls, parent, defVal, r, c, cmd, arg = None):
		chkValue = tk.BooleanVar()
		chkValue.set(defVal)
		if arg is None:
			action = cmd
		else:
			action = lambda: cmd(arg)
		chkBox = tk.Checkbutton(parent, var=chkValue, command=action)
		chkBox.grid(row=r, column=c, sticky='w')
		return chkValue

	@classmethod
	def AddFrame(cls, parent, r, c, px = 0, py = 0, columnspan=1):
		frame = ttk.Frame(parent)
		frame.grid(row=r, column=c, sticky='w', padx=px, pady=py, columnspan=columnspan)
		return frame

class UI:
	def __init__(self):
		self.klaRunner = KlaRunner()
		self.model = self.klaRunner.model
		OsOperations.RunFromUI = True

	def Run(self):
		if not ctypes.windll.shell32.IsUserAnAdmin():
			print 'Please run this application with Administrator privilates'
			os.system('PAUSE')
			return
		self.window = tk.Tk()
		self.window.title('KLA Application Runner')
		iconPath = self.model.StartPath + r'\Plus.ico'
		if os.path.exists(iconPath):
			self.window.iconbitmap(iconPath)
		#self.window.geometry('750x350')
		#self.window.resizable(0, 0) # To Disable Max button, Then half screen won't work
		#self.window.overrideredirect(1) # Remove Window border
		self.window.protocol("WM_DELETE_WINDOW", self.OnCloseWindow)
		UIHeader(self.window, 0, 0, self.model)
		UIMainMenu(self.window, 1, 0, self.klaRunner)
		self.window.mainloop()

	def OnCloseWindow(self):
		self.model.WriteConfigFile()
		self.window.destroy()

class UIHeader:
	def __init__(self, parent, r, c, model):
		self.model = model
		frame = UIFactory.AddFrame(parent, r, c, 20, 0)
		self.CreateUI(frame)

	def CreateUI(self, parent):
		UIFactory.AddLabel(parent, ' ', 0, 2)
		UIFactory.AddLabel(parent, ' ', 0, 5)

		r = 1
		self.AddSource(parent, r, 0)
		self.AddConfig(parent, r, 3)
		self.AddAttachMmi(parent, r, 6)

		r = 2
		self.AddBranch(parent, r, 0)
		self.AddPlatform(parent, r, 3)
		self.AddCopyMmi(parent, r, 6)

		r = 3
		self.AddTest(parent, r, 0)
		self.AddActiveSrcs(parent, r, 3)

		self.AddSlots(parent, 4, 0)

	def AddSource(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Source', r, c)
		srcs = [src[0] for src in self.model.Sources]
		self.cmbSource = UIFactory.AddCombo(parent, srcs, self.model.SrcIndex, r, c+1, self.OnSrcChanged, 70)

	def OnSrcChanged(self, event):
		if self.model.UpdateSource(self.cmbSource[0].current(), False):
			self.lblBranch[1].set(self.model.Branch)
			self.cmbConfig[1].set(self.model.Config)
			self.cmbPltfm[1].set(self.model.Platform)
			print 'Source Changed to : ' + self.model.Source

	def AddConfig(self, parent, r, c):
		configInx = ConfigEncoder.Configs.index(self.model.Config)
		UIFactory.AddLabel(parent, 'Config', r, c)
		self.cmbConfig = UIFactory.AddCombo(parent, ConfigEncoder.Configs, configInx, r, c+1, self.OnConfigChanged, 10)

	def OnConfigChanged(self, event):
		if self.model.UpdateConfig(self.cmbConfig[0].current()):
			print 'Config Changed to : ' + self.model.Config

	def AddBranch(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Branch', r, c)
		self.lblBranch = UIFactory.AddLabel(parent, self.model.Branch, r, c+1)

	def AddPlatform(self, parent, r, c):
		platformInx = ConfigEncoder.Platforms.index(self.model.Platform)
		UIFactory.AddLabel(parent, 'Platform', r, c)
		self.cmbPltfm = UIFactory.AddCombo(parent, ConfigEncoder.Platforms, platformInx, r, c+1, self.OnPlatformChanged, 10)

	def OnPlatformChanged(self, event):
		if self.model.UpdatePlatform(self.cmbPltfm[0].current()):
			print 'Platform Changed to : ' + self.model.Platform

	def AddTest(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Test', r, c)
		testNames = [TestNameEncoer.Encode(item)[0] for item in self.model.Tests]
		self.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, r, c+1, self.OnTestChanged, 70)

	def OnTestChanged(self, event):
		if self.model.UpdateTest(self.cmbTest[0].current(), False):
			print 'Test Changed to : ' + self.model.TestName
			for i in range(self.model.MaxSlots):
				self.chkSlots[i].set((i+1) in self.model.slots)

	def AddAttachMmi(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Attach MMi', r, c)
		self.chkAttachMmi = UIFactory.AddCheckBox(parent, self.model.DebugVision, r, c+1, self.OnAttach)

	def OnAttach(self):
		self.model.DebugVision = self.chkAttachMmi.get()
		print 'Attach to MMi : ' + ('Yes' if self.model.DebugVision else 'No')

	def AddCopyMmi(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Copy MMI to Icos', r, c)
		self.chkCopyMmi = UIFactory.AddCheckBox(parent, self.model.CopyMmi, r, c+1, self.OnCopyMmi)

	def OnCopyMmi(self):
		self.model.CopyMmi = self.chkCopyMmi.get()
		print 'Copy MMI to ICOS : ' + str(self.chkCopyMmi.get())

	def AddSlots(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Slots', r, c)
		frame = UIFactory.AddFrame(parent, r, c+1, columnspan=5)
		self.chkSlots = []
		for i in range(self.model.MaxSlots):
			isSelected = (i+1) in self.model.slots
			UIFactory.AddLabel(frame, str(i+1), 0, i * 2)
			self.chkSlots.append(UIFactory.AddCheckBox(frame, isSelected, 0, i * 2 + 1, self.OnSlotChn, i))

	def OnSlotChn(self, index):
		self.model.UpdateSlots(index, self.chkSlots[index].get())
		print 'Selected slots for the current test : ' + str(self.model.slots)

	def AddActiveSrcs(self, parent, r, c):
		UIFactory.AddLabel(parent, 'Sources', r, c)
		frame = UIFactory.AddFrame(parent, r, c+1, columnspan=4)
		self.chkActiveSrcs = []
		srcs = self.model.ActiveSrcs
		for i in range(len(self.model.Sources)):
			isSelected = True if i in srcs else False
			UIFactory.AddLabel(frame, str(i+1), 0, i * 2)
			self.chkActiveSrcs.append(UIFactory.AddCheckBox(frame, isSelected, 0, i * 2 + 1, self.OnActiveSrcsChn, i))

	def OnActiveSrcsChn(self, index):
		if self.chkActiveSrcs[index].get():
			self.model.ActiveSrcs.append(index)
			self.model.ActiveSrcs = list(set(self.model.ActiveSrcs))
			print 'Enabled the source : ' + str(self.model.Sources[index][0])
		else:
			self.model.ActiveSrcs.remove(index)
			print 'Disabled the source : ' + str(self.model.Sources[index][0])

class UIMainMenu:
	def __init__(self, parent, r, c, klaRunner):
		self.model = klaRunner.model
		self.frame = UIFactory.AddFrame(parent, r, c, 20, 20)
		self.klaRunner = klaRunner
		self.testRunner = AutoTestRunner(self.model)
		self.settings = Settings(self.model, self.klaRunner)
		self.appRunner = AppRunner(self.model, self.testRunner)
		self.klaSourceBuilder = KlaSourceBuilder(self.model, self.klaRunner)
		self.CreateUI(self.frame)
		self.thread1 = None

	def CreateUI(self, parent):
		self.AddColumn1(parent, 0)
		self.AddColumn2(parent, 1)
		self.AddColumn3(parent, 2)
		self.AddColumn4(parent, 3)
		self.AddColumn5(parent, 4)

	def AddColumn1(self, parent, c):
		actionData = [
			['Open Python', self.klaRunner.OpenPython],
			['Run test', self.RunAutoTest, False],
			['Start test', self.RunAutoTest, True],
			['Run Handler and MMi', self.appRunner.RunHandlerMMi],
			['Run Handler alone', self.appRunner.RunHandler],
			['Run MMi from Source', self.appRunner.RunMMi, True],
			['Run MMi from C:Icos', self.appRunner.RunMMi, False],
		]
		self.Col1 = UIActionGroup(parent, 0, c, actionData)

	def RunAutoTest(self, startOnly):
		index = 2 if startOnly else 1
		self.thread1 = self.testRunner.RunAutoTestAsync(startOnly)
		if not startOnly:
			self.SetActiveButton(self.Col1.Buttons[index])

	def SetActiveButton(self, but):
		but.config(background='red')
		self.ActiveButton = but
		threading.Thread(target=self.WaitForThread).start()

	def WaitForThread(self):
		if self.thread1:
			self.thread1.join()
		if self.ActiveButton:
			self.ActiveButton.config(background='SystemButtonFace')

	def AddColumn2(self, parent, c):
		sourceBuilder = self.klaSourceBuilder
		actionData = [
			['Open CIT100', sourceBuilder.OpenSolution, 0],
			['Open Simulator', sourceBuilder.OpenSolution, 1],
			['Open Mmi', sourceBuilder.OpenSolution, 2],
			['Open MockLicense', sourceBuilder.OpenSolution, 3],
			['Open Converters', sourceBuilder.OpenSolution, 4],
		]
		UIActionGroup(parent, 0, c, actionData)

	def AddColumn3(self, parent, c):
		actionData = [
			['Open Test Folder', self.klaRunner.OpenTestFolder],
			['Open Local Diff', self.OpenLocalDif],
			['Open Git GUI', self.OpenGitGui],
			['Open Git Bash', self.OpenGitBash],
		]
		UIActionGroup(parent, 0, c, actionData)

	def AddColumn4(self, parent, c):
		actionData = [
			['Run Slots', self.RunSlots],
			['Run ToolLink Host', self.appRunner.RunToollinkHost],
			['Comment VisionSystem', self.testRunner.ModifyVisionSystem],
			['Copy Mock License', self.testRunner.CopyMockLicense],
			['Copy xPort xml', self.testRunner.CopyIllumRef],
			['Print mmi.h IDs', self.klaRunner.PrintMissingIds],
		]
		UIActionGroup(parent, 0, c, actionData)

	def RunSlots(self):
		VMWareRunner.RunSlots(self.model)

	def AddColumn5(self, parent, c):
		sourceBuilder = self.klaSourceBuilder
		settings = self.settings
		effortLogger = EffortLogger(self.model)
		actionData = [
			['Clean Source', self.CleanSource],
			['Build Source', self.BuildSource],
			#['Add Test', self.AddTest],
			['Clear Screen', self.ClearScreen],
			['Effort Log', effortLogger.ReadEffortLog],
			['Stop All KLA Apps', self.StopTasks],
		]
		UIActionGroup(parent, 0, c, actionData)

	def OpenLocalDif(self):
		AppRunner.OpenLocalDif(self.model.Source)

	def OpenGitGui(self):
		Git.OpenGitGui(self.model.Source)

	def OpenGitBash(self):
		Git.OpenGitBash((self.model.GitBin, self.model.Source))

	def ClearScreen(self):
		OsOperations.Cls()

	def StopTasks(self):
		AppRunner.StopTasks(True)
		if self.thread1 is not None:
			self.thread1._Thread__stop()

	def BuildSource(self):
		self.klaSourceBuilder.BuildSource()

	def CleanSource(self):
		self.klaSourceBuilder.CleanSource()

	def AddTest(self):
		print 'Not implemented in UI. Its available only in console.'

class UIActionGroup:
	def __init__(self, parent, r, c, actionData):
		self.Buttons = []
		self.actionData = actionData
		self.frame = ttk.Frame(parent)
		self.frame.grid(row=r, column=c, sticky='n')
		self.CreateUI(self.frame)

	def CreateUI(self, parent):
		for inx,item in enumerate(self.actionData):
			arg = item[2] if len(item) > 2 else None
			but = UIFactory.AddButton(parent, item[0], inx, 0, item[1], arg, 19)
			self.Buttons.append(but)

class Menu:
	def __init__(self, klaRunner, model):
		self.klaRunner = klaRunner
		self.testRunner = AutoTestRunner(model)
		self.settings = Settings(model, klaRunner)
		self.appRunner = AppRunner(model, self.testRunner)
		self.klaSourceBuilder = KlaSourceBuilder(model, klaRunner)

	def PrepareMainMenu(self):
		model = self.klaRunner.model
		seperator = ' : '
		menuData = [
			['Source', seperator, model.Source, ' '*5, 'Config', seperator, model.Config],
			['Branch', seperator, model.Branch, ' '*5, 'Platform', seperator, model.Platform],
			['Test', seperator, model.TestName, ' '*5, 'Copy MMI to Icos', seperator, model.CopyMmi]
		]
		PrettyTable(TableFormatFactory().SetNoBorder('')).PrintTable(menuData)

		testRunner = self.testRunner
		sourceBuilder = self.klaSourceBuilder
		settings = self.settings
		effortLogger = EffortLogger(model)
		autoTest = ('', ' (attach MMi)')[model.DebugVision]
		activeSrcs = str([i + 1 for i in model.ActiveSrcs]).replace(' ', '') if len(model.ActiveSrcs) > 0 else ''
		group = [
		[
			[1, ['Open Python', self.klaRunner.OpenPython]],
			[2, ['Run test' + autoTest, testRunner.RunAutoTestAsync, False]],
			[3, ['Start test' + autoTest, testRunner.RunAutoTestAsync, True]],
			[4, ['Run Handler and MMi', self.appRunner.RunHandlerMMi]],
			[5, ['Run Handler alone', self.appRunner.RunHandler]],
			[6, ['Run MMi from Source', self.appRunner.RunMMi, True]],
			[7, ['Run MMi from C:Icos', self.appRunner.RunMMi, False]],
			[9, ['Run ToolLink Host', self.appRunner.RunToollinkHost]],
			[8, ['Effort Log', effortLogger.ReadEffortLog]],
		],[
			[10, ['Open CIT100', sourceBuilder.OpenSolution, 0]],
			[11, ['Open Simulator', sourceBuilder.OpenSolution, 1]],
			[12, ['Open Mmi', sourceBuilder.OpenSolution, 2]],
			[14, ['Open MockLicense', sourceBuilder.OpenSolution, 3]],
			[15, ['Open Converters', sourceBuilder.OpenSolution, 4]],
		],[
			[20, ['Open Test Folder', self.klaRunner.OpenTestFolder]],
			[21, ['Open Local Diff', AppRunner.OpenLocalDif, model.Source]],
			[22, ['Open Git GUI', Git.OpenGitGui, model.Source]],
			[23, ['Open Git Bash', Git.OpenGitBash, (model.GitBin, model.Source)]],
			[24, ['Comment VisionSystem', testRunner.ModifyVisionSystem]],
			[25, ['Copy Mock License', testRunner.CopyMockLicense]],
			[26, ['Copy xPort xml', testRunner.CopyIllumRef, model.ClearHistory]],
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
		PrettyTable(TableFormatFactory().SetDoubleLineBorder()).PrintTable(menuData)
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
		self.SetWorkingDir()

	def Run(self):
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
		OsOperations.System(par, 'Starting my.py')

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
			branch = Git.GetBranch(src[0])
			if src[0] == self.model.Source:
				self.model.Branch = branch
			menuData.append([src[0], branch, src[1], src[2]])
		return (heading, menuData)

	def PrintBranches(self, activeSrcs = None):
		heading, data = self.GetSourceInfo(activeSrcs)
		menuData = [ heading, ['-'] ] + data
		PrettyTable(TableFormatFactory().SetSingleLine()).PrintTable(menuData)
		return data

	def SetWorkingDir(self):
		wd = os.path.join(self.model.StartPath, self.model.TempDir)
		if not os.path.isdir(wd):
			os.mkdir(wd)
		os.chdir(wd)

class AppRunner:
	def __init__(self, model, testRunner):
		self.model = model
		self.testRunner = testRunner

	@classmethod
	def GetPlatform(self, platform, isSimulator = False):
		if isSimulator and 'Win32' == platform:
			platform = 'x86'
		return platform

	def RunHandler(self, doPause = True):
		self.StopTasks(False)

		config = self.model.Config
		platform = self.GetPlatform(self.model.Platform)
		handlerPath = '{}/handler/cpp/bin/{}/{}/system'.format(self.model.Source, platform, config)
		consoleExe = handlerPath + '/console.exe'
		testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'

		platform = self.GetPlatform(self.model.Platform, True)
		simulatorExe = '{}/handler/Simulator/ApplicationFiles/bin/{}/{}/CIT100Simulator.exe'
		simulatorExe = simulatorExe.format(self.model.Source, platform, config)

		for file in [consoleExe, testTempDir, simulatorExe]:
			if not os.path.exists(file):
				print 'File not found : ' + file
				OsOperations.Pause()
				return

		OsOperations.System('start ' + consoleExe + ' ' + testTempDir)
		OsOperations.System('start {} {} {}'.format(simulatorExe, testTempDir, handlerPath))
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def RunMMi(self, fromSrc, doPause = True):
		# Set correct path to C:\Windows\mmi_han.ini

		self.StopTask('MMi.exe')
		VMWareRunner.RunSlots(self.model)

		if fromSrc:
			self.testRunner.CopyMockLicense(False, False) # Do we need this
		mmiPath = self.testRunner.CopyMockLicense(fromSrc, False)
		self.testRunner.CopyIllumRef()

		OsOperations.Timeout(8)

		mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')
		if not os.path.exists(mmiExe):
			print 'File not found : ' + mmiExe
			OsOperations.Pause()
			return

		OsOperations.System('start ' + mmiExe)
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def RunHandlerMMi(self):
		self.RunHandler(False)
		self.RunMMi(True, False)
		OsOperations.Pause(self.model.ClearHistory)

	def RunToollinkHost(self):
		sys.path.append('C:\Handler\\testing')
		import handlerprocesses
		import secshost
		from generated.handlerSystem import ActionIds

		fabLinkPath = self.model.Source + '\handler\FabLink'
		processes = handlerprocesses.HandlerProcesses('', '', '', fabLinkPath)
		processes.secshost.start()
		OsOperations.Timeout(10)

		#visionApplications = ['BBI/Surface1: OFF', 'TopPVI/Mark: ON', 'TopPVI/Surface1: ON', 'TopPVI/Surface2: OFF']
		#visionApplications = ['Top Spectrum Plus/Mark: OFF', 'Top Spectrum Plus/Data Matrix: ON','Top Spectrum Plus/Alignment based Combined Surf:ON','Top Spectrum Plus/Alignment based Surface*:OFF','Bottom Spectrum Plus/Mark:OFF','Top Spectrum Plus/Pin 1:OFF','Top Spectrum Plus/Empty Pocket:OFF']
		#visionApplications = ['BGA: ON']
		visionApplications = ["LeadLess/*: ON"]
		#visionApplications= ['SMI/Pin*: ON']
		#ppidList=['/component/test', '/handler/test']
		ppSelectParams = {
			'PPID' : 'test',
			#'PASS-DESTINATION': 'TAPE',
			'VISION-APPLICATIONS' : visionApplications,
			#'PPID-LIST' : ppidList,
		}
		processes.secshost.proxy.runHostCommandSend(remoteCommand=ActionIds.PP_SELECT, commandParameters=ppSelectParams, waitForAnswer=True, enhanced=True)

	@classmethod
	def StopTasks(self, doPause):
		for exeName in [
			'Mmi.exe',
			'Mmi_spc.exe',
			'console.exe',
			'CIT100Simulator.exe',
			'HostCamServer.exe',
			'Ves.exe',
		]:
			AppRunner.StopTask(exeName)
		AppRunner.StopTask('python.exe', os.getpid())
		OsOperations.Pause(doPause)

	@classmethod
	def StopTask(self, exeName, exceptProcId = -1):
		processIds = OsOperations.GetProcessIds(exeName)
		if exceptProcId > 0:
			processIds.remove(exceptProcId)
		if len(processIds) == 0:
			return
		print '{} Process IDs : {}'.format(exeName, processIds)
		if exceptProcId < 0:
			OsOperations.Popen([ 'TASKKILL', '/IM', exeName, '/T', '/F' ])
		else:
			for proId in processIds:
				OsOperations.Popen([ 'TASKKILL', '/PID', str(proId), '/T', '/F' ])

	@classmethod
	def OpenLocalDif(self, source):
		par = [ 'TortoiseGitProc.exe', '/command:diff', '/path:' + source + '' ]
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)
		OsOperations.Pause()

class VMWareRunner:
	@classmethod
	def RunSlots(self, model):
		vMwareWS = model.VMwareWS
		slots = model.slots
		vmRunExe = vMwareWS + "vmrun.exe"
		vmWareExe = vMwareWS + "vmware.exe"
		vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'
		par = [vmRunExe, '-vp', '1', 'list']
		output = subprocess.Popen(par, stdout=subprocess.PIPE).communicate()[0]
		runningSlots = []
		searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
		for line in output.split():
			m = re.search(searchPattern, line, re.IGNORECASE)
			if m:
				runningSlots.append(int(m.group(1)))

		for slot in slots:
			vmxPath = vmxGenericPath.format(slot)
			if slot in runningSlots:
				print 'VMware Slot ' + str(slot) + ' : Restarted.'
				subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
			else:
				subprocess.Popen([vmWareExe, vmxPath])
				print 'Start VMware Slot ' + str(slot)
				os.system('PAUSE')
				print 'VMware Slot ' + str(slot) + ' : Started.'

class AutoTestRunner:
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
		FileOperations.Copy(licenseFile, mmiPath)
		OsOperations.Pause(doPause and self.model.ClearHistory)
		return mmiPath

	def CopyIllumRef(self, doPause = False, delay = False):
		src = self.model.StartPath + '\\xPort_IllumReference.xml'
		des = 'C:/icos/xPort/'
		if delay:
			FileOperations.Copy(src, des, 8, 3)
		else:
			FileOperations.Copy(src, des)
		OsOperations.Pause(doPause)

	def ModifyVisionSystem(self, doPause = True):
		line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
		oldLine = ' ' + line
		newLine = ' #' + line
		fileName = os.path.abspath(self.model.Source + '/libs/testing/visionsystem.py')
		with open(fileName) as f:
			oldText = f.read()
		if oldLine in oldText:
			newText = oldText.replace(oldLine, newLine)
			with open(fileName, "w") as f:
				f.write(newText)
			print fileName + ' has been modified.'
		else:
			print fileName + ' had already been modified.'
		OsOperations.Pause(doPause and self.model.ClearHistory)

	def RunAutoTestAsync(self, startUp):
		AppRunner.StopTasks(False)
		VMWareRunner.RunSlots(self.model)
		self.ModifyVisionSystem(False)
		self.CopyIllumRef(False, True)
		#FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
		os.chdir(self.model.StartPath)
		t1 = threading.Thread(target=self.Run, args=(startUp,))
		t1.start()
		return t1

	def Run(self, startUp):
		libsPath = AutoTestRunner.UpdateLibsTestingPath(self.model.Source)
		tests = AutoTestRunner.SearchInTests(libsPath, self.model.TestName)
		if len(tests) == 0:
			return
		import my
		print 'Module location of my : ' + my.__file__
		my.c.startup = startUp
		my.c.debugvision = self.model.DebugVision
		my.c.copymmi = self.model.CopyMmi
		my.c.mmiBuildConfiguration = self.model.GetBuildConfig()
		my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
		my.c.platform = self.model.Platform
		my.c.mmiConfigurationsPath = self.model.MMiConfigPath
		my.c.mmiSetupsPath = self.model.MMiSetupsPath
		my.run(tests[0][0])
		print 'Completed Auto Test : ' + tests[0][1]

	@classmethod
	def SearchInTests(cls, libsPath, text):
		# Remove the already loaded my module if source changed
		if 'my' in sys.modules:
			expectedPath = libsPath + '\\my.py'
			if expectedPath != sys.modules['my'].__file__:
				del sys.modules['my']
		sys.stdout = stdOutRedirect = StdOutRedirect()
		import my
		lineBreak = 'KLARunnerLineBreak'
		print lineBreak
		my.h.l(text)
		msgs = stdOutRedirect.ResetOriginal()
		inx = msgs.index(lineBreak)
		tests = []
		for msg in msgs[inx+1:]:
			arr = msg.split(':')
			if len(arr) == 2:
				tests.append([int(arr[0].strip()), arr[1].strip()])
		return tests

	@classmethod
	def GetTestName(cls, source, number):
		libsPath = cls.UpdateLibsTestingPath(source)
		tests = cls.SearchInTests(libsPath, number)
		if len(tests) > 0:
			return tests[0][1]
		return ''

	@classmethod
	def UpdateLibsTestingPath(cls, source):
		libsTesting = '/libs/testing'
		newPath = os.path.abspath(source + libsTesting)
		index = ArrayOrganizer.ContainsInArray(newPath, sys.path)
		if index >= 0:
			return newPath
		paths = [p.replace('\\', '/') for p in sys.path]
		index = ArrayOrganizer.ContainsInArray(libsTesting, paths)
		if index >= 0:
			print 'Old path ({}) has been replaced with new path ({}) in sys.path.'.format(sys.path[index], newPath)
			sys.path[index] = newPath
		else:
			print 'New path ({}) has been added in sys.path.'.format(newPath)
			sys.path.append(newPath)
		return newPath
		OsOperations.Pause(self.model.ClearHistory)

class Settings:
	def __init__(self, model, klaRunner):
		self.model = model
		self.klaRunner = klaRunner

	def ChangeTest(self):
		index = self.SelectOption1('Test Name', self.model.Tests, self.model.TestIndex)
		self.model.UpdateTest(index, True)
		OsOperations.Pause(self.model.ClearHistory)

	def AddTest(self):
		number = OsOperations.InputNumber('Type the number of test then press ENTER: ')
		testName = AutoTestRunner.GetTestName(self.model.Source, number)
		if testName == '':
			print 'There is no test exists for the number : ' + str(number)
			return
		if ArrayOrganizer.ContainsInArray(testName, self.model.Tests) >= 0:
			print 'The given test ({}) already exists'.format(testName)
			return
		slots = raw_input('Enter slots : ')
		testNameAndSlot = '{} {}'.format(testName, slots)
		self.model.Tests.append(testNameAndSlot)
		self.model.UpdateTest(len(self.model.Tests) - 1, True)
		OsOperations.Pause(self.model.ClearHistory)

	def ChangeSource(self):
		heading, data = self.klaRunner.GetSourceInfo(None)
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
		PrettyTable(TableFormatFactory().SetSingleLine()).PrintTable(data)
		number = OsOperations.InputNumber('Type the number then press ENTER: ')
		if number > 0 and number <= len(arrOfArr):
			return number - 1
		else:
			print 'Wrong input is given !!!'
		return -1

class KlaSourceBuilder:
	def __init__(self, model, klaRunner):
		self.model = model
		self.klaRunner = klaRunner
		self.Solutions = [
			'/handler/cpp/CIT100.sln',
			'/handler/Simulator/CIT100Simulator/CIT100Simulator.sln',
			'/mmi/mmi/Mmi.sln',
			'/mmi/mmi/MockLicense.sln',
			'/mmi/mmi/Converters.sln'
		]
		self.SlnNames = ['CIT100', 'Simulator', 'MMi', 'Mock', 'Converters']

	def VerifySources(self, message):
		isAre = (' is', 's are')[len(self.model.ActiveSrcs) > 1]
		print 'The following source{} ready for {}.'.format(isAre, message)
		sources = self.klaRunner.PrintBranches(self.model.ActiveSrcs)
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
			FileOperations.DeleteAllInTree(src, gitIgnore)
			with open(src + '/' + gitIgnore, 'w') as f:
				f.writelines(str.join('\n', excludeDirs))
			Git.Clean(src, '-fd')
			print 'Reseting files in ' + src
			Git.ResetHard(src)
			print 'Submodule Update'
			Git.SubmoduleUpdate(src)
			print 'Cleaning completed for ' + src
		OsOperations.Pause(self.model.ClearHistory)

	def BuildSource(self):
		logFileName = self.model.StartPath + '/' + self.model.LogFileName
		buildLoger = BuildLoger(logFileName)
		for source, branch, config, srcPlatform in self.VerifySources('building'):
			buildLoger.StartSource(source, branch)
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

	def StartSource(self, src, branch):
		self.srcStartTime = datetime.now()
		self.Log('Source : ' + src)
		self.Log('Branch : ' + branch)
		self.logDataTable = [
			[ 'Solution', 'Config', 'Platform', 'Succeeded', 'Failed', 'Up To Date', 'Skipped', 'Time Taken' ],
			['-']
		]

	def EndSource(self, src):
		timeDelta = self.TimeDeltaToStr(datetime.now() - self.srcStartTime)
		self.Log('Completed building : {} in {}'.format(src, timeDelta))
		table = PrettyTable(TableFormatFactory().SetSingleLine()).ToString(self.logDataTable)
		print table
		FileOperations.Append(self.fileName, table)

	def StartSolution(self, slnFile, name, config, platform):
		self.Log('Start building : ' + slnFile)
		self.slnStartTime = datetime.now()
		self.logDataRow = [name, config, platform]

	def EndSolution(self):
		if len(self.logDataRow) == 3:
			self.logDataRow += [''] * 4
		timeDelta = self.TimeDeltaToStr(datetime.now() - self.slnStartTime)
		self.logDataRow.append(timeDelta)
		self.logDataTable.append(self.logDataRow)

	def Log(self, message):
		print message
		message = datetime.now().strftime('%Y %b %d %H:%M:%S> ') + message
		FileOperations.Append(self.fileName, message)

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

class FileOperations:
	@classmethod
	def ReadLine(cls, fileName, utf = 'utf-8'):
		f = open(fileName, 'rb')
		data = f.read()
		f.close()
		lines = data.decode(utf).splitlines()
		for line in lines:
			yield line

	@classmethod
	def Append(self, fileName, message):
		with open(fileName, 'a') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def Write(self, fileName, message):
		with open(fileName, 'w') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def DeleteAllInTree(self, dirName, fileName):
		for root, dirs, files in os.walk(dirName):
			if fileName in files:
				os.remove('{}/{}'.format(root, fileName))

	@classmethod
	def Copy(cls, src, des, initWait = 0, inter = 0):
		if initWait == 0 and inter == 0:
			cls._Copy(src, des, inter)
		else:
			print 'Try to Copy({},{}) after {} seconds.'.format(src, des, initWait)
			threading.Timer(initWait, cls._Copy, [src, des, inter]).start()

	@classmethod
	def _Copy(cls, src, des, inter = 0):
		while not os.path.exists(des):
			if inter > 0:
				print '({}) not existing. Try to Copy({}) after {} seconds.'.format(des, src, inter)
				time.sleep(inter)
			else:
				print 'Wrong input - Destination folder not existing : ' + des
				return
		if os.path.isfile(src):
			OsOperations.System('COPY /Y "' + src + '" "' + des + '"')
		elif os.path.isdir(src):
			OsOperations.System('XCOPY /S /Y "' + src + '" "' + des + '"')
		else:
			print 'Wrong input - Neither file nor directory : ' + src

class OsOperations:
	RunFromUI = False

	@classmethod
	def Cls(cls):
		os.system('cls')

	@classmethod
	def System(cls, params, message = None):
		if message is None:
			print 'params : ' + params
		else:
			print message
		os.system(params)

	@classmethod
	def Pause(cls, condition = True):
		if condition and not cls.RunFromUI:
			#raw_input('Press ENTER key to continue . . .')
			os.system('PAUSE')

	@classmethod
	def GetProcessIds(cls, exeName):
		exeName = exeName.lower()
		params = [ 'TASKLIST', '/FI' ]
		params.append('IMAGENAME eq {}'.format(exeName))
		output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
		processIds = []
		for line in output.splitlines():
			parts = line.lower().split()
			if len(parts) > 2 and parts[0] == exeName:
				processIds.append(int(parts[1]))
		return processIds

	@classmethod
	def Timeout(cls, seconds):
		os.system('timeout ' + str(seconds))

	@classmethod
	def InputNumber(cls, message):
		userIn = raw_input(message)
		while True:
			if userIn != '':
				return int(userIn)
			userIn = raw_input()

	@classmethod
	def Popen(cls, params, callPrint = None):
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
	def Call(cls, params):
		print params
		subprocess.call(params)

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

class TableFormatFactory:
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
		outMessage = self.PrintLine(colWidths, self.Format.Top)
		[left, mid, right, fill] = list(self.Format.Ver)
		for line in data:
			if len(line) == 0:
				outMessage += self.PrintLine(colWidths, self.Format.Emt)
			elif len(line) == 1 and line[0] == '-':
				outMessage += self.PrintLine(colWidths, self.Format.Mid)
			else:
				outMessage += left
				for inx,colWidth in enumerate(colWidths):
					cell = line[inx] if len(line) > inx else ''
					alignMode = ('<', '^')[isinstance(cell, int) and not isinstance(cell, bool)]
					if isinstance(cell, list) and len(cell) > 0:
						cell = cell[0]
					outMessage += self.GetAligned(str(cell), colWidths[inx], alignMode)
					outMessage += (mid, right)[inx == colCnt - 1]
				outMessage += '\n'
		outMessage += self.PrintLine(colWidths, self.Format.Bot)
		return outMessage

	def GetAligned(self, message, width, mode):
		return '{{:{}{}}}'.format(mode, width).format(message)

	def PrintLine(self, colWidths, formatRow):
		[left, mid, right, fill] = list(formatRow)
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
		actual = PrettyTable(TableFormatFactory().SetSingleLine()).ToString(data)
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
		actual = PrettyTable(TableFormatFactory().SetDoubleLineBorder()).ToString(data)
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
		actual = PrettyTable(TableFormatFactory().SetDoubleLine()).ToString(data)
		#print actual
		Test.AssertMultiLines(actual, expected)

	def NoBorder(self):
		data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], ['ICOS', 12345, False]]
		expected = u'''
ColA,Col B,Col C
KLA ,  2  ,True 
ICOS,12345,False
'''[1:]
		actual = PrettyTable(TableFormatFactory().SetNoBorder(',')).ToString(data)
		#print actual
		Test.AssertMultiLines(actual, expected)

class Git:
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
		par = 'start {}sh.exe --cd={}'.format(*args)
		OsOperations.System(par, 'Staring Git Bash')
		OsOperations.Pause()

class StdOutRedirect(object):
	def __init__(self):
		self.messages = ''
		self.orig_stdout = sys.stdout
		self.IsReset = False

	def write(self, message):
		if self.IsReset:
			print message, # This is needed only for printing summary
		else:
			self.messages += message

	def ResetOriginal(self):
		sys.stdout = self.orig_stdout
		self.IsReset = True
		return self.messages.splitlines()

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

	@classmethod
	def ContainsInArray(self, str, strArray):
		for inx, item in enumerate(strArray):
			if str in item:
				return inx
		return -1

class NumValDict(dict):
	def Add(self, key, value):
		if key in self:
			self[key] = self[key] + value
		else:
			self[key] = value

class TestNumValDict:
	def __init__(self):
		self.StrInt()

	def StrInt(self):
		d = NumValDict()
		d.Add('hi', 23)
		d.Add('hi', 5)
		d.Add('bye', 3)
		Test.Assert(d, {'bye': 3, 'hi': 28})

class EffortLogger:
	def __init__(self, model):
		self.model = model
		self.LogFileEncode = 'UTF-16'
		self.DTFormat = self.model.DateFormat + ' %H:%M:%S'
		self.ColWidth = 80
		self.MinMinutes = 3
		self.MinTime = timedelta(minutes=self.MinMinutes)

	def ReadEffortLog(self):
		yesterday = datetime.now() - timedelta(days=1)
		self.ReadEffortLogOn(yesterday, 'Yesterday')
		today = datetime.now()
		self.ReadEffortLogOn(today, 'Today')
		OsOperations.Pause()

	def ReadEffortLogOn(self, date, message):
		logFile = self.model.EffortLogFile
		dictAppNameToTime = NumValDict()
		lastDt = None
		totalTime = timedelta()
		for line in FileOperations.ReadLine(logFile, self.LogFileEncode):
			if line[:7] == 'Current':
				continue
			lineParts = self.FormatText(line).split('$')
			if len(lineParts) > 2:
				dt = datetime.strptime(lineParts[0], self.DTFormat)
				if not self.IsSameDate(dt, date):
					continue
				ts = (dt - lastDt) if lastDt is not None else (dt-dt)
				txt = self.PrepareDescription(lineParts[1], lineParts[2])
				dictAppNameToTime.Add(txt, ts)
				lastDt = dt
				totalTime += ts
			else:
				print 'Error: ' + line
		data = []
		oneMinAppsTime = timedelta()
		for k,v in dictAppNameToTime.items():
			if v > self.MinTime:
				data.append([self.Trim(k, self.ColWidth), v])
			else:
				oneMinAppsTime += v
		minAppDesc = 'Other Apps Less Than {} Minute(s)'.format(self.MinMinutes)
		data.append([minAppDesc, oneMinAppsTime])
		data = sorted(data, key = lambda x : x[1], reverse=True)
		menuData = [['Applications On ' + message, 'Time Taken'], ['-']] + data
		menuData += [['-'], ['Total Time', totalTime]]
		table = PrettyTable(TableFormatFactory().SetSingleLine()).ToString(menuData)
		print table
		#table = datetime.now().strftime('%Y %b %d %H:%M:%S\n') + table
		#FileOperations.Append(logFile + '.txt', table)

	def IsSameDate(self, a, b):
		return a.day == b.day and a.month == b.month and a.year == b.year

	def FormatText(self, message):
		return message.encode('ascii', 'ignore').decode('ascii')

	def PrepareDescription(self, message1, message2):
		groupNames = [
			'Google Chrome',
			'Internet Explorer',
			'explorer.exe',
			'OUTLOOK',
		]
		for name in groupNames:
			if name in message1 or name in message2:
				return name
		message = message2 if len(message2) > 50 else message1 + '$' + message2
		message = message.replace('[Administrator]', '')
		return message

	def Trim(self, message, width):
		if len(message) > width:
			return message[:width / 2 - 1] + '...' + message[2 - width / 2:]
		return message

class TestEffortLogger:
	def __init__(self):
		model = Model()
		model.DateFormat = '%d-%b-%Y'
		self.EL = EffortLogger(model)
		self.TestTrim()
		self.PrepareDescription()
	def TestTrim(self):
		Test.Assert(self.EL.Trim('India is my country', 10), 'Indi...try')
		Test.Assert(self.EL.Trim('India is my country', 15), 'India ...untry')
	def PrepareDescription(self):
		Test.Assert(self.EL.PrepareDescription('explorer.exe', 'ICOS SecsGem Interface'), 'explorer.exe')

class Test:
	_ok = 0
	_notOk = 0

	@classmethod
	def AssertMultiLines(cls, actual, expected):
		isEqual = True
		clsName, funName = cls._GetClassMethod()
		for lineNum,(act,exp) in enumerate(itertools.izip(actual.splitlines(), expected.splitlines()), 1):
			if act != exp:
				message = '{}.{} Line # {}'.format(clsName, funName, lineNum)
				cls._Print(act, exp, message)
				return
		message = '{}.{}'.format(clsName, funName)
		cls._Print(True, True, message)

	@classmethod
	def Assert(cls, actual, expected, message = ''):
		clsName, funName = cls._GetClassMethod()
		message = '{}.{} {}'.format(clsName, funName, message)
		cls._Print(actual, expected, message)

	@classmethod
	def _Print(cls, actual, expected, message):
		if actual == expected:
			print 'Test OK     : ' + message
			cls._ok += 1
		else:
			print 'Test Not OK : ' + message
			print 'Expected    : ' + str(expected)
			print 'Actual      : ' + str(actual)
			cls._notOk += 1

	@classmethod
	def _GetClassMethod(cls):
		stack = inspect.stack()
		clsName = stack[2][0].f_locals['self'].__class__.__name__
		funName = stack[2][0].f_code.co_name
		return (clsName, funName)

	@classmethod
	def PrintResults(cls):
		print
		print 'Tests OK     : ' + str(cls._ok)
		print 'Tests NOT OK : ' + str(cls._notOk)
		print 'Total Tests  : ' + str(cls._ok + cls._notOk)

class UnitTestsRunner:
	def Run(self):
		TestNumValDict()
		TestEffortLogger()
		TestPrettyTable()

		Test.PrintResults()

class ConfigEncoder:
	Configs = ['Debug', 'Release']
	Platforms = ['Win32', 'x64']
	@classmethod
	def DecodeSource(cls, srcArr):
		source = srcArr[0]
		config = cls.Configs[srcArr[1][0] == 'R']
		platform = cls.Platforms[srcArr[1][1:] == '64']
		return (source, config, platform)

	@classmethod
	def EncodeSource(cls, srcSet):
		return [srcSet[0], srcSet[1][0] + srcSet[2][-2:]]

class TestNameEncoer:
	@classmethod
	def Encode(cls, testNameSlots):
		parts = testNameSlots.split()
		return (parts[0], map(int, parts[1].split('_')))

	@classmethod
	def Decode(cls, testName, slots):
		slotStrs = [str(slot) for slot in slots]
		return '{} {}'.format(testName, '_'.join(slotStrs))

class Model:
	def __init__(self):
		self.StartPath = os.path.dirname(os.path.abspath(__file__))
		self.fileName = self.StartPath + '\\KlaRunner.ini'

		self.SrcIndex = -1
		self.TestIndex = -1
		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []
		self.Config = ''
		self.Platform = ''

	def ReadConfigFile(self):
		with open(self.fileName) as f:
			_model = json.load(f)

		self.Sources = [ConfigEncoder.DecodeSource(item) for item in _model['Sources']]
		self.UpdateSource(_model['SrcIndex'], False)
		self.Tests = _model['Tests']
		if not self.UpdateTest(_model['TestIndex'], False):
			self.TestIndex = 0
		self.ActiveSrcs = _model['ActiveSrcs']
		self.VisualStudioBuild = _model['VisualStudioBuild']
		self.VisualStudioRun = _model['VisualStudioRun']
		self.GitBin = _model['GitBin']
		self.VMwareWS = _model['VMwareWS']
		self.EffortLogFile = _model['EffortLogFile']
		self.DateFormat = _model['DateFormat']
		self.MMiConfigPath = _model['MMiConfigPath']
		self.MMiSetupsPath = _model['MMiSetupsPath']
		self.DebugVision = _model['DebugVision']
		self.CopyMmi = _model['CopyMmi']
		self.TempDir = _model['TempDir']
		self.LogFileName = _model['LogFileName']
		self.MenuColCnt = _model['MenuColCnt']
		self.MaxSlots = _model['MaxSlots']
		self.ClearHistory = _model['ClearHistory']

	def WriteConfigFile(self):
		_model = OrderedDict()
		_model['Sources'] = [ConfigEncoder.EncodeSource(item) for item in self.Sources]
		_model['SrcIndex'] = self.SrcIndex
		_model['ActiveSrcs'] = self.ActiveSrcs
		_model['Tests'] = self.Tests
		_model['TestIndex'] = self.TestIndex
		_model['VisualStudioBuild'] = self.VisualStudioBuild
		_model['VisualStudioRun'] = self.VisualStudioRun
		_model['GitBin'] = self.GitBin
		_model['VMwareWS'] = self.VMwareWS
		_model['EffortLogFile'] = self.EffortLogFile
		_model['DateFormat'] = self.DateFormat
		_model['MMiConfigPath'] = self.MMiConfigPath
		_model['MMiSetupsPath'] = self.MMiSetupsPath
		_model['DebugVision'] = self.DebugVision
		_model['CopyMmi'] = self.CopyMmi
		_model['TempDir'] = self.TempDir
		_model['LogFileName'] = self.LogFileName
		_model['MenuColCnt'] = self.MenuColCnt
		_model['MaxSlots'] = self.MaxSlots
		_model['ClearHistory'] = self.ClearHistory

		with open(self.fileName, 'w') as f:
			json.dump(_model, f, indent=3)

	def UpdateSource(self, index, writeToFile):
		if index < 0 or index >= len(self.Sources):
			return False
		if self.SrcIndex == index:
			return False
		self.SrcIndex = index
		self.Source, self.Config, self.Platform = self.Sources[self.SrcIndex]
		self.Branch = Git.GetBranch(self.Source)
		if writeToFile:
			self.WriteConfigFile()
		return True

	def UpdateTest(self, index, writeToFile):
		if index < 0 or index >= len(self.Tests):
			return False
		if self.TestIndex == index:
			return False
		self.TestIndex = index
		self.TestName, self.slots = TestNameEncoer.Encode(self.Tests[self.TestIndex])
		if writeToFile:
			self.WriteConfigFile()
		return True

	def UpdateConfig(self, index):
		if index < 0 or index >= len(ConfigEncoder.Configs):
			return False
		newConfig = ConfigEncoder.Configs[index]
		if self.Config == newConfig:
			return False
		self.Config = newConfig
		self.Sources[self.SrcIndex] = self.Source, self.Config, self.Platform
		return True

	def UpdatePlatform(self, index):
		if index < 0 or index >= len(ConfigEncoder.Platforms):
			return False
		newPlatform = ConfigEncoder.Platforms[index]
		if self.Platform == newPlatform:
			return False
		self.Platform = newPlatform
		self.Sources[self.SrcIndex] = self.Source, self.Config, self.Platform
		return True

	def UpdateSlots(self, index, isSelected):
		slotNum = index + 1
		if isSelected:
			self.slots.append(slotNum)
		else:
			self.slots.remove(slotNum)
		self.Tests[self.TestIndex] = TestNameEncoer.Decode(self.TestName, self.slots)

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

	def GetLibsTestPath(self):
		return self.Source + '/libs/testing'

	def GetBuildConfig(self):
		debugConfigSet = ('debugx64', 'debug')
		releaseConfigSet = ('releasex64', 'release')
		configSet = (debugConfigSet, releaseConfigSet)[self.Config == 'Release']
		return configSet[self.Platform == 'Win32']

def main():
	if (len(sys.argv) == 2):
		param1 = sys.argv[1].lower()
		if param1 == 'test':
			UnitTestsRunner().Run()
			return
		elif param1 == 'ui':
			UI().Run()
			return
	if (__name__ == '__main__'):
		KlaRunner().Run()

main()
