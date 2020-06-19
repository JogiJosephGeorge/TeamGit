# coding=utf-8
from collections import OrderedDict
import ctypes
from datetime import datetime, timedelta
from functools import partial
import time
import inspect
import itertools
import json
import msvcrt
import os
import re
import subprocess
import sys
import shutil
import threading
import Tkinter as tk
import tkMessageBox as messagebox
import ttk
import tkFileDialog

class UIFactory:
	@classmethod
	def CreateWindow(cls, parent, title, startPath):
		if parent is None:
			window = tk.Tk()
		else:
			parent.withdraw()
			window = tk.Toplevel(parent)
		window.title(title)
		iconPath = startPath + r'\Plus.ico'
		#window.geometry('750x350')
		#window.resizable(0, 0) # To Disable Max button, Then half screen won't work
		#window.overrideredirect(1) # Remove Window border
		if os.path.exists(iconPath):
			window.iconbitmap(iconPath)
		return window

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
	def AddText(cls, parent, r, c, width = 0):
		textBox = tk.Text(parent, width=width)
		textBox.grid(row=r, column=c, sticky='w')
		return textBox

	@classmethod
	def AddCombo(cls, parent, values, inx, r, c, cmd, width = 0):
		var = tk.StringVar()
		combo = ttk.Combobox(parent, textvariable=var)
		combo['state'] = 'readonly'
		combo['values'] = values
		if inx >= 0 and inx < len(values):
			combo.current(inx)
		if width > 0:
			combo['width'] = width
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

	@classmethod
	def GetTextValue(cls, textBox):
		return textBox.get('1.0', 'end-1c')

class UI:
	def __init__(self):
		KlaRunner.RunFromUI = True

	def Run(self):
		self.model = Model()
		VM = UIViewModel(self.model)
		if not os.path.exists(self.model.ConfigInfo.FileName):
			UISettings(None, self.model, VM).Show()
			return
		else:
			self.model.ReadConfigFile()
		self.klaRunner = KlaRunner(self.model)

		if not ctypes.windll.shell32.IsUserAnAdmin():
			print 'Please run this application with Administrator privilates'
			os.system('PAUSE')
			return
		title = 'KLA Application Runner 1.0.' + Git.GetHash()
		self.window = UIFactory.CreateWindow(None, title, self.model.StartPath)
		UIHeader(self.window, 0, 0, self.model, VM)
		UIMainMenu(self.window, 1, 0, self.klaRunner, VM)
		self.window.mainloop()

class UIHeader:
	def __init__(self, parent, r, c, model, VM):
		self.model = model
		self.VM = VM
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
		self.AddActiveSrcs(parent, 3)

		self.AddRow()
		self.AddBranch(parent, 0)
		self.AddConfig(parent, 3)
		self.AddAttachMmi(parent, 6)

		self.AddRow()
		self.AddTest(parent, 0)
		self.AddPlatform(parent, 3)
		if self.model.ShowAllButtons:
			self.AddCopyMmi(parent, 6)

		self.AddRow()
		self.AddSlots(parent, 0)

	def AddSource(self, parent, c):
		UIFactory.AddLabel(parent, 'Source', self.Row, c)
		srcs = self.VM.GetSourceComboItems()
		self.VM.cmbSource = UIFactory.AddCombo(parent, srcs, self.model.SrcIndex, self.Row, c+1, self.VM.OnSrcChanged, 70)

	def AddConfig(self, parent, c):
		configInx = ConfigEncoder.Configs.index(self.model.Config)
		UIFactory.AddLabel(parent, 'Config', self.Row, c)
		self.VM.cmbConfig = UIFactory.AddCombo(parent, ConfigEncoder.Configs, configInx, self.Row, c+1, self.VM.OnConfigChanged, 10)

	def AddBranch(self, parent, c):
		UIFactory.AddLabel(parent, 'Branch', self.Row, c)
		self.VM.lblBranch = UIFactory.AddLabel(parent, self.model.Branch, self.Row, c+1)

	def AddPlatform(self, parent, c):
		platformInx = ConfigEncoder.Platforms.index(self.model.Platform)
		UIFactory.AddLabel(parent, 'Platform', self.Row, c)
		self.VM.cmbPltfm = UIFactory.AddCombo(parent, ConfigEncoder.Platforms, platformInx, self.Row, c+1, self.VM.OnPlatformChanged, 10)

	def AddTest(self, parent, c):
		UIFactory.AddLabel(parent, 'Test', self.Row, c)
		testNames = self.model.AutoTests.GetNames()
		self.VM.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, self.Row, c+1, self.VM.OnTestChanged, 70)

	def AddAttachMmi(self, parent, c):
		UIFactory.AddLabel(parent, 'Attach MMi', self.Row, c)
		self.VM.chkAttachMmi = UIFactory.AddCheckBox(parent, self.model.DebugVision, self.Row, c+1, self.VM.OnAttach)

	def AddCopyMmi(self, parent, c):
		UIFactory.AddLabel(parent, 'Copy MMI to Icos', self.Row, c)
		self.VM.chkCopyMmi = UIFactory.AddCheckBox(parent, self.model.CopyMmi, self.Row, c+1, self.VM.OnCopyMmi)

	def AddSlots(self, parent, c):
		UIFactory.AddLabel(parent, 'Slots', self.Row, c)
		frame = UIFactory.AddFrame(parent, self.Row, c+1, columnspan=5)
		self.VM.chkSlots = []
		for i in range(self.model.MaxSlots):
			isSelected = (i+1) in self.model.slots
			UIFactory.AddLabel(frame, str(i+1), 0, i * 2)
			self.VM.chkSlots.append(UIFactory.AddCheckBox(frame, isSelected, 0, i * 2 + 1, self.VM.OnSlotChn, i))

	def AddActiveSrcs(self, parent, c):
		UIFactory.AddLabel(parent, 'Active Srcs', self.Row, c)
		frame = UIFactory.AddFrame(parent, self.Row, c+1, columnspan=4)
		self.VM.chkActiveSrcs = []
		srcs = self.model.ActiveSrcs
		for i in range(len(self.model.Sources)):
			isSelected = True if i in srcs else False
			UIFactory.AddLabel(frame, str(i+1), 0, i * 2)
			self.VM.chkActiveSrcs.append(UIFactory.AddCheckBox(frame, isSelected, 0, i * 2 + 1, self.VM.OnActiveSrcsChn, i))

