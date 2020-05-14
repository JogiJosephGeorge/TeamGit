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
import tkMessageBox as messagebox
import ttk

class UIFactory:
	@classmethod
	def AddButton(cls, parent, text, r, c, cmd, args, width = 0):
		if args is None:
			action = cmd
		else:
			action = lambda: cmd(*args)
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
	def AddFrame(cls, parent, r, c, px = 0, py = 0, columnspan=1, sticky='w'):
		frame = ttk.Frame(parent)
		frame.grid(row=r, column=c, sticky=sticky, padx=px, pady=py, columnspan=columnspan)
		return frame

class UI:
	def __init__(self):
		self.klaRunner = KlaRunner()
		self.model = self.klaRunner.model
		KlaRunner.RunFromUI = True

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
		self.Row = 0
		self.CreateUI(frame)

	def AddRow(self):
		self.Row += 1

	def CreateUI(self, parent):
		UIFactory.AddLabel(parent, ' ', self.Row, 2)
		UIFactory.AddLabel(parent, ' ', self.Row, 5)

		self.AddRow()
		self.AddSource(parent, 0)
		self.AddConfig(parent, 3)
		self.AddAttachMmi(parent, 6)

		self.AddRow()
		self.AddBranch(parent, 0)
		self.AddPlatform(parent, 3)
		self.AddCopyMmi(parent, 6)

		self.AddRow()
		self.AddTest(parent, 0)
		self.AddActiveSrcs(parent, 3)

		self.AddRow()
		self.AddSlots(parent, 0)

	def AddSource(self, parent, c):
		UIFactory.AddLabel(parent, 'Source', self.Row, c)
		srcs = [src[0] for src in self.model.Sources]
		self.cmbSource = UIFactory.AddCombo(parent, srcs, self.model.SrcIndex, self.Row, c+1, self.OnSrcChanged, 70)

	def OnSrcChanged(self, event):
		if self.model.UpdateSource(self.cmbSource[0].current(), False):
			self.lblBranch[1].set(self.model.Branch)
			self.cmbConfig[1].set(self.model.Config)
			self.cmbPltfm[1].set(self.model.Platform)
			print 'Source Changed to : ' + self.model.Source

	def AddConfig(self, parent, c):
		configInx = ConfigEncoder.Configs.index(self.model.Config)
		UIFactory.AddLabel(parent, 'Config', self.Row, c)
		self.cmbConfig = UIFactory.AddCombo(parent, ConfigEncoder.Configs, configInx, self.Row, c+1, self.OnConfigChanged, 10)

	def OnConfigChanged(self, event):
		if self.model.UpdateConfig(self.cmbConfig[0].current()):
			print 'Config Changed to : ' + self.model.Config

	def AddBranch(self, parent, c):
		UIFactory.AddLabel(parent, 'Branch', self.Row, c)
		self.lblBranch = UIFactory.AddLabel(parent, self.model.Branch, self.Row, c+1)

	def AddPlatform(self, parent, c):
		platformInx = ConfigEncoder.Platforms.index(self.model.Platform)
		UIFactory.AddLabel(parent, 'Platform', self.Row, c)
		self.cmbPltfm = UIFactory.AddCombo(parent, ConfigEncoder.Platforms, platformInx, self.Row, c+1, self.OnPlatformChanged, 10)

	def OnPlatformChanged(self, event):
		if self.model.UpdatePlatform(self.cmbPltfm[0].current()):
			print 'Platform Changed to : ' + self.model.Platform

	def AddTest(self, parent, c):
		UIFactory.AddLabel(parent, 'Test', self.Row, c)
		testNames = self.model.AutoTests.GetNames()
		self.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, self.Row, c+1, self.OnTestChanged, 70)

	def OnTestChanged(self, event):
		if self.model.UpdateTest(self.cmbTest[0].current(), False):
			print 'Test Changed to : ' + self.model.TestName
			for i in range(self.model.MaxSlots):
				self.chkSlots[i].set((i+1) in self.model.slots)

	def AddAttachMmi(self, parent, c):
		UIFactory.AddLabel(parent, 'Attach MMi', self.Row, c)
		self.chkAttachMmi = UIFactory.AddCheckBox(parent, self.model.DebugVision, self.Row, c+1, self.OnAttach)

	def OnAttach(self):
		self.model.DebugVision = self.chkAttachMmi.get()
		print 'Attach to MMi : ' + ('Yes' if self.model.DebugVision else 'No')

	def AddCopyMmi(self, parent, c):
		UIFactory.AddLabel(parent, 'Copy MMI to Icos', self.Row, c)
		self.chkCopyMmi = UIFactory.AddCheckBox(parent, self.model.CopyMmi, self.Row, c+1, self.OnCopyMmi)

	def OnCopyMmi(self):
		self.model.CopyMmi = self.chkCopyMmi.get()
		print 'Copy MMI to ICOS : ' + str(self.chkCopyMmi.get())

	def AddSlots(self, parent, c):
		UIFactory.AddLabel(parent, 'Slots', self.Row, c)
		frame = UIFactory.AddFrame(parent, self.Row, c+1, columnspan=5)
		self.chkSlots = []
		for i in range(self.model.MaxSlots):
			isSelected = (i+1) in self.model.slots
			UIFactory.AddLabel(frame, str(i+1), 0, i * 2)
			self.chkSlots.append(UIFactory.AddCheckBox(frame, isSelected, 0, i * 2 + 1, self.OnSlotChn, i))

	def OnSlotChn(self, index):
		self.model.UpdateSlots(index, self.chkSlots[index].get())
		print 'Slots for the current test : ' + str(self.model.slots)

	def AddActiveSrcs(self, parent, c):
		UIFactory.AddLabel(parent, 'Sources', self.Row, c)
		frame = UIFactory.AddFrame(parent, self.Row, c+1, columnspan=4)
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