class UIViewModel:
	def __init__(self, model):
		self.model = model

	def OnSrcChanged(self, event):
		if self.model.SrcCnf.UpdateSource(self.cmbSource[0].current(), True):
			self.lblBranch[1].set(self.model.Branch)
			self.cmbConfig[1].set(self.model.Config)
			self.cmbPltfm[1].set(self.model.Platform)
			print 'Source Changed to : ' + self.model.Source
			#UIViewModel.RestartApp(self.model)

	@classmethod
	def RestartApp(cls, model):
		print 'Application Restarted.'
		argv = sys.argv
		if not os.path.exists(argv[0]):
			argv[0] = model.StartPath + '\\' + argv[0]
			#argv[0] = model.StartPath + '\\StartKLARunner.lnk'
		python = sys.executable
		os.execl(python, python, * argv)

	def OnConfigChanged(self, event):
		if self.model.UpdateConfig(self.cmbConfig[0].current()):
			self.model.WriteConfigFile()
			print 'Config Changed to : ' + self.model.Config

	def OnPlatformChanged(self, event):
		if self.model.UpdatePlatform(self.cmbPltfm[0].current()):
			self.model.WriteConfigFile()
			print 'Platform Changed to : ' + self.model.Platform

	def OnTestChanged(self, event):
		if self.model.UpdateTest(self.cmbTest[0].current(), True):
			print 'Test Changed to : ' + self.model.TestName
			for i in range(self.model.MaxSlots):
				self.chkSlots[i].set((i+1) in self.model.slots)

	def OnAttach(self):
		self.model.DebugVision = self.chkAttachMmi.get()
		self.model.WriteConfigFile()
		print 'Attach to MMi : ' + ('Yes' if self.model.DebugVision else 'No')

	def OnCopyMmi(self):
		self.model.CopyMmi = self.chkCopyMmi.get()
		self.model.WriteConfigFile()
		print 'Copy MMI to ICOS : ' + str(self.chkCopyMmi.get())

	def OnSlotChn(self, index):
		self.model.UpdateSlots(index, self.chkSlots[index].get())
		self.model.WriteConfigFile()
		print 'Slots for the current test : ' + str(self.model.slots)

	def OnActiveSrcsChn(self, index):
		if self.chkActiveSrcs[index].get():
			self.model.ActiveSrcs.append(index)
			self.model.ActiveSrcs = list(set(self.model.ActiveSrcs))
			print 'Enabled the source : ' + str(self.model.Sources[index][0])
		else:
			self.model.ActiveSrcs.remove(index)
			print 'Disabled the source : ' + str(self.model.Sources[index][0])
		self.model.WriteConfigFile()

	def GetSourceComboItems(self):
		#return [src[0] for src in self.model.Sources]
		srcCmb = []
		for src in self.model.Sources:
			branch = Git.GetBranch(src[0])
			srcCmb.append('{} ({})'.format(src[0], branch))
		return srcCmb

	def UpdateCombo(self):
		self.cmbSource[0]['values'] = self.GetSourceComboItems()
		self.cmbTest[0]['values'] = self.model.AutoTests.GetNames()

class ThreadHandler:
	def __init__(self):
		self.threads = {}
		self.Buttons = {}

	def Start(self, name, funPnt, args = None, InitFunPnt = None):
		if InitFunPnt is not None:
			if not InitFunPnt():
				return
		if args is None:
			self.threads[name] = threading.Thread(target=funPnt)
		else:
			self.threads[name] = threading.Thread(target=funPnt, args=args)
		self.threads[name].start()
		self.SetButtonActive(name)
		threading.Thread(target=self.WaitForThread, args=(name,)).start()

	def WaitForThread(self, name):
		self.threads[name].join()
		self.SetButtonNormal(name)
		del self.threads[name]

	def AddButton(self, but):
		name = self.GetButtonName(but)
		self.Buttons[name] = but

	def GetButtonName(self, but):
		return ' '.join(but.config('text')[-1])

	def SetButtonActive(self, name):
		self.Buttons[name]['state'] = 'disabled'
		#for button in self.Buttons.values():
		#	button['state'] = 'disabled'
		self.Buttons[name].config(background='red')

	def SetButtonNormal(self, name):
		self.Buttons[name]['state'] = 'normal'
		#for button in self.Buttons.values():
		#	button['state'] = 'normal'
		self.Buttons[name].config(background='SystemButtonFace')

class UIMainMenu:
	def __init__(self, parent, r, c, klaRunner, VM):
		self.parent = parent
		self.model = klaRunner.model
		self.frame = UIFactory.AddFrame(self.parent, r, c, 20, 20)
		self.klaRunner = klaRunner
		self.VM = VM
		self.testRunner = AutoTestRunner(self.model)
		self.settings = Settings(self.model, self.klaRunner)
		self.appRunner = AppRunner(self.model, self.testRunner)
		self.klaSourceBuilder = KlaSourceBuilder(self.model, self.klaRunner)
		self.threadHandler = ThreadHandler()
		self.Col = 0
		self.AddColumn1(self.frame)
		self.AddColumn2(self.frame)
		self.AddColumn3(self.frame)
		self.AddColumn4(self.frame)
		self.AddColumn5(self.frame)

	def AddColumn1(self, parent):
		self.CreateColumnFrame(parent)
		self.AddButton('Stop All KLA Apps', TaskMan.StopTasks, (False,))
		tr = self.testRunner
		self.AddParallelButton('Run test', tr.RunAutoTest, (False,False), tr.InitAutoTest)
		self.AddParallelButton('Start test', tr.RunAutoTest, (True,False), tr.InitAutoTest)
		if self.model.ShowAllButtons:
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
		self.AddButton('Open Python', self.klaRunner.OpenPython)
		self.AddButton('Open Test Folder', self.klaRunner.OpenTestFolder)
		self.AddButton('Compare Test Results', self.klaRunner.CompareMmiReports)
		self.AddButton('Open Local Diff', AppRunner.OpenLocalDif, (self.model,))
		if self.model.ShowAllButtons:
			self.AddButton('Open Git GUI', Git.OpenGitGui, (self.model,))
			self.AddButton('Open Git Bash', Git.OpenGitBash, (self.model,))
		self.AddButton('Git Fetch Pull', Git.FetchPull, (self.model,))

	def AddColumn4(self, parent):
		self.CreateColumnFrame(parent)
		self.AddButton('Run Slots', VMWareRunner.RunSlots, (self.model,))
		if self.model.ShowAllButtons:
			self.AddButton('Comment VisionSystem', PreTestActions.ModifyVisionSystem, (self.model,))
			self.AddButton('Run ToolLink Host', self.appRunner.RunToollinkHost)
			self.AddButton('Copy Mock License', PreTestActions.CopyMockLicense, (self.model,))
			self.AddButton('Copy xPort xml', PreTestActions.CopyxPortIllumRef, (self.model,))
			self.AddButton('Copy MmiSaveLogs.exe', PreTestActions.CopyMmiSaveLogExe, (self.model,))

	def AddColumn5(self, parent):
		self.CreateColumnFrame(parent)
		effortLogger = EffortLogger(self.model)
		self.AddButton('Settings', self.ShowSettings)
		if self.model.ShowAllButtons:
			self.AddButton('Clear Output', OsOperations.Cls)
		self.AddParallelButton('Clean Active Srcs', self.klaSourceBuilder.CleanSource)
		self.AddParallelButton('Build Active Srcs', self.klaSourceBuilder.BuildSource)
		if self.model.ShowAllButtons:
			self.AddButton('Print mmi.h IDs', self.klaRunner.PrintMissingIds)
			self.AddButton('Effort Log', effortLogger.PrintEffortLogInDetail)
			self.AddButton('Daily Log', effortLogger.PrintDailyLog)

	def CreateColumnFrame(self, parent):
		self.ColFrame = UIFactory.AddFrame(parent, 0, self.Col, sticky='n')
		self.Col += 1
		self.ColInx = 0

	def AddParallelButton(self, label, FunPnt, arg = None, InitFunPnt = None):
		args = (label, FunPnt, arg, InitFunPnt)
		but = UIFactory.AddButton(self.ColFrame, label, self.ColInx, 0,
			self.threadHandler.Start, args, 19)
		self.threadHandler.AddButton(but)
		self.ColInx += 1

	def AddButton(self, label, FunPnt, args = None):
		but = UIFactory.AddButton(self.ColFrame, label, self.ColInx, 0, FunPnt, args, 19)
		self.ColInx += 1

	def ShowSettings(self):
		uiSettings = UISettings(self.parent, self.model, self.VM)
		uiSettings.Show()

class UISettings:
	def __init__(self, parent, model, VM):
		self.Parent = parent
		self.model = model
		self.VM = VM

	def Show(self):
		title = 'Settings'
		self.window = UIFactory.CreateWindow(self.Parent, title, self.model.StartPath)
		self.Row = 2
		self.frame = UIFactory.AddFrame(self.window, 0, 0, 20, 20)
		self.CreateUI(self.frame)
		self.window.protocol('WM_DELETE_WINDOW', self.OnClosing)
		if self.Parent is None:
			self.window.mainloop()

	def OnClosing(self):
		self.model.WriteConfigFile()
		#UIViewModel.RestartApp(self.model)
		if self.Parent is not None:
			self.Parent.deiconify()
			self.Parent = None
			self.VM.UpdateCombo()
		self.window.destroy()

	def AddRow(self):
		self.Row += 1

	def CreateUI(self, parent):
		frame = UIFactory.AddFrame(parent, 0, 0, 0, 0, 2)
		UIFactory.AddButton(frame, 'Add Source', 0, 0, self.AddSource, None, 19)
		UIFactory.AddButton(frame, 'Add Test', 0, 1, self.AddTest, None, 19)
		UIFactory.AddButton(frame, 'Update Kla Runner', 0, 2, self.UpdateKlaRunner, None, 19)
		self.AddSelectFileRow(parent, 'DevEnv.com', 'DevEnvCom')
		self.AddSelectFileRow(parent, 'DevEnv.exe', 'DevEnvExe')
		self.AddSelectPathRow(parent, 'Git Bin', 'GitBin')
		self.AddSelectPathRow(parent, 'VM ware WS', 'VMwareWS')
		self.AddSelectFileRow(parent, 'Effort Log File', 'EffortLogFile')
		self.AddSelectPathRow(parent, 'MMi Config Path', 'MMiConfigPath')
		self.AddSelectPathRow(parent, 'MMi Setups Path', 'MMiSetupsPath')
		self.AddShowAllCheck(parent)

	def AddSelectPathRow(self, parent, label, attrName):
		self.AddSelectItemRow(parent, label, attrName, False)

	def AddSelectFileRow(self, parent, label, attrName):
		self.AddSelectItemRow(parent, label, attrName, True)

	def AddSelectItemRow(self, parent, label, attrName, isFile):
		UIFactory.AddLabel(parent, label, self.Row, 0)
		text = getattr(self.model, attrName)
		if isFile:
			if not os.path.isfile(text):
				print "Given file doesn't exist : " + text
			cmd = self.SelectFile
		else:
			if not os.path.isdir(text):
				print "Given directory doesn't exist : " + text
			cmd = self.SelectPath
		textVar = UIFactory.AddLabel(parent, text, self.Row, 1)[1]
		args = (textVar, attrName)
		UIFactory.AddButton(parent, ' ... ', self.Row, 2, cmd, args)
		self.AddRow()

	def SelectPath(self, textVar, attrName):
		folderSelected = tkFileDialog.askdirectory()
		if len(folderSelected) > 0:
			textVar.set(folderSelected)
			setattr(self.model, attrName, folderSelected)
			print '{} Path changed : {}'.format(attrName, folderSelected)

	def SelectFile(self, textVar, attrName):
		filename = tkFileDialog.askopenfilename(initialdir = "/", title = "Select file")
		if len(filename) > 0:
			textVar.set(filename)
			setattr(self.model, attrName, filename)
			print '{} Path changed : {}'.format(attrName, filename)

	def AddShowAllCheck(self, parent):
		UIFactory.AddLabel(parent, 'Show All Commands', self.Row, 0)
		isChecked = self.model.ShowAllButtons
		self.ChkShowAll = UIFactory.AddCheckBox(parent, isChecked, self.Row, 1, self.OnShowAll)
		self.AddRow()

	def OnShowAll(self):
		self.model.ShowAllButtons = self.ChkShowAll.get()

	def AddSource(self):
		folderSelected = tkFileDialog.askdirectory()
		if len(folderSelected) > 0:
			ConfigEncoder.AddSrc(self.model, folderSelected)
			print 'New source added : ' + folderSelected

	def AddTest(self):
		dir = self.model.Source + '/handler/tests'
		ftypes=[('Script Files', 'Script.py')]
		title = "Select Script file"
		filename = tkFileDialog.askopenfilename(initialdir=dir, filetypes=ftypes, title=title)
		if len(filename) > 10:
			testName = filename[len(dir) + 1: -10]
			self.model.AutoTests.AddTest(testName, [])
			print 'Test Added   : {}'.format(testName)

	def UpdateKlaRunner(self):
		Git.FetchPull('.', False)

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
		PrettyTable(TableFormat().SetNoBorder('')).PrintTable(menuData)

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
			[24, ['Comment VisionSystem', PreTestActions.ModifyVisionSystem, model]],
			[25, ['Copy Mock License', PreTestActions.CopyMockLicense, model]],
			[26, ['Copy xPort xml', PreTestActions.CopyxPortIllumRef, model]],
			[27, ['Print mmi.h IDs', self.klaRunner.PrintMissingIds]],
			[28, ['Copy MmiSaveLogs.exe', PreTestActions.CopyMmiSaveLogExe, model]],
		],[
			[91, ['Build Source ' + activeSrcs, sourceBuilder.BuildSource]],
			[92, ['Clean Source ' + activeSrcs, sourceBuilder.CleanSource]],
			[93, ['Add Test', settings.AddTest]],
			[94, ['Change Test', settings.ChangeTest]],
			[95, ['Change Source', settings.ChangeSource]],
			[96, ['Change MMI Attach', settings.ChangeDebugVision]],
			[97, ['Effort Log', effortLogger.PrintEffortLogInDetail]],
			[98, ['Clear Output', OsOperations.Cls]],
			[99, ['Stop All KLA Apps', TaskMan.StopTasks, True]],
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
		PrettyTable(TableFormat().SetDoubleLineBorder()).PrintTable(menuData)
		userIn = OsOperations.InputNumber('Type the number then press ENTER: ')
		for row in menuData:
			for i in range(1, len(row)):
				if row[i - 1] == userIn:
					return row[i]
		print 'Wrong input is given !!!'
		return [-1]

class KlaRunner:
	RunFromUI = False

	def __init__(self, model):
		self.model = model
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
		#FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))
		fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
		par = 'start python -i ' + fileName
		OsOperations.System(par, 'Starting my.py')

	def GetTestPath(self):
		return os.path.abspath(self.model.Source + '/handler/tests/' + self.model.TestName)

	def OpenTestFolder(self):
		dirPath = self.GetTestPath()
		if not os.path.isdir(dirPath):
			msg = 'Test folder does not exists : ' + dirPath
			print msg
			messagebox.showinfo('KLA Runner', msg)
			return
		subprocess.Popen(['Explorer', dirPath])
		print 'Open directory : ' + dirPath
		OsOperations.Pause(self.model.ClearHistory)

	def CompareMmiReports(self):
		if not os.path.isfile(self.model.BCompare):
			print 'Beyond compare does not exist in the given path : ' + self.model.BCompare
			return
		leftFolder = self.GetTestPath() + '/GoldenReports'
		rightFolder = self.GetTestPath() + '~/_results'
		subprocess.Popen([self.model.BCompare, leftFolder, rightFolder])

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
		PrettyTable(TableFormat().SetSingleLine()).PrintTable(menuData)
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

	def RunHandler(self, doPause = True):
		TaskMan.StopTasks(False)

		config = self.model.Config
		platform = ConfigEncoder.GetPlatform(self.model.Platform)
		handlerPath = '{}/handler/cpp/bin/{}/{}/system'.format(self.model.Source, platform, config)
		consoleExe = handlerPath + '/console.exe'
		testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'

		platform = ConfigEncoder.GetPlatform(self.model.Platform, True)
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
		TaskMan.StopTask('MMi.exe')
		VMWareRunner.RunSlots(self.model)

		if fromSrc:
			PreTestActions.CopyMockLicense(self.model, False, False) # Do we need this
		mmiPath = PreTestActions.CopyMockLicense(self.model, fromSrc, False)
		PreTestActions.CopyxPortIllumRef(self.model)

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
	def OpenLocalDif(cls, model):
		par = [ 'TortoiseGitProc.exe', '/command:diff', '/path:' + model.Source + '' ]
		print 'subprocess.Popen : ' + str(par)
		subprocess.Popen(par)
		OsOperations.Pause()

class TaskMan:
	copyIllumTimer = None

	@classmethod
	def StopTasks(cls, doPause):
		cls.StopTimers()
		for exeName in [
			'Mmi.exe',
			'Mmi_spc.exe',
			'console.exe',
			'CIT100Simulator.exe',
			'HostCamServer.exe',
			'Ves.exe',
		]:
			TaskMan.StopTask(exeName)
		TaskMan.StopTask('python.exe', os.getpid())
		OsOperations.Pause(doPause)

	@classmethod
	def StopTask(cls, exeName, exceptProcId = -1):
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
	def StopTimers(cls):
		if cls.copyIllumTimer is not None:
			cls.copyIllumTimer.stop()
			cls.copyIllumTimer = None

class VMWareRunner:
	@classmethod
	def RunSlots(cls, model):
		vMwareWS = model.VMwareWS
		slots = model.slots
		if len(slots) == 0:
			cls.ShowMessage('Please select necessary slot(s).')
			return False
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
				msg = 'Please start ' + slotName
				cls.ShowMessage(msg)
				print slotName + ' : Started.'
		return True

	@classmethod
	def ShowMessage(cls, msg):
		print msg
		if KlaRunner.RunFromUI:
			messagebox.showinfo('KLA Runner', msg)
		else:
			os.system('PAUSE')

class PreTestActions:
	@classmethod
	def CopyMockLicense(cls, model, toSrc = True, doPause = True):
		args = (model.Source, model.Platform, model.Config)
		if toSrc:
			mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(*args))
		else:
			mmiPath = 'C:/icos'
		licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
		licenseFile = os.path.abspath(licencePath.format(*args))
		FileOperations.Copy(licenseFile, mmiPath)
		OsOperations.Pause(doPause and model.ClearHistory)
		return mmiPath

	@classmethod
	def CopyxPortIllumRef(cls, model, doPause = False, delay = False):
		src = model.StartPath + '\\xPort_IllumReference.xml'
		des = 'C:/icos/xPort/'
		if delay:
			TaskMan.StopTimers()
			TaskMan.copyIllumTimer = FileOperations.Copy(src, des, 8, 3)
		else:
			FileOperations.Copy(src, des)
		OsOperations.Pause(doPause)

	@classmethod
	def CopyMmiSaveLogExe(cls, model):
		destin = os.path.abspath("{}/handler/tests/{}~\Icos".format(
			model.Source, model.TestName))
		src = os.path.abspath('{}/mmi/mmi/Bin/{}/{}/MmiSaveLogs.exe'.format(
			model.Source, model.Platform, model.Config))
		FileOperations.Copy(src, destin)

	@classmethod
	def ModifyVisionSystem(cls, model, doPause = True):
		line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
		oldLine = ' ' + line
		newLine = ' #' + line
		fileName = os.path.abspath(model.Source + '/libs/testing/visionsystem.py')
		with open(fileName) as f:
			oldText = f.read()
		if oldLine in oldText:
			newText = oldText.replace(oldLine, newLine)
			with open(fileName, "w") as f:
				f.write(newText)
			print fileName + ' has been modified.'
		else:
			print fileName + ' had already been modified.'
		OsOperations.Pause(doPause and model.ClearHistory)