class ThreadHandler:
	def __init__(self):
		self.threads = {}
		self.Buttons = {}

	def Start(self, name, funPnt, args = None):
		if args is None:
			self.threads[name] = threading.Thread(target=funPnt)
		else:
			self.threads[name] = threading.Thread(target=funPnt, args=args)
		self.threads[name].start()
		self.Buttons[name].config(background='red')
		threading.Thread(target=self.WaitForThread, args=(name,)).start()

	def WaitForThread(self, name):
		self.threads[name].join()
		self.Buttons[name].config(background='SystemButtonFace')
		del self.threads[name]

	def AddButton(self, but):
		name = self.GetButtonName(but)
		self.Buttons[name] = but

	def GetButtonName(self, but):
		return ' '.join(but.config('text')[-1])

class UIMainMenu:
	def __init__(self, parent, r, c, klaRunner):
		self.model = klaRunner.model
		self.frame = UIFactory.AddFrame(parent, r, c, 20, 20)
		self.klaRunner = klaRunner
		self.testRunner = AutoTestRunner(self.model)
		self.settings = Settings(self.model, self.klaRunner)
		self.appRunner = AppRunner(self.model, self.testRunner)
		self.klaSourceBuilder = KlaSourceBuilder(self.model, self.klaRunner)
		self.threadHandler = ThreadHandler()
		self.Col = 0
		self.CreateUI(self.frame)

	def CreateUI(self, parent):
		self.AddColumn1(parent)
		self.AddColumn2(parent)
		self.AddColumn3(parent)
		self.AddColumn4(parent)
		self.AddColumn5(parent)

	def AddColumn1(self, parent):
		self.CreateColumnFrame(parent)
		self.AddButton('Open Python', self.klaRunner.OpenPython)
		self.AddParallelButton('Run test', self.testRunner.RunAutoTest, (False,))
		self.AddParallelButton('Start test', self.testRunner.RunAutoTest, (True,))
		self.AddButton('Run Handler and MMi', self.appRunner.RunHandlerMMi)
		self.AddButton('Run Handler alone', self.appRunner.RunHandler)
		self.AddButton('Run MMi from Source', self.appRunner.RunMMi, (True,False))
		self.AddButton('Run MMi from C:Icos', self.appRunner.RunMMi, (False,False))

	def AddColumn2(self, parent):
		sourceBuilder = self.klaSourceBuilder
		self.CreateColumnFrame(parent)
		self.AddButton('Open CIT100', sourceBuilder.OpenSolution, (0,))
		self.AddButton('Open Simulator', sourceBuilder.OpenSolution, (1,))
		self.AddButton('Open Mmi', sourceBuilder.OpenSolution, (2,))
		self.AddButton('Open MockLicense', sourceBuilder.OpenSolution, (3,))
		self.AddButton('Open Converters', sourceBuilder.OpenSolution, (4,))

	def AddColumn3(self, parent):
		self.CreateColumnFrame(parent)
		self.AddButton('Open Test Folder', self.klaRunner.OpenTestFolder)
		self.AddButton('Open Local Diff', AppRunner.OpenLocalDif, (self.model,))
		self.AddButton('Open Git GUI', Git.OpenGitGui, (self.model,))
		self.AddButton('Open Git Bash', Git.OpenGitBash, (self.model,))

	def AddColumn4(self, parent):
		self.CreateColumnFrame(parent)
		self.AddButton('Run Slots', VMWareRunner.RunSlots, (self.model,))
		self.AddButton('Run ToolLink Host', self.appRunner.RunToollinkHost)
		self.AddButton('Comment VisionSystem', self.testRunner.ModifyVisionSystem)
		self.AddButton('Copy Mock License', self.testRunner.CopyMockLicense)
		self.AddButton('Copy xPort xml', self.testRunner.CopyIllumRef)
		self.AddButton('Print mmi.h IDs', self.klaRunner.PrintMissingIds)
		self.AddButton('Copy MmiSaveLogs.exe', self.klaRunner.CopyMmiSaveLogExe)

	def AddColumn5(self, parent):
		sourceBuilder = self.klaSourceBuilder
		settings = self.settings
		effortLogger = EffortLogger(self.model)
		self.CreateColumnFrame(parent)
		self.AddButton('Clear Output', OsOperations.Cls)
		self.AddParallelButton('Clean Source', self.klaSourceBuilder.CleanSource)
		self.AddParallelButton('Build Source', self.klaSourceBuilder.BuildSource)
		self.AddButton('Effort Log', effortLogger.Print)
		self.AddButton('Stop All KLA Apps', AppRunner.StopTasks, (False,))
		self.AddButton('Version', AppRunner.ShowVersion)

	def CreateColumnFrame(self, parent):
		self.ColFrame = UIFactory.AddFrame(parent, 0, self.Col, sticky='n')
		self.Col += 1
		self.ColInx = 0

	def AddParallelButton(self, label, funPnt, arg = None):
		args = (label, funPnt, arg)
		but = UIFactory.AddButton(self.ColFrame, label, self.ColInx, 0,
			self.threadHandler.Start, args, 19)
		self.threadHandler.AddButton(but)
		self.ColInx += 1

	def AddButton(self, label, funPnt, args = None):
		but = UIFactory.AddButton(self.ColFrame, label, self.ColInx, 0, funPnt, args, 19)
		self.threadHandler.AddButton(but)
		self.ColInx += 1

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
			[2, ['Run test' + autoTest, testRunner.RunAutoTest, False]],
			[3, ['Start test' + autoTest, testRunner.RunAutoTest, True]],
			[4, ['Run Handler and MMi', self.appRunner.RunHandlerMMi]],
			[5, ['Run Handler alone', self.appRunner.RunHandler]],
			[6, ['Run MMi from Source', self.appRunner.RunMMi, True]],
			[7, ['Run MMi from C:Icos', self.appRunner.RunMMi, False]],
			[8, ['Run Slots', VMWareRunner.RunSlots, model]],
			[9, ['Run ToolLink Host', self.appRunner.RunToollinkHost]],
		],[
			[10, ['Open CIT100', sourceBuilder.OpenSolution, 0]],
			[11, ['Open Simulator', sourceBuilder.OpenSolution, 1]],
			[12, ['Open Mmi', sourceBuilder.OpenSolution, 2]],
			[14, ['Open MockLicense', sourceBuilder.OpenSolution, 3]],
			[15, ['Open Converters', sourceBuilder.OpenSolution, 4]],
		],[
			[20, ['Open Test Folder', self.klaRunner.OpenTestFolder]],
			[21, ['Open Local Diff', AppRunner.OpenLocalDif, model]],
			[22, ['Open Git GUI', Git.OpenGitGui, model]],
			[23, ['Open Git Bash', Git.OpenGitBash, model]],
			[24, ['Comment VisionSystem', testRunner.ModifyVisionSystem]],
			[25, ['Copy Mock License', testRunner.CopyMockLicense]],
			[26, ['Copy xPort xml', testRunner.CopyIllumRef, model.ClearHistory]],
			[27, ['Print mmi.h IDs', self.klaRunner.PrintMissingIds]],
			[28, ['Copy MmiSaveLogs.exe', self.klaRunner.CopyMmiSaveLogExe]],
		],[
			[91, ['Build Source ' + activeSrcs, sourceBuilder.BuildSource]],
			[92, ['Clean Source ' + activeSrcs, sourceBuilder.CleanSource]],
			[93, ['Add Test', settings.AddTest]],
			[94, ['Change Test', settings.ChangeTest]],
			[95, ['Change Source', settings.ChangeSource]],
			[96, ['Change MMI Attach', settings.ChangeDebugVision]],
			[97, ['Effort Log', effortLogger.Print]],
			[98, ['Clear Output', OsOperations.Cls]],
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
	RunFromUI = False

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
		FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))
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

	def CopyMmiSaveLogExe(self):
		destin = os.path.abspath("{}/handler/tests/{}~\Icos".format(
			self.model.Source, self.model.TestName))
		src = os.path.abspath('{}/mmi/mmi/Bin/{}/{}/MmiSaveLogs.exe'.format(
			self.model.Source, self.model.Platform, self.model.Config))
		FileOperations.Copy(src, destin)
		pass

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

	@classmethod
	def ShowInfo(cls, caption, msg, doPause):
		if KlaRunner.RunFromUI:
			messagebox.showinfo(caption, msg)
		else:
			print msg
			OsOperations.Pause(doPause)

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
		'''
		wmic process where name="mmi.exe" call terminate
		wmic process where "name='mmi.exe'" delete
		taskkill /IM "mmi.exe" /T /F
		'''
		print '{} Process IDs : {}'.format(exeName, processIds)
		if exceptProcId < 0:
			OsOperations.Popen([ 'TASKKILL', '/IM', exeName, '/T', '/F' ])
		else:
			for proId in processIds:
				OsOperations.Popen([ 'TASKKILL', '/PID', str(proId), '/T', '/F' ])

	@classmethod
	def OpenLocalDif(self, model):
		par = [ 'TortoiseGitProc.exe', '/command:diff', '/path:' + model.Source + '' ]
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)
		OsOperations.Pause()

	@classmethod
	def ShowVersion(self):
		v = OsOperations.ProcessOpen(['git', 'describe', '--always'])
		msg = '1.0.' + v
		KlaRunner.ShowInfo('Version', msg, True)