class AutoTestRunner:
	def __init__(self, model):
		self.model = model
		self.lastSrc = None

	def InitAutoTest(self):
		if self.lastSrc is None:
			self.lastSrc = self.model.Source
		elif self.lastSrc != self.model.Source:
			msg = 'Test has already been executed with different source. So please restart KLA Runner.'
			if KlaRunner.RunFromUI:
				messagebox.showinfo('KLA Runner', msg)
			else:
				print msg
			return False
		TaskMan.StopTasks(False)
		return VMWareRunner.RunSlots(self.model)

	def RunAutoTest(self, startUp, callInit = True):
		if callInit:
			self.InitAutoTest()
		PreTestActions.ModifyVisionSystem(self.model, False)
		#PreTestActions.CopyxPortIllumRef(self.model, False, True)
		#FileOperations.Copy(self.model.StartPath + '/Profiles', 'C:/icos/Profiles', 8, 3)
		os.chdir(self.model.StartPath)

		# After swtiching sources with different configurations, we have to remove myconfig.py
		FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))

		libsPath = AutoTestRunner.UpdateLibsTestingPath(self.model.Source)
		tests = AutoTestRunner.SearchInTests(libsPath, self.model.TestName)
		if len(tests) == 0:
			return
		import my
		#print 'Module location of my : ' + my.__file__
		my.c.startup = startUp
		my.c.debugvision = self.model.DebugVision
		my.c.copymmi = self.model.CopyMmi
		my.c.mmiBuildConfiguration = ConfigEncoder.GetBuildConfig(self.model)
		my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
		my.c.platform = self.model.Platform
		my.c.mmiConfigurationsPath = self.model.MMiConfigPath
		my.c.mmiSetupsPath = self.model.MMiSetupsPath
		my.run(tests[0][0])
		print 'Completed Auto Test : {} : {}'.format(tests[0][0], tests[0][1])

	@classmethod
	def SearchInTests(cls, libsPath, text):
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
		slots = OsOperations.Input('Enter slots : ')
		index = self.model.AutoTests.AddTest(testName, slots)
		self.model.UpdateTest(index, True)
		OsOperations.Pause(self.model.ClearHistory)

	def ChangeSource(self):
		heading, data = self.klaRunner.GetSourceInfo(None)
		index = self.SelectOption(heading, data, self.model.SrcIndex)
		self.model.SrcCnf.UpdateSource(index, True)
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
		PrettyTable(TableFormat().SetSingleLine()).PrintTable(data)
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
		if OsOperations.Input(question) == 'Yes':
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
		for srcSet in self.VerifySources('cleaning'):
			src = srcSet[0]
			cnt = len(Git.ModifiedFiles(self.model.Source))
			if cnt > 0:
				Git.Commit(self.model, 'Temp')
			print 'Cleaning files in ' + src
			self.DeleteAllGitIgnoreFiles(src)
			with open(src + '/.gitignore', 'w') as f:
				f.writelines(str.join('\n', excludeDirs))
			Git.Clean(src, '-fd')
			print 'Reseting files in ' + src
			Git.ResetHard(src)
			if cnt > 0:
				Git.RevertLastCommit(self.model)
			print 'Cleaning completed for ' + src
		OsOperations.Pause(self.model.ClearHistory)

	def DeleteAllGitIgnoreFiles(self, dirName):
		os.remove('{}/.gitignore'.format(dirName))
		for root, dirs, files in os.walk(dirName):
			if '.gitignore' in files and '.git' not in files:
				os.remove('{}/.gitignore'.format(root))

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
				platform = ConfigEncoder.GetPlatform(srcPlatform, isSimulator)
				BuildConf = config + '|' + platform
				outFile = os.path.abspath(source + '/Out_' + self.SlnNames[inx]) + '.txt'

				buildLoger.StartSolution(sln, self.SlnNames[inx], config, platform)
				params = [self.model.DevEnvCom, slnFile, '/build', BuildConf, '/out', outFile]
				OsOperations.Popen(params, buildLoger.PrintMsg)
				buildLoger.EndSolution()
			buildLoger.EndSource(source)
		OsOperations.Pause(self.model.ClearHistory)

	def OpenSolution(self, index):
		fileName = self.model.Source + self.Solutions[index]
		param = [
			self.model.DevEnvExe,
			fileName
		]
		subprocess.Popen(param)
		print 'Open solution : ' + fileName
		if self.model.Config is not 'Debug' or self.model.Platform is not 'Win32':
			msg = 'Please check configuration and platform in Visual Studio'
			KlaSourceBuilder.ShowInfo('Visual Studio', msg, self.model.ClearHistory)
		else:
			OsOperations.Pause(self.model.ClearHistory)

	@classmethod
	def ShowInfo(cls, caption, msg, doPause):
		if KlaRunner.RunFromUI:
			messagebox.showinfo(caption, msg)
		else:
			print msg
			OsOperations.Pause(doPause)

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
		table = PrettyTable(TableFormat().SetSingleLine()).ToString(self.logDataTable)
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
		if not os.path.exists(fileName):
			print "File doesn't exist : " + fileName
			return []
		f = open(fileName, 'rb')
		data = f.read()
		f.close()
		return data.decode(utf).splitlines()

	@classmethod
	def Append(cls, fileName, message):
		if not os.path.exists(fileName):
			print "File doesn't exist : " + fileName
			return
		with open(fileName, 'a') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def Write(cls, fileName, message):
		with open(fileName, 'w') as f:
			 f.write((message + '\n').encode('utf8'))

	@classmethod
	def Delete(cls, fileName):
		if os.path.isfile(fileName):
			os.remove(fileName)
			print 'File deleted : ' + fileName
		else:
			print 'Not found to delete : ' + fileName

	@classmethod
	def Copy(cls, src, des, initWait = 0, inter = 0):
		if initWait == 0 and inter == 0:
			cls._Copy(src, des, inter)
		else:
			print 'Try to Copy({},{}) after {} seconds.'.format(src, des, initWait)
			copyTimer = MyTimer(cls._Copy, initWait, inter, src, des)
			copyTimer.start()
			return copyTimer

	@classmethod
	def _Copy(cls, src, des, inter = 0):
		while not os.path.exists(des):
			if inter > 0:
				print '({}) not existing. Try to Copy({}) after {} seconds.'.format(des, src, inter)
				time.sleep(inter)
			else:
				print 'Wrong input - Destination folder not existing : ' + des
				return False
		if os.path.isfile(src):
			OsOperations.System('COPY /Y "' + src + '" "' + des + '"')
		elif os.path.isdir(src):
			OsOperations.System('XCOPY /S /Y "' + src + '" "' + des + '"')
		else:
			print 'Wrong input - Neither file nor directory : ' + src
			return False
		return True