class VMWareRunner:
	@classmethod
	def RunSlots(self, model):
		vMwareWS = model.VMwareWS
		slots = model.slots
		vmRunExe = vMwareWS + "vmrun.exe"
		vmWareExe = vMwareWS + "vmware.exe"
		vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'
		par = [vmRunExe, '-vp', '1', 'list']
		output = OsOperations.ProcessOpen(par)
		runningSlots = []
		searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
		for line in output.split():
			m = re.search(searchPattern, line, re.IGNORECASE)
			if m:
				runningSlots.append(int(m.group(1)))

		for slot in slots:
			vmxPath = vmxGenericPath.format(slot)
			slotName = 'VMware Slot ' + str(slot)
			if slot in runningSlots:
				print slotName + ' : Restarted.'
				subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
			else:
				subprocess.Popen([vmWareExe, vmxPath])
				message = 'Please start ' + slotName
				print message
				os.system('PAUSE')
				print slotName + ' : Started.'

class AutoTestRunner:
	def __init__(self, model):
		self.model = model

	def CopyMockLicense(self, fromSrc = True, doPause = True):
		args = (self.model.Source, self.model.Platform, self.model.Config)
		if fromSrc:
			mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(*args))
		else:
			mmiPath = 'C:/icos'
		licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
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

	def RunAutoTest(self, startUp):
		AppRunner.StopTasks(False)
		VMWareRunner.RunSlots(self.model)
		self.ModifyVisionSystem(False)
		self.CopyIllumRef(False, True)
		#FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
		os.chdir(self.model.StartPath)

		FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))
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
			print 'The path ({}) already exists in sys.path.'.format(newPath)
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
		index = self.SelectOption1('Test Name', self.model.AutoTests.GetNames(), self.model.TestIndex)
		self.model.UpdateTest(index, True)
		OsOperations.Pause(self.model.ClearHistory)

	def AddTest(self):
		number = OsOperations.InputNumber('Type the number of test then press ENTER: ')
		testName = AutoTestRunner.GetTestName(self.model.Source, number)
		if testName == '':
			print 'There is no test exists for the number : ' + str(number)
			return
		if self.model.AutoTests.Contains(testName):
			print 'The given test ({}) already exists'.format(testName)
			return
		slots = raw_input('Enter slots : ')
		index = self.model.AutoTests.AddTest(testName, slots)
		self.model.UpdateTest(index, True)
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
		if self.model.Config is not 'Debug' or self.model.Platform is not 'Win32':
			msg = 'Please check configuration and platform in Visual Studio'
			KlaRunner.ShowInfo('Visual Studio', msg, self.model.ClearHistory)
		else:
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
	def Delete(cls, fileName):
		if os.path.isfile(fileName):
			os.remove(fileName)
			print 'File deleted : ' + fileName

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
		if condition and not KlaRunner.RunFromUI:
			#raw_input('Press ENTER key to continue . . .')
			os.system('PAUSE')

	@classmethod
	def GetProcessIds(cls, exeName):
		exeName = exeName.lower()
		params = [ 'TASKLIST', '/FI' ]
		params.append('IMAGENAME eq {}'.format(exeName))
		output = OsOperations.ProcessOpen(params)
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
	def ProcessOpen(cls, params):
		return subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]

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
		output = OsOperations.ProcessOpen(params)
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
	def OpenGitGui(self, model):
		param = [ 'git-gui', '--working-dir', model.Source ]
		print 'Staring Git GUI'
		subprocess.Popen(param)
		OsOperations.Pause()

	@classmethod
	def OpenGitBash(self, model):
		par = 'start {}sh.exe --cd={}'.format(model.GitBin, model.Source)
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
		self.DayStarts = timedelta(hours=4) # 4am
		self.ShowPrevDaysLogs = 1

	def Print(self):
		for i in range(self.ShowPrevDaysLogs, 0, -1):
			prevDay = datetime.now() - timedelta(days=i)
			self.PrintErrortTable(prevDay, prevDay.strftime(self.model.DateFormat))
		today = datetime.now()
		self.PrintErrortTable(today, 'Today')
		OsOperations.Pause()
		self.CheckApplication()

	def PrintErrortTable(self, date, message):
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
		dollarTime = timedelta()
		for k,v in dictAppNameToTime.items():
			if v > self.MinTime:
				data.append([self.Trim(k, self.ColWidth), v])
			else:
				oneMinAppsTime += v
			if k == '$':
				dollarTime = v
		minAppDesc = 'Other Apps Less Than {} Minute(s)'.format(self.MinMinutes)
		data.append([minAppDesc, oneMinAppsTime])
		data = sorted(data, key = lambda x : x[1], reverse=True)
		menuData = [[message, 'Time Taken'], ['-']] + data
		menuData += [['-'], ['Total Time', totalTime]]
		table = PrettyTable(TableFormatFactory().SetSingleLine()).ToString(menuData)
		#table = datetime.now().strftime('%Y %b %d %H:%M:%S\n') + table
		#FileOperations.Append(logFile + '.txt', table)
		print table,
		print totalTime - dollarTime

	def IsSameDate(self, a, b):
		a1 = a - self.DayStarts
		b1 = b - self.DayStarts
		return a1.day == b1.day and a1.month == b1.month and a1.year == b1.year

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

	def CheckApplication(self):
		if len(OsOperations.GetProcessIds('EffortCapture_2013.exe')) > 0:
			print 'Effort logger is running'
		else:
			print 'Effort logger is not running'

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

class AutoTests:
	def __init__(self, fileName):
		self.FileName = fileName

	def Read(self):
		self.Tests = list(FileOperations.ReadLine(self.FileName))

	def Write(self):
		content = '\n'.join(self.Tests)
		FileOperations.Write(self.FileName, content)

	def IsValidIndex(self, index):
		return index >= 0 and index < len(self.Tests)

	def GetTest(self, index):
		if self.IsValidIndex(index):
			return self.Encode(self.Tests[index])

	def GetNames(self):
		return [self.Encode(item)[0] for item in self.Tests]

	def GetNameSlots(self, index):
		return self.Encode(self.Tests[index])

	def SetNameSlots(self, index, name, slots):
		self.Tests[index] = self.Decode(name, slots)

	def Contains(self, testName):
		return ArrayOrganizer.ContainsInArray(testName, self.Tests) >= 0

	def AddTest(self, testName, slots):
		testNameAndSlot = '{} {}'.format(testName, slots)
		self.Tests.append(testNameAndSlot)
		return len(self.Tests) - 1

	def Encode(self, testNameSlots):
		parts = testNameSlots.split()
		return (parts[0], map(int, parts[1].split('_')))

	def Decode(self, testName, slots):
		slotStrs = [str(slot) for slot in slots]
		return '{} {}'.format(testName, '_'.join(slotStrs))