class MyTimer(threading.Thread):
	def __init__(self, target, initWait = 0, inter = 0, *args):
		super(MyTimer, self).__init__()
		self._stop = threading.Event()
		self.target = target
		self.initWait = initWait
		self.interval = inter
		self.args = args

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def run(self):
		if self.initWait > 0:
			time.sleep(self.initWait)
		while True:
			if self.stopped():
				return
			if self.target(*self.args):
				return
			time.sleep(self.interval)

class OsOperations:
	@classmethod
	def Cls(cls):
		os.system('cls')

	@classmethod
	def System(cls, params, message = None):
		if message is None:
			print params
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
		userIn = cls.Input(message)
		while True:
			if userIn != '':
				return int(userIn)
			userIn = raw_input()

	@classmethod
	def FlushInput(cls):
		while msvcrt.kbhit():
			msvcrt.getch(),

	@classmethod
	def Input(cls, message):
		cls.FlushInput()
		return raw_input(message)

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

class TableFormat:
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
	def PrintArray(cls, arr, colCnt):
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
		actual = PrettyTable(TableFormat().SetSingleLine()).ToString(data)
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
		actual = PrettyTable(TableFormat().SetDoubleLineBorder()).ToString(data)
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
		actual = PrettyTable(TableFormat().SetDoubleLine()).ToString(data)
		#print actual
		Test.AssertMultiLines(actual, expected)

	def NoBorder(self):
		data = [['ColA', 'Col B', 'Col C'], ['-'], ['KLA', 2, True], ['ICOS', 12345, False]]
		expected = u'''
ColA,Col B,Col C
KLA ,  2  ,True 
ICOS,12345,False
'''[1:]
		actual = PrettyTable(TableFormat().SetNoBorder(',')).ToString(data)
		#print actual
		Test.AssertMultiLines(actual, expected)

class Git:
	@classmethod
	def GetBranch(cls, source):
		#print 'Git.GetBranch : ' + source
		params = ['git', '-C', source, 'branch']
		output = OsOperations.ProcessOpen(params)
		isCurrent = False
		for part in output.split():
			if isCurrent:
				return part
			if part == '*':
				isCurrent = True

	@classmethod
	def Git(cls, source, cmd):
		OsOperations.Call('git -C {} {}'.format(source, cmd))

	@classmethod
	def ModifiedFiles(cls, source):
		params = ['git', '-C', source, 'status', '-s']
		return OsOperations.ProcessOpen(params).split('\n')[:-1]

	@classmethod
	def Clean(cls, source, options):
		cls.Git(source, 'clean ' + options)

	@classmethod
	def ResetHard(cls, source):
		cls.Git(source, 'reset --hard')

	@classmethod
	def SubmoduleUpdate(cls, model):
		cls.Git(model.Source, 'submodule update --init --recursive')
		cls.Git(model.Source, 'submodule foreach git reset --hard') # It seems this is not working

	@classmethod
	def OpenGitGui(cls, model):
		param = [ 'git-gui', '--working-dir', model.Source ]
		print 'Staring Git GUI'
		subprocess.Popen(param)
		OsOperations.Pause()

	@classmethod
	def OpenGitBash(cls, model):
		par = 'start {}sh.exe --cd={}'.format(model.GitBin, model.Source)
		OsOperations.System(par, 'Staring Git Bash')
		OsOperations.Pause()

	@classmethod
	def FetchPull(cls, model, submoduleUpdate=True):
		cls.Git(model.Source, 'pull')
		if submoduleUpdate:
			Git.SubmoduleUpdate(model)
		print 'Git fetch and pull completed.'
		OsOperations.Pause()

	@classmethod
	def GetHash(cls):
		str = OsOperations.ProcessOpen('git describe --always')
		return re.sub('\W+', '', str)

	@classmethod
	def Commit(cls, model, msg):
		cls.Git(model.Source, 'add -A')
		cls.Git(model.Source, 'commit -m "' + msg + '"')

	@classmethod
	def RevertLastCommit(cls, model):
		cls.Git(model.Source, 'reset --mixed HEAD~1')

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
	def ContainsInArray(cls, str, strArray):
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

class DateTimeOps:
	@classmethod
	def IsSameDate(cls, datetime1, datetime2, dayStarts):
		if datetime1 is None or datetime2 is None:
			return False
		a1 = datetime1 - dayStarts
		b1 = datetime2 - dayStarts
		return a1.day == b1.day and a1.month == b1.month and a1.year == b1.year

	@classmethod
	def Strftime(cls, myTimeDelta, format):
		hours, remainder = divmod(myTimeDelta.total_seconds(), 3600)
		minutes, seconds = divmod(remainder, 60)
		return format.format(int(hours), int(minutes), int(seconds))

class EffortReader:
	def __init__(self, model):
		self.model = model
		self.LogFileEncode = 'UTF-16'
		self.DTFormat = self.model.DateFormat + ' %H:%M:%S'
		self.DayStarts = timedelta(hours=4) # 4am

	def ReadFile(self):
		logFile = self.model.EffortLogFile
		self.content = []
		for line in FileOperations.ReadLine(logFile, self.LogFileEncode):
			if line[:7] == 'Current':
				continue
			lineParts = self.FormatText(line).split('$')
			if len(lineParts) > 2:
				self.content.append(lineParts)
			else:
				print 'Error: ' + line

	def GetDetailedEfforts(self, date):
		if len(self.content) is 0:
			return
		dictAppNameToTime = NumValDict()
		lastDt = None
		totalTime = timedelta()
		for lineParts in self.content:
			dt = datetime.strptime(lineParts[0], self.DTFormat)
			if not DateTimeOps.IsSameDate(dt, date, self.DayStarts):
				continue
			ts = (dt - lastDt) if lastDt is not None else (dt-dt)
			txt = self.PrepareDescription(lineParts[1], lineParts[2])
			dictAppNameToTime.Add(txt, ts)
			lastDt = dt
			totalTime += ts
		return dictAppNameToTime, totalTime

	def GetConsolidatedTime(self):
		if len(self.content) is 0:
			return
		lastDt = None
		actualTime = None
		date = None
		data = []
		def AddRow(d1, t1):
			formattedTime = DateTimeOps.Strftime(t1, '{:02}:{:02}')
			data.append([d1, formattedTime])
		for lineParts in self.content:
			dt = datetime.strptime(lineParts[0], self.DTFormat)
			if DateTimeOps.IsSameDate(dt, date, self.DayStarts):
				ts = dt - lastDt
				if len(lineParts[1] + lineParts[2]) > 0:
					actualTime += ts
			else:
				if date is not None:
					AddRow(formattedDay, actualTime)
				date = dt
				formattedDay = dt.strftime(self.model.DateFormat)
				actualTime = timedelta()
			lastDt = dt
		AddRow(formattedDay, actualTime)
		return data

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

	def CheckApplication(self):
		if len(OsOperations.GetProcessIds('EffortCapture_2013.exe')) > 0:
			print 'Effort logger is running.'
		else:
			print 'Effort logger is not running !'