class Model:
	def __init__(self):
		self.StartPath = os.path.dirname(os.path.abspath(__file__))
		self.fileName = self.StartPath + '\\KlaRunner.ini'
		self.AutoTests = AutoTests(self.StartPath + '\\Tests.txt')

		self.SrcIndex = -1
		self.TestIndex = -1
		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []
		self.Config = ''
		self.Platform = ''

	def ReadConfigFile(self):
		self.AutoTests.Read()
		with open(self.fileName) as f:
			_model = json.load(f)

		self.Sources = [ConfigEncoder.DecodeSource(item) for item in _model['Sources']]
		self.UpdateSource(_model['SrcIndex'], False)
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
		self.AutoTests.Write()
		_model = OrderedDict()
		_model['Sources'] = [ConfigEncoder.EncodeSource(item) for item in self.Sources]
		_model['SrcIndex'] = self.SrcIndex
		_model['ActiveSrcs'] = self.ActiveSrcs
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
		if not self.AutoTests.IsValidIndex(index):
			return False
		if self.TestIndex == index:
			return False
		self.TestIndex = index
		self.TestName, self.slots = self.AutoTests.GetNameSlots(self.TestIndex)
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
			self.slots.sort()
		else:
			self.slots.remove(slotNum)
		self.AutoTests.SetNameSlots(self.TestIndex, self.TestName, self.slots)

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