class EffortLogger:
	def __init__(self, model):
		self.model = model
		self.ColWidth = 80
		self.MinMinutes = 3
		self.MinTime = timedelta(minutes=self.MinMinutes)
		self.ShowPrevDaysLogs = 1

	def PrintEffortLogInDetail(self):
		reader = EffortReader(self.model)
		reader.ReadFile()
		for i in range(self.ShowPrevDaysLogs, 0, -1):
			prevDay = datetime.now() - timedelta(days=i)
			formattedDay = prevDay.strftime(self.model.DateFormat)
			self.PrintEffortTable(prevDay, formattedDay, reader)
		today = datetime.now()
		self.PrintEffortTable(today, 'Today', reader)
		reader.CheckApplication()
		OsOperations.Pause()

	def PrintEffortTable(self, date, message, reader):
		dictAppNameToTime, totalTime = reader.GetDetailedEfforts(date)
		if dictAppNameToTime is None:
			return
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
		menuData += [['Actual Time', totalTime - dollarTime]]
		table = PrettyTable(TableFormat().SetSingleLine()).ToString(menuData)
		#table = datetime.now().strftime('%Y %b %d %H:%M:%S\n') + table
		#FileOperations.Append(logFile + '.txt', table)
		print table,

	def PrintDailyLog(self):
		reader = EffortReader(self.model)
		reader.ReadFile()
		data = reader.GetConsolidatedTime()
		if data is None:
			return
		effortData = [['Date', 'Actual Time'], ['-']] + data
		table = PrettyTable(TableFormat().SetSingleLine()).ToString(effortData)
		print table,
		reader.CheckApplication()

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

	def TestTrim(self):
		Test.Assert(self.EL.Trim('India is my country', 10), 'Indi...try')
		Test.Assert(self.EL.Trim('India is my country', 15), 'India ...untry')

class Test:
	_ok = 0
	_notOk = 0

	@classmethod
	def AssertMultiLines(cls, actual, expected, level = 0):
		isEqual = True
		clsName, funName = cls._GetClassMethod(level)
		for lineNum,(act,exp) in enumerate(itertools.izip(actual.splitlines(), expected.splitlines()), 1):
			if act != exp:
				message = '{}.{} Line # {}'.format(clsName, funName, lineNum)
				cls._Print(act, exp, message)
				return
		message = '{}.{}'.format(clsName, funName)
		cls._Print(True, True, message)

	@classmethod
	def Assert(cls, actual, expected, message = '', level = 0):
		clsName, funName = cls._GetClassMethod(level)
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
	def _GetClassMethod(cls, level):
		stack = inspect.stack()
		clsName = stack[2 + level][0].f_locals['self'].__class__.__name__
		funName = stack[2 + level][0].f_code.co_name
		return (clsName, funName)

	@classmethod
	def PrintResults(cls):
		print
		print 'Tests OK     : ' + str(cls._ok)
		print 'Tests NOT OK : ' + str(cls._notOk)
		print 'Total Tests  : ' + str(cls._ok + cls._notOk)

class TestSourceCode:
	def __init__(self):
		self.TestClassLineCount()

	def TestClassLineCount(self):
		data = []
		for name, obj in inspect.getmembers(sys.modules[__name__]):
			if inspect.isclass(obj) and str(obj)[:8] == '__main__':
				lineCnt = len(inspect.getsourcelines(obj)[0])
				data.append([name, lineCnt])
		sorted(data, key=lambda x: x[1])
		for item in data:
			#Test.Assert(item[1] < 100, True, '{:20} {}'.format(item[0], item[1]))
			#print '{:20} {}'.format(item[0], item[1])
			if item[1] > 100:
				Test.Assert(item[1], '< 100', 'Exceeds line count : {}'.format(item[0]))

class UnitTestsRunner:
	def Run(self):
		TestNumValDict()
		TestEffortLogger()
		TestPrettyTable()
		TestSourceCode()
		TestKlaRunnerIni()

		Test.PrintResults()

class ConfigEncoder:
	Configs = ['Debug', 'Release']
	Platforms = ['Win32', 'x64']

	@classmethod
	def DecodeSource(cls, srcStr):
		source = srcStr[4:]
		config = cls.Configs[srcStr[0] == 'R']
		platform = cls.Platforms[srcStr[1:3] == '64']
		return (source, config, platform)

	@classmethod
	def EncodeSource(cls, srcSet):
		return srcSet[1][0] + srcSet[2][-2:] + ' ' + srcSet[0]

	@classmethod
	def GetPlatform(cls, platform, isSimulator = False):
		if isSimulator and 'Win32' == platform:
			platform = 'x86'
		return platform

	@classmethod
	def GetBuildConfig(cls, model):
		debugConfigSet = ('debugx64', 'debug')
		releaseConfigSet = ('releasex64', 'release')
		configSet = (debugConfigSet, releaseConfigSet)[model.Config == cls.Configs[1]]
		# releasex64 is not working
		# return configSet[model.Platform == cls.Platforms[0]]
		return configSet[1]

	@classmethod
	def AddSrc(cls, model, newSrcPath):
		for srcSet in model.Sources:
			if newSrcPath == srcSet[0]:
				return
		model.Sources.append((newSrcPath, cls.Configs[0], cls.Platforms[0]))
		if model.SrcIndex < 0:
			model.SrcIndex = 0

class AutoTestModel:
	def __init__(self):
		self.Tests = []

	def Read(self, testArray):
		self.Tests = []
		for item in testArray:
			nameSlot = self.Encode(item)
			if nameSlot is not None:
				self.Tests.append(nameSlot)

	def Write(self):
		return [self.Decode(item[0], item[1]) for item in self.Tests]

	def IsValidIndex(self, index):
		return index >= 0 and index < len(self.Tests)

	def GetNames(self):
		return [item[0] for item in self.Tests]

	def GetNameSlots(self, index):
		return self.Tests[index]

	def SetNameSlots(self, index, name, slots):
		self.Tests[index] = [name, slots]

	def Contains(self, testName):
		for inx, item in self.Tests:
			if testName in item[0]:
				return inx

	def AddTest(self, testName, slots):
		for item in self.Tests:
			if item[0] == testName:
				return -1
		self.Tests.append([testName, slots])
		return len(self.Tests) - 1

	def Encode(self, testNameSlots):
		parts = testNameSlots.split()
		if len(parts) > 1:
			return (parts[0], map(int, parts[1].split('_')))
		elif len(parts) > 0:
			return (parts[0], [])

	def Decode(self, testName, slots):
		slotStrs = [str(slot) for slot in slots]
		return '{} {}'.format(testName, '_'.join(slotStrs))

class ConfigInfo:
	def __init__(self, fileName):
		self.FileName = fileName

	def Read(self, model):
		if not os.path.exists(self.FileName):
			print "File doesn't exist : " + self.FileName
			return
		with open(self.FileName) as f:
			_model = json.load(f)

		try:
			model.Sources = [ConfigEncoder.DecodeSource(item) for item in _model['Sources']]
			model.SrcCnf.UpdateSource(_model['SrcIndex'], False)
			model.AutoTests.Read(_model['Tests'])
			if not model.UpdateTest(_model['TestIndex'], False):
				model.TestIndex = 0
			model.ActiveSrcs = _model['ActiveSrcs']
			model.DevEnvCom = _model['DevEnvCom']
			model.DevEnvExe = _model['DevEnvExe']
			model.GitBin = _model['GitBin']
			model.VMwareWS = _model['VMwareWS']
			model.EffortLogFile = _model['EffortLogFile']
			model.BCompare = _model['BCompare']
			model.DateFormat = _model['DateFormat']
			model.MMiConfigPath = _model['MMiConfigPath']
			model.MMiSetupsPath = _model['MMiSetupsPath']
			model.DebugVision = _model['DebugVision']
			model.CopyMmi = _model['CopyMmi']
			model.TempDir = _model['TempDir']
			model.LogFileName = _model['LogFileName']
			model.MenuColCnt = _model['MenuColCnt']
			model.MaxSlots = _model['MaxSlots']
			model.ClearHistory = _model['ClearHistory']
			model.ShowAllButtons = _model['ShowAllButtons']
		except:
			print("Unexpected error:", sys.exc_info()[0])

		model.MMiConfigPath = model.MMiConfigPath.replace('/', '\\')

	def Write(self, model):
		_model = OrderedDict()
		_model['Sources'] = [ConfigEncoder.EncodeSource(item) for item in model.Sources]
		_model['SrcIndex'] = model.SrcIndex
		_model['ActiveSrcs'] = model.ActiveSrcs
		_model['Tests'] = model.AutoTests.Write()
		_model['TestIndex'] = model.TestIndex
		_model['DevEnvCom'] = model.DevEnvCom
		_model['DevEnvExe'] = model.DevEnvExe
		_model['GitBin'] = model.GitBin
		_model['VMwareWS'] = model.VMwareWS
		_model['EffortLogFile'] = model.EffortLogFile
		_model['BCompare'] = model.BCompare
		_model['DateFormat'] = model.DateFormat
		_model['MMiConfigPath'] = model.MMiConfigPath
		_model['MMiSetupsPath'] = model.MMiSetupsPath
		_model['DebugVision'] = model.DebugVision
		_model['CopyMmi'] = model.CopyMmi
		_model['TempDir'] = model.TempDir
		_model['LogFileName'] = model.LogFileName
		_model['MenuColCnt'] = model.MenuColCnt
		_model['MaxSlots'] = model.MaxSlots
		_model['ClearHistory'] = model.ClearHistory
		_model['ShowAllButtons'] = model.ShowAllButtons

		with open(self.FileName, 'w') as f:
			json.dump(_model, f, indent=3)

class SourceConfig:
	def __init__(self, model):
		self.model = model

	def UpdateSource(self, index, writeToFile):
		if index < 0 or index >= len(self.model.Sources):
			return False
		if self.model.SrcIndex == index:
			return False
		self.model.SrcIndex = index
		self.model.Source, self.model.Config, self.model.Platform = self.model.Sources[self.model.SrcIndex]
		self.model.Branch = Git.GetBranch(self.model.Source)
		if writeToFile:
			self.model.WriteConfigFile()
		return True

class TestKlaRunnerIni:
	def __init__(self):
		self.model = Model()
		self.model.ReadConfigFile()
		self.Source()
		self.AutoTest()
		self.FileExists()
		self.DirectoryExists()

	def Source(self):
		for srcSet in self.model.Sources:
			src = srcSet[0]
			Test.Assert(os.path.isdir(src), True, 'Directory {} exists.'.format(src))
		self.TestIndex(self.model.Sources, self.model.SrcIndex, 'Index')

	def AutoTest(self):
		self.TestIndex(self.model.AutoTests.Tests, self.model.TestIndex, 'Index')

	def TestIndex(self, list, index, message):
		isValidIndex = index >= 0 and index < len(list)
		Test.Assert(isValidIndex, True, message, 1)

	def FileExists(self):
		Test.Assert(os.path.isfile(self.model.DevEnvCom), True, 'DevEnv.com')
		Test.Assert(os.path.isfile(self.model.DevEnvExe), True, 'DevEnv.exe')
		Test.Assert(os.path.isfile(self.model.EffortLogFile), True, 'EffortLogFile')

	def DirectoryExists(self):
		Test.Assert(os.path.isdir(self.model.GitBin), True, 'GitBin')
		Test.Assert(os.path.isdir(self.model.VMwareWS), True, 'VMwareWS')
		Test.Assert(os.path.isdir(self.model.MMiConfigPath), True, 'MMiConfigPath')
		Test.Assert(os.path.isdir(self.model.MMiSetupsPath), True, 'MMiSetupsPath')

class Model:
	def __init__(self):
		self.StartPath = os.path.dirname(os.path.abspath(__file__))
		self.ConfigInfo = ConfigInfo(self.StartPath + '\\KlaRunner.ini')
		self.AutoTests = AutoTestModel()
		self.SrcCnf = SourceConfig(self)

		self.SrcIndex = -1
		self.TestIndex = -1
		self.Sources = []
		self.ActiveSrcs = []
		self.Source = ''
		self.Branch = ''
		self.TestName = ''
		self.slots = []
		self.Config = ConfigEncoder.Configs[0]
		self.Platform = ConfigEncoder.Platforms[0]
		
		self.DevEnvCom = 'C:/Program Files (x86)/Microsoft Visual Studio 12.0/Common7/IDE/devenv.com'
		self.DevEnvExe = 'C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional/Common7/IDE/devenv.exe'
		self.GitBin = 'C:/Progra~1/Git/bin/'
		self.VMwareWS = 'C:/Program Files (x86)/VMware/VMware Workstation/'
		self.EffortLogFile = 'D:/QuEST/Tools/EffortCapture_2013/timeline.log'
		self.BCompare = 'C:/Program Files (x86)/Beyond Compare 4/BCompare.exe'
		self.DateFormat = '%d-%b-%Y'
		self.MMiConfigPath = 'D:/'
		self.MMiSetupsPath = 'D:/MmiSetups'
		self.DebugVision = False
		self.CopyMmi = True
		self.TempDir = 'bin'
		self.LogFileName = 'bin/Log.txt'
		self.MenuColCnt = 4
		self.MaxSlots = 8
		self.ClearHistory = False
		self.ShowAllButtons = False

	def ReadConfigFile(self):
		self.ConfigInfo.Read(self)

	def WriteConfigFile(self):
		self.ConfigInfo.Write(self)

	def UpdateTest(self, index, writeToFile):
		if not self.AutoTests.IsValidIndex(index):
			return False
		if self.TestIndex == index:
			return False
		self.TestIndex = index
		[self.TestName, self.slots] = self.AutoTests.GetNameSlots(self.TestIndex)
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

	def GetLibsTestPath(self):
		return self.Source + '/libs/testing'

def main():
	if (len(sys.argv) == 2):
		param1 = sys.argv[1].lower()
		if param1 == 'test':
			UnitTestsRunner().Run()
		elif param1 == 'ui':
			UI().Run()
	elif (__name__ == '__main__'):
		model = Model()
		model.ReadConfigFile()
		KlaRunner(model).Run()

main()
print 'Have a nice day...'
