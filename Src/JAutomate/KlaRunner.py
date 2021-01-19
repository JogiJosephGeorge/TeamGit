# coding=utf-8
import ctypes
from datetime import datetime
from xml.dom import minidom
import time
import os
import re
import subprocess
import sys
import threading
import Tkinter as tk
import ttk
import tkFileDialog

from Common.Git import Git
from Common.FileOperations import FileOperations
from Common.Logger import Logger
from Common.MessageBox import MessageBox
from Common.OsOperations import OsOperations
from Common.PrettyTable import  TableFormat, PrettyTable
from KLA.LicenseConfigWriter import LicenseConfigWriter
from Model.Model import ConfigEncoder, Model
from QuEST.EffortLog import EffortLogger

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
    def AddButton(cls, parent, text, r, c, cmd, args = None, width = 0):
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
    def AddLabel(cls, parent, text, r, c, width = 0, anchor='w'):
        labelVar = tk.StringVar()
        labelVar.set(text)
        label = tk.Label(parent, textvariable=labelVar, anchor=anchor)
        if width > 0:
            label['width'] = width
        label.grid(row=r, column=c, sticky='w')
        return labelVar

    @classmethod
    def AddEntry(cls, parent, cmd, r, c, width = 0):
        entry = tk.Entry(parent, width=width)
        entry.grid(row=r, column=c, sticky='w')
        reg = parent.register(cmd)
        entry.config(validate='key', validatecommand=(reg, '%P'))

    @classmethod
    def AddCombo(cls, parent, values, inx, r, c, cmd, arg = None, width = 0):
        combo = ttk.Combobox(parent)
        combo['state'] = 'readonly'
        combo['values'] = values
        if inx >= 0 and inx < len(values):
            combo.current(inx)
        if arg is None:
            action = cmd
        else:
            action = lambda _ : cmd(arg)
        if width > 0:
            combo['width'] = width
        combo.grid(row=r, column=c)
        combo.bind("<<ComboboxSelected>>", action)
        return combo

    @classmethod
    def AddCheckBox(cls, parent, text, defVal, r, c, cmd, args = None, sticky='w'):
        chkValue = tk.BooleanVar()
        chkValue.set(defVal)
        if args is None:
            action = cmd
        else:
            action = lambda: cmd(*args)
        chkBox = tk.Checkbutton(parent, var=chkValue, command=action, text=text)
        chkBox.grid(row=r, column=c, sticky=sticky)
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
    def Run(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raw_input('Please run this application with Administrator privilates')
            #os.system('PAUSE')
            return
        self.model = Model()
        self.VM = UIViewModel(self.model)
        self.model.ReadConfigFile()
        if not os.path.exists(self.model.ConfigInfo.FileName):
            UISourceSelector(None, self.model).Show()
            return
        fileName = self.model.StartPath + '/' + self.model.LogFileName
        Logger.Init(fileName)
        klaRunner = KlaRunner(self.model)
        vsSolutions = VisualStudioSolutions(self.model)
        threadHandler = ThreadHandler()
        testRunner = AutoTestRunner(self.model, self.VM)

        title = 'KLA Application Runner'
        self.window = UIFactory.CreateWindow(None, title, self.model.StartPath)
        self.mainFrame = UIFactory.AddFrame(self.window, 0, 0, 20, 0)
        self.Row = 0
        UISourceGroup(self, klaRunner, vsSolutions, threadHandler)
        UITestGroup(self, klaRunner, vsSolutions, threadHandler, testRunner)
        UIMainMenu(self, klaRunner, vsSolutions, threadHandler, testRunner)

        self.window.after(200, self.LazyInit)
        self.window.mainloop()

    def LazyInit(self):
        title = 'KLA Application Runner ' + self.GetVersion()
        self.window.title(title)
        self.model.Branch = Git.GetBranch(self.model.Source)
        self.VM.lblBranch.set(self.model.Branch)
        Git.GitSilent('.', 'pull')
        print title

    def GetVersion(self):
        commitCnt = OsOperations.ProcessOpen('git rev-list --all --count')
        revision = int(re.sub('\W+', '', commitCnt)) - 165
        desStr = OsOperations.ProcessOpen('git describe --always')
        hash = re.sub('\W+', '', desStr)
        return '1.3.{}.{}'.format(revision, hash)

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddSeparator(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, ' ', 0, 0)

class UISourceGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler):
        self.window = UI.window
        self.model = UI.model
        self.VM = UI.VM
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler

        row1 = UI.AddRow()
        UIFactory.AddLabel(row1, 'Source', 0, 0)
        self.AddSourceDescription(row1, 0, 1)
        UIFactory.AddButton(row1, ' ... ', 0, 2, self.OnSelectSource)
        self.VM.lblBranch = UIFactory.AddLabel(row1, self.model.Branch, 0, 3)

    def AddSourceDescription(self, parent, r, c):
        source = self.VM.GetSource()
        self.VM.lblSource = UIFactory.AddLabel(parent, source, r, c)

    def OnSelectSource(self):
        UISourceSelector(self.window, self.model, self.klaRunner, self.vsSolutions, self.VM, self.threadHandler).Show()

    def AddParallelButton(self, label, FunPnt, InitFunPnt):
        self.threadHandler.AddButton(self.frame, label, 0, self.ColInx, FunPnt, None, InitFunPnt, 0)
        self.ColInx += 1

class UITestGroup:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, tr):
        self.window = UI.window
        self.parent = UI.window
        self.model = UI.model
        self.VM = UI.VM
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.threadHandler = threadHandler
        self.tr = tr

        UI.AddSeparator()

        row1 = UI.AddRow()
        self.AddRunTestButton(row1, 0, 0)
        self.AddTestCombo(row1, 0, 1)
        self.AddAutoTestSettings(row1, 0, 2)

        row2 = UI.AddRow()
        self.AddStartOnly(row2, 0, 0)
        self.AddAttachMmi(row2, 0, 1)
        UIFactory.AddButton(row2, 'Open Test Folder', 0, 2, self.klaRunner.OpenTestFolder)
        UIFactory.AddButton(row2, 'Compare Test Results', 0, 3, self.klaRunner.CompareMmiReports)

        row3 = UI.AddRow()
        UIFactory.AddLabel(row3, 'Slots', 0, 0)
        self.AddSlots(row3, 0, 1)
        UIFactory.AddButton(row3, 'Run Slots', 0, 2, VMWareRunner.RunSlots, (self.model,))
        UIFactory.AddButton(row3, 'Test First Slot Selected', 0, 4, VMWareRunner.TestSlots, (self.model,))

    def AddRunTestButton(self, parent, r, c):
        label = self.GetLabel()
        self.RunTestBut = self.threadHandler.AddButton(parent, label, r, c, self.tr.RunAutoTest, None, self.tr.InitAutoTest)

    def GetLabel(self):
        return 'Start Test' if self.model.StartOnly else 'Run Test'

    def AddTestCombo(self, parent, r, c):
        testNames = self.model.AutoTests.GetNames()
        self.VM.cmbTest = UIFactory.AddCombo(parent, testNames, self.model.TestIndex, r, c, self.VM.OnTestChanged, None, 70)

    def AddAutoTestSettings(self, parent, r, c):
        UIFactory.AddButton(parent, ' ... ', r, c, self.ShowAutoTestSettings)

    def ShowAutoTestSettings(self):
        uiAutoTestSettings = UIAutoTestSettings(self.window, self.model, self.VM)
        uiAutoTestSettings.Show()

    def AddStartOnly(self, parent, r, c):
        self.chkStartOnly = UIFactory.AddCheckBox(parent, 'Start only', self.model.StartOnly, r, c, self.OnStartOnly)

    def OnStartOnly(self):
        self.model.StartOnly = self.chkStartOnly.get()
        self.model.WriteConfigFile()
        label = self.GetLabel()
        print label
        self.RunTestBut.config(text=label)

    def AddAttachMmi(self, parent, r, c):
        self.chkAttachMmi = UIFactory.AddCheckBox(parent, 'Attach MMi', self.model.DebugVision, r, c, self.OnAttach)

    def OnAttach(self):
        self.model.DebugVision = self.chkAttachMmi.get()
        self.model.WriteConfigFile()
        print 'Test Runner will ' + ['NOT ', ''][self.model.DebugVision] + 'wait for debugger to attach to testhost/mmi.'

    def AddSlots(self, parent, r, c):
        frame = UIFactory.AddFrame(parent, r, c)
        self.VM.chkSlots = []
        for i in range(self.model.MaxSlots):
            isSelected = (i+1) in self.model.slots
            txt = str(i+1)
            self.VM.chkSlots.append(UIFactory.AddCheckBox(frame, txt, isSelected, 0, i, self.OnSlotChn, (i,)))

    def OnSlotChn(self, index):
        self.model.UpdateSlot(index, self.VM.chkSlots[index].get())
        self.model.WriteConfigFile()
        print 'Slots for the current test : ' + str(self.model.slots)

class UIViewModel:
    def __init__(self, model):
        self.model = model

    def GetSource(self):
        return '{}     ({} | {})'.format(self.model.Source, self.model.Config, self.model.Platform)

    def UpdateSourceBranch(self):
        source = self.GetSource()
        self.lblSource.set(source)
        self.lblBranch.set(self.model.Branch)

    def StopTasks(self):
        TaskMan.StopTasks()
        VMWareRunner.RunSlots(self.model, False, False)

    @classmethod
    def RestartApp(cls, model):
        # This won't work when we execute the application using shortcut link
        # This works only when running from command prompt
        print 'Application Restarted.'
        argv = sys.argv
        if not os.path.exists(argv[0]):
            argv[0] = model.StartPath + '\\' + argv[0]
            #argv[0] = model.StartPath + '\\StartKLARunner.lnk'
        python = sys.executable
        os.execl(python, python, * argv)

    def UpdateSlotsChk(self, writeToFile):
        for i in range(self.model.MaxSlots):
            self.chkSlots[i].set((i+1) in self.model.slots)
        if writeToFile:
            self.model.WriteConfigFile()

    def OnCopyMmi(self):
        self.model.CopyMmi = self.chkCopyMmi.get()
        self.model.WriteConfigFile()
        print 'Copy MMi to ICOS : ' + str(self.chkCopyMmi.get())

    def UpdateCombo(self):
        tests = self.model.AutoTests.GetNames()
        self.cmbTest['values'] = tests
        if self.model.TestIndex >= 0 and len(tests) > self.model.TestIndex:
            self.cmbTest.current(self.model.TestIndex)

    def OnTestChanged(self, event):
        if self.model.UpdateTest(self.cmbTest.current(), False):
            print 'Test Changed to : ' + self.model.TestName
            self.UpdateSlotsChk(True)

    def UpdateSlots(self):
        if VMWareRunner.SelectSlots(self.model):
            print 'Slots Updated : ' + str(self.model.slots)
            self.UpdateSlotsChk(True)

class ControlCollection:
    def __init__(self):
        self.Buttons = {}

    def AddButton(self, button, name):
        name = self.GetValidName(name)
        self.Buttons[name] = button

    def GetButton(self, name):
        name = self.GetValidName(name)
        return self.Buttons[name]

    def GetValidName(self, name):
        return name.replace(' ', '')

class ThreadHandler:
    def __init__(self):
        self.threads = {}
        self.controlCollection = ControlCollection()

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

    def GetButtonName(self, but):
        return ' '.join(but.config('text')[-1])

    def SetButtonActive(self, name):
        but = self.controlCollection.GetButton(name)
        but['state'] = 'disabled'
        but.config(background='red')

    def SetButtonNormal(self, name):
        but = self.controlCollection.GetButton(name)
        but['state'] = 'normal'
        but.config(background='SystemButtonFace')

    def AddButton(self, parent, label, r, c, FunPnt, args = None, InitFunPnt = None, width = 19):
        argSet = (label, FunPnt, args, InitFunPnt)
        but = UIFactory.AddButton(parent, label, r, c, self.Start, argSet, width)
        name = self.GetButtonName(but)
        self.controlCollection.AddButton(but, name)
        return but

class UIGrid:
    def __init__(self, parent, threadHandler):
        self.Col = 0
        self.parent = parent
        self.threadHandler = threadHandler

    def CreateColumnFrame(self):
        self.ColFrame = UIFactory.AddFrame(self.parent, 0, self.Col, sticky='n')
        self.Col += 1
        self.RowInx = 0

    def AddParallelButton(self, label, FunPnt, args = None, InitFunPnt = None):
        self.threadHandler.AddButton(self.ColFrame, label, self.RowInx, 0, FunPnt, args, InitFunPnt)
        self.RowInx += 1

    def AddButton(self, label, FunPnt, args = None):
        but = UIFactory.AddButton(self.ColFrame, label, self.RowInx, 0, FunPnt, args, 19)
        self.RowInx += 1

class UIMainMenu:
    def __init__(self, UI, klaRunner, vsSolutions, threadHandler, testRunner):
        self.window = UI.window
        self.VM = UI.VM
        self.model = klaRunner.model
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.testRunner = testRunner
        self.mmiSpcTestRunner = MmiSpcTestRunner(self.model)
        self.appRunner = AppRunner(self.model, testRunner, vsSolutions)

        UI.AddSeparator()

        self.uiGrid = UIGrid(UI.AddRow(), threadHandler)
        self.AddColumn1()
        self.AddColumn2()
        self.AddColumn3()
        self.AddColumn4()
        self.AddColumn5()

        UI.AddSeparator()

    def AddColumn1(self):
        self.uiGrid.CreateColumnFrame()
        self.uiGrid.AddButton('Stop All KLA Apps', self.VM.StopTasks)
        if self.model.ShowAllButtons:
            self.uiGrid.AddButton('Run Handler', self.appRunner.RunHandler)
            self.uiGrid.AddButton('Stop MMi alone', self.appRunner.StopMMi)
            self.uiGrid.AddButton('Run MMi from Source', self.appRunner.RunMMi, (True,))
            self.uiGrid.AddButton('Run MMi from C:/Icos', self.appRunner.RunMMi, (False,))
        self.uiGrid.AddButton('Run MMi SPC Tests', self.mmiSpcTestRunner.RunAllTests)

    def AddColumn2(self):
        self.uiGrid.CreateColumnFrame()
        vsSolutions = self.vsSolutions
        self.uiGrid.AddButton('Open Python', self.klaRunner.OpenPython)
        for inx,sln in enumerate(self.vsSolutions.Solutions):
            label = 'Open ' + self.vsSolutions.GetSlnName(sln)
            self.uiGrid.AddButton(label, vsSolutions.OpenSolutionFile, (sln,))
        self.uiGrid.AddButton('Other Solutions', self.ShowOpenSolutionDlg)

    def ShowOpenSolutionDlg(self):
        UISolutionList(self.window, self.model, self.vsSolutions).Show()

    def AddColumn3(self):
        self.uiGrid.CreateColumnFrame()
        self.uiGrid.AddButton('Tortoise Git Diff', AppRunner.OpenLocalDif, (self.model,))
        if self.model.ShowAllButtons:
            self.uiGrid.AddButton('Git GUI', Git.OpenGitGui, (self.model,))
            self.uiGrid.AddButton('Git Bash Console', Git.OpenGitBash, (self.model,))
        self.uiGrid.AddButton('Git Fetch Pull', Git.FetchPull, (self.model,))
        self.uiGrid.AddButton('Git Submodule Update', Git.SubmoduleUpdate, (self.model,))

    def AddColumn4(self):
        if self.model.ShowAllButtons:
            self.uiGrid.CreateColumnFrame()
            self.uiGrid.AddButton('Run ToolLink Host', self.appRunner.RunToollinkHost)
            self.uiGrid.AddButton('Copy Mock License', PreTestActions.CopyMockLicense, (self.model,))
            self.uiGrid.AddButton('Copy xPort xml', PreTestActions.CopyxPortIllumRef, (self.model,))
            self.uiGrid.AddButton('Generate LicMgrConfig', PreTestActions.GenerateLicMgrConfig, (self.model,))
            self.uiGrid.AddButton('Copy LicMgrConfig', PreTestActions.CopyLicMgrConfig, (self.model,))
            self.uiGrid.AddButton('Copy MmiSaveLogs.exe', PreTestActions.CopyMmiSaveLogExe, (self.model,))

    def AddColumn5(self):
        self.uiGrid.CreateColumnFrame()
        effortLogger = EffortLogger()
        self.uiGrid.AddButton('Settings', self.ShowSettings)
        if self.model.ShowAllButtons:
            self.uiGrid.AddButton('Clear Output', OsOperations.Cls)
        if self.model.ShowAllButtons:
            self.uiGrid.AddButton('Print mmi.h IDs', self.klaRunner.PrintMissingIds)
            self.uiGrid.AddButton('Effort Log', effortLogger.PrintEffortLogInDetail, (self.model.EffortLogFile,))
            self.uiGrid.AddButton('Daily Log', effortLogger.PrintDailyLog, (self.model.EffortLogFile,))

    def ShowSettings(self):
        uiSettings = UISettings(self.window, self.model)
        uiSettings.Show()

class UIWindow(object):
    def __init__(self, parent, model, title):
        self.Parent = parent
        self.model = model
        self.Title = title

    def Show(self):
        self.window = UIFactory.CreateWindow(self.Parent, self.Title, self.model.StartPath)
        self.frame = UIFactory.AddFrame(self.window, 0, 0, 20, 20)
        self.CreateUI(self.frame)
        self.window.protocol('WM_DELETE_WINDOW', self.OnClosing)
        if self.Parent is None:
            self.window.mainloop()

    def CreateUI(self, parent):
        pass

    def OnClosing(self):
        if self.Parent is not None:
            self.Parent.deiconify()
            self.Parent = None
        self.model.WriteConfigFile()
        self.window.destroy()

    def AddBackButton(self, parent, r, c):
        UIFactory.AddButton(parent, 'Back', r, c, self.OnClosing, None, 19)

class UIAutoTestSettings(UIWindow):
    def __init__(self, parent, model, VM):
        super(UIAutoTestSettings, self).__init__(parent, model, 'Auto Test Settings')
        self.VM = VM

    def CreateUI(self, parent):
        testFrame = UIFactory.AddFrame(parent, 0, 0)

        UIFactory.AddLabel(testFrame, 'Method 1: Add test by browsing script.py file', 0, 0)
        self.AddBrowseButton(testFrame, 1)

        UIFactory.AddLabel(testFrame, '', 2, 0) # Empty Row

        UIFactory.AddLabel(testFrame, 'Method 2: Add test by selecting from list', 3, 0)
        self.filterTestSelector = FilterTestSelector()
        self.RemoveTestMan = RemoveTestMan()
        self.filterTestSelector.AddUI(testFrame, self.model, 4, 0, self.RemoveTestMan.UpdateCombo)

        UIFactory.AddLabel(testFrame, '', 5, 0) # Empty Row

        self.RemoveTestMan.AddUI(testFrame, self.model, 6, 0)

        UIFactory.AddLabel(testFrame, '', 7, 0) # Empty Row

        self.AddBackButton(parent, 8, 0)

    def OnClosing(self):
        self.VM.UpdateCombo()
        self.VM.UpdateSlotsChk(False)
        super(UIAutoTestSettings, self).OnClosing()

    def AddBrowseButton(self, parent, r):
        frame = UIFactory.AddFrame(parent, r, 0)
        UIFactory.AddButton(frame, 'Add Test', 0, 0, self.AddTestUI, None, 19)

    def AddTestUI(self):
        dir = self.model.Source + '/handler/tests'
        ftypes=[('Script Files', 'Script.py')]
        title = "Select Script file"
        filename = tkFileDialog.askopenfilename(initialdir=dir, filetypes=ftypes, title=title)
        if len(filename) > 10:
            testName = filename[len(dir) + 1: -10]
            self.filterTestSelector.AddSelectedTest(testName)

class UISettings(UIWindow):
    def __init__(self, parent, model):
        super(UISettings, self).__init__(parent, model, 'Settings')

    def CreateUI(self, parent):
        pathFrame = UIFactory.AddFrame(parent, 0, 0)
        self.Row = 0
        self.AddSelectFileRow(pathFrame, 'DevEnv.com', 'DevEnvCom')
        self.AddSelectFileRow(pathFrame, 'DevEnv.exe', 'DevEnvExe')
        self.AddSelectPathRow(pathFrame, 'Git Bin', 'GitBin')
        self.AddSelectPathRow(pathFrame, 'VM ware WS', 'VMwareWS')
        self.AddSelectFileRow(pathFrame, 'Effort Log File', 'EffortLogFile')
        self.AddSelectPathRow(pathFrame, 'MMi Config Path', 'MMiConfigPath')
        self.AddSelectPathRow(pathFrame, 'MMi Setups Path', 'MMiSetupsPath')

        self.checkFrame = UIFactory.AddFrame(parent, 1, 0)
        self.Row = 0
        self.CheckBoxes = dict()
        self.AddCheckBoxRow('Show All Commands in KlaRunner', 'ShowAllButtons', self.OnShowAll)
        self.AddCheckBoxRow('Restart Slots while running MMi alone', 'RestartSlotsForMMiAlone', self.OnRestartSlotsForMMi)
        self.AddCheckBoxRow('Copy MMi to Icos On AutoTest', 'CopyMmi', self.OnCopyMMiToIcosOnTest)
        self.AddCheckBoxRow('Generate LicMgrConfig.xml On AutoTest', 'GenerateLicMgrConfigOnTest', self.OnGenerateLicMgrConfigOnTest)
        self.AddCheckBoxRow('Copy Mock License On AutoTest', 'CopyMockLicenseOnTest', self.OnCopyMockLicenseOnTest)
        self.AddCheckBoxRow('Copy xPort_IllumReference.xml on AutoTest', 'CopyExportIllumRefOnTest', self.OnCopyExportIllumRefOnTest)

        self.AddBackButton(parent, 2, 0)

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
        textVar = UIFactory.AddLabel(parent, text, self.Row, 1)
        args = (textVar, attrName)
        UIFactory.AddButton(parent, ' ... ', self.Row, 2, cmd, args)
        self.Row += 1

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

    def AddCheckBoxRow(self, txt, attrName, FunPnt):
        isChecked = getattr(self.model, attrName) # self.model.__dict__[modelVar] also works
        args = (FunPnt, attrName)
        self.CheckBoxes[attrName] = UIFactory.AddCheckBox(self.checkFrame, txt, isChecked, self.Row, 0, self.OnClickCheckBox, args)
        self.Row += 1

    def OnClickCheckBox(self, FunPnt, attrName):
        setattr(self.model, attrName, self.CheckBoxes[attrName].get())
        FunPnt()

    def OnShowAll(self):
        MessageBox.ShowMessage('You need to restart the application to update the UI.')

    def OnRestartSlotsForMMi(self):
        msg = 'The selected slots will {}be restarted while running MMi alone.'
        if self.model.RestartSlotsForMMiAlone:
            print msg.format('')
        else:
            print msg.format('NOT ')

    def OnCopyMMiToIcosOnTest(self):
        if not self.model.CopyMmi:
            MessageBox.ShowMessage('Do NOT copy the mmi built over the installation in C:/icos.\nThis is NOT RECOMMENDED.')
        else:
            print 'Copy the mmi built over the installation in C:/icos.'

    def OnGenerateLicMgrConfigOnTest(self):
        if self.model.GenerateLicMgrConfigOnTest:
            MessageBox.ShowMessage('The file LicMgrConfig.xml will be created while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file LicMgrConfig.xml will NOT be created while running auto test.'

    def OnCopyMockLicenseOnTest(self):
        if self.model.CopyMockLicenseOnTest:
            MessageBox.ShowMessage('The file mock License.dll will be copied while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file mock License.dll will NOT be copied while running auto test.'

    def OnCopyExportIllumRefOnTest(self):
        if self.model.CopyExportIllumRefOnTest:
            MessageBox.ShowMessage('The file xPort_IllumReference.xml will be copied while running auto test.\nThis is NOT RECOMMENDED.')
        else:
            print 'The file xPort_IllumReference.xml will NOT be copied while running auto test.'

class UISourceSelector(UIWindow):
    def __init__(self, parent, model, klaRunner, vsSolutions, VM, threadHandler):
        super(UISourceSelector, self).__init__(parent, model, 'Select Source')
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions
        self.VM = VM
        self.threadHandler = threadHandler
        self.srcBuilder = KlaSourceBuilder(self.model, self.klaRunner, self.vsSolutions)

    def CreateUI(self, parent):
        self.SelectedSrc = tk.IntVar()
        self.SelectedSrc.set(self.model.SrcIndex)
        self.lblBranches = []
        self.cboConfig = []
        self.cboPlatform = []
        self.chkActiveSrcs = []
        self.Row = 0
        self.mainFrame = parent
        frameGrid = self.AddRow()
        UIFactory.AddLabel(frameGrid, 'Current Source', 0, 0)
        UIFactory.AddLabel(frameGrid, 'Branch', 0, 1)
        UIFactory.AddLabel(frameGrid, 'Configuration', 0, 2)
        UIFactory.AddLabel(frameGrid, 'Platform', 0, 3)
        UIFactory.AddLabel(frameGrid, 'Is Active', 0, 4)
        r = 1
        for srcTuple in self.model.Sources:
            self.AddSource(frameGrid, r, 0, srcTuple[0])
            self.AddBranch(frameGrid, r, 1, srcTuple[0])
            self.AddConfig(frameGrid, r, 2, srcTuple[1])
            self.AddPlatform(frameGrid, r, 3, srcTuple[2])
            self.AddActive(frameGrid, r, 4)
            r += 1

        self.AddSolutions()
        self.AddFunctions()

        threading.Thread(target=self.LazyUiInit).start()

    def AddRow(self):
        frame = UIFactory.AddFrame(self.mainFrame, self.Row, 0)
        self.Row += 1
        return frame

    def AddEmptyRow(self):
        frame = self.AddRow()
        UIFactory.AddLabel(frame, '', 0, 0)

    def LazyUiInit(self):
        index = 0
        data = [['Source', 'Branch']]
        for srcTuple in self.model.Sources:
            data.append(['-'])
            branch = '' # Git.GetBranch(srcTuple[0])
            for brn1 in Git.GetLocalBranches(srcTuple[0]):
                if brn1.startswith('* '):
                    branch = brn1[2:]
                    data.append([srcTuple[0], branch])
                else:
                    data.append(['', brn1])
            self.lblBranches[index].set(branch)
            if index == self.model.SrcIndex:
                self.model.Branch = branch
            index += 1
        print PrettyTable(TableFormat().SetSingleLine()).ToString(data)

    def OnClosing(self):
        self.model.Branch = self.lblBranches[self.model.SrcIndex].get()
        if self.VM is not None:
            self.VM.UpdateSourceBranch()
        super(UISourceSelector, self).OnClosing()

    def AddSource(self, parent, r, c, source):
        rd = tk.Radiobutton(parent,
            text = source,
            variable = self.SelectedSrc,
            command = self.OnSelectSrc,
            value = r-1)
        rd.grid(row=r, column=0, sticky='w')

    def OnSelectSrc(self):
        SrcIndex = self.SelectedSrc.get()
        self.model.SrcCnf.UpdateSource(SrcIndex, False)
        print 'Source changed to : ' + self.model.Source
        Logger.Log('Source changed to : ' + self.model.Source)

    def AddBranch(self, parent, r, c, source):
        label = UIFactory.AddLabel(parent, 'Branch Name Updating...', r, c)
        self.lblBranches.append(label)

    def AddConfig(self, parent, r, c, config):
        configInx = ConfigEncoder.Configs.index(config)
        combo = UIFactory.AddCombo(parent, ConfigEncoder.Configs, configInx, r, c, self.OnConfigChanged, r-1, 10)
        self.cboConfig.append(combo)

    def OnConfigChanged(self, row):
        selectedInx = self.cboConfig[row].current()
        if self.model.UpdateConfig(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Config Changed to {} for source {}'.format(srcTuple[1], srcTuple[0])

    def AddPlatform(self, parent, r, c, platform):
        platformInx = ConfigEncoder.Platforms.index(platform)
        combo = UIFactory.AddCombo(parent, ConfigEncoder.Platforms, platformInx, r, c, self.OnPlatformChanged, r-1, 10)
        self.cboPlatform.append(combo)

    def OnPlatformChanged(self, row):
        selectedInx = self.cboPlatform[row].current()
        if self.model.UpdatePlatform(row, selectedInx):
            self.model.WriteConfigFile()
            srcTuple = self.model.Sources[row]
            print 'Platform Changed to {} for source {}'.format(srcTuple[2], srcTuple[0])

    def AddActive(self, parent, r, c):
        Index = r - 1
        isActive = Index in self.model.ActiveSrcs
        chk = UIFactory.AddCheckBox(parent, '', isActive, r, c, self.OnActiveSrcChanged, (Index,), 'ew')
        self.chkActiveSrcs.append(chk)

    def OnActiveSrcChanged(self, Index):
        if self.chkActiveSrcs[Index].get():
            self.model.ActiveSrcs.append(Index)
            self.model.ActiveSrcs = list(set(self.model.ActiveSrcs))
            print 'Enabled the source : ' + str(self.model.Sources[Index][0])
        else:
            self.model.ActiveSrcs.remove(Index)
            print 'Disabled the source : ' + str(self.model.Sources[Index][0])

    def AddSolutions(self):
        allSlns = self.vsSolutions.GetAllSlnFiles()
        self.vsSolutions.SelectedInxs = [True] * len(allSlns)
        if self.klaRunner is None:
            return
        self.AddEmptyRow()
        selMsg = 'Select Solutions to build / clean on active sources'
        UIFactory.AddLabel(self.AddRow(), selMsg, 0, 0)
        self.slnChks = []
        row1 = self.AddRow()
        for inx,sln in enumerate(allSlns):
            slnName = self.vsSolutions.GetSlnName(sln)
            chk = UIFactory.AddCheckBox(row1, slnName, True, 0, inx, self.OnSelectSolution, (inx,))
            self.slnChks.append(chk)
        row2 = self.AddRow()
        self.threadHandler.AddButton(row2, ' Clean Solutions ', 0, 0, self.srcBuilder.CleanSource, None, self.srcBuilder.NotifyClean, 19)
        self.threadHandler.AddButton(row2, ' Build Solutions ', 0, 1, self.srcBuilder.BuildSource, None, self.srcBuilder.NotifyBuild, 19)

    def OnSelectSolution(self, inx):
        self.vsSolutions.SelectedInxs[inx] = self.slnChks[inx].get()

    def AddFunctions(self):
        if self.klaRunner is not None:
            if self.model.ShowAllButtons:
                self.AddEmptyRow()
                row1 = self.AddRow()
                self.threadHandler.AddButton(row1, ' Reset Source ', 0, 0, self.srcBuilder.ResetSource, None, self.srcBuilder.NotifyReset, 19)
                self.AddCleanDotVsOnReset(row1, 0, 1)

        self.AddEmptyRow()
        row2 = self.AddRow()
        UIFactory.AddButton(row2, 'Add Source', 0, 0, self.OnAddSource, None, 19)
        UIFactory.AddButton(row2, 'Remove Source', 0, 1, self.OnRemoveSource, None, 19)
        self.AddBackButton(row2, 0, 2)

    def AddCleanDotVsOnReset(self, parent, r, c):
        txt = 'Remove .vs directories on reseting source'
        isChecked = self.model.CleanDotVsOnReset
        self.ChkCleanDotVsOnReset = UIFactory.AddCheckBox(parent, txt, isChecked, r, c, self.OnCleanDotVsOnReset)

    def OnCleanDotVsOnReset(self):
        self.model.CleanDotVsOnReset = self.ChkCleanDotVsOnReset.get()
        if self.model.CleanDotVsOnReset:
            MessageBox.ShowMessage('All .vs directories in the source will be removed while reseting source.')
        else:
            print 'The .vs directories will NOT be affected while reseting source.'

    def OnAddSource(self):
        folderSelected = tkFileDialog.askdirectory()
        if len(folderSelected) > 0:
            ConfigEncoder.AddSrc(self.model, folderSelected)
            row = len(self.model.Sources)
            self.AddRow(row, self.model.Sources[-1])
            print 'New source added : ' + folderSelected

    def OnRemoveSource(self):
        src = self.model.Sources[self.model.SrcIndex][0]
        if MessageBox.YesNoQuestion('Remove Source', 'Do you want to remove source ' + src):
            msg = 'The source ' + src + ' has been removed.'
            del self.model.Sources[self.model.SrcIndex]
            del self.cboConfig[self.model.SrcIndex]
            del self.cboPlatform[self.model.SrcIndex]
            self.model.SrcCnf.UpdateSource(self.model.SrcIndex - 1, False)
            print msg

class UISolutionList(UIWindow):
    def __init__(self, parent, model, vsSolutions):
        super(UISolutionList, self).__init__(parent, model, 'Visutal Studio Solutions')
        self.vsSolutions = vsSolutions

    def CreateUI(self, parent):
        frame = UIFactory.AddFrame(parent, 0, 0, 50)

        for inx,sln in enumerate(self.vsSolutions.OtherSolutions):
            label = 'Open ' + self.vsSolutions.GetSlnName(sln)
            UIFactory.AddButton(frame, label, inx, 0, self.OnOpenSolution, (sln,), 19)
        self.AddBackButton(frame, 8, 0)

    def OnOpenSolution(self, sln):
        self.vsSolutions.OpenSolutionFile(sln)

class FilterTestSelector:
    def AddUI(self, parent, model, r, c, updateCombo):
        self.model = model
        self.UpdateCombo = updateCombo
        frame = UIFactory.AddFrame(parent, r, c)
        UIFactory.AddEntry(frame, self.OnSearchTextChanged, 0, 0, 25)
        self.AddTestCombo(frame, 1)
        UIFactory.AddButton(frame, 'Add Selected Test', 0, 2, self.OnAddSelectedTest)

    def AddTestCombo(self, parent, c):
        self.TestCmb = UIFactory.AddCombo(parent, [], -1, 0, c, self.OnChangeTestCmb, None, 50)
        threading.Thread(target=self.UpdateUI).start()

    def GetAllTests(self):
        allFiles = []
        dir = self.model.Source + '/handler/tests'
        dirLen = len(dir) + 1
        for root, dirs, files in os.walk(dir):
            if 'script.py' in files and not root[-1:] == '~':
                allFiles.append(root[dirLen:].replace('\\', '/'))
        return allFiles

    def OnChangeTestCmb(self, event):
        if len(self.FilteredTests) > 0:
            print 'Combo item changed to : ' + self.FilteredTests[self.TestCmb.current()]
        else:
            print 'Combo is empty'

    def OnSearchTextChanged(self, input):
        input = input.lower()
        self.FilteredTests = []
        for testName in self.AllTests:
            if input in testName.lower():
                self.FilteredTests.append(testName)
        self.TestCmb['values'] = self.FilteredTests
        if len(self.FilteredTests) > 0:
            self.TestCmb.current(0)
        else:
            self.TestCmb.set('')
        return True

    def OnAddSelectedTest(self):
        if len(self.FilteredTests) > 0:
            testName = self.FilteredTests[self.TestCmb.current()]
            self.AddSelectedTest(testName)
        else:
            print 'No tests selected'

    def AddSelectedTest(self, testName):
        index = self.model.AutoTests.AddTestToModel(testName)
        if self.model.UpdateTest(index, False):
            print 'Test Added : ' + testName
            self.UpdateCombo()
        else:
            print 'Test is already Added : ' + testName

    def UpdateUI(self):
        self.FilteredTests = self.AllTests = self.GetAllTests()
        self.TestCmb['values'] = self.FilteredTests
        if len(self.FilteredTests) > 0:
            self.TestCmb.current(0)

class RemoveTestMan:
    def AddUI(self, parent, model, r, c):
        self.model = model
        frame = UIFactory.AddFrame(parent, r, c, 0, 0, 2)
        self.Tests = self.model.AutoTests.GetNames()
        UIFactory.AddLabel(frame, 'Selected Tests', 0, 0)
        self.TestCmb = UIFactory.AddCombo(frame, self.Tests, 0, 0, 1, self.OnChangeTestCmb, None, 50)
        if len(self.Tests) > 0:
            self.TestCmb.current(0)
        UIFactory.AddButton(frame, 'Remove Test', 0, 2, self.OnRemoveSelectedTest)

    def OnChangeTestCmb(self, event):
        if len(self.Tests) > 0:
            print 'Combo item changed to : ' + self.Tests[self.TestCmb.current()]
        else:
            print 'Combo is empty'

    def OnRemoveSelectedTest(self):
        if len(self.Tests) > 0:
            index = self.TestCmb.current()
            testName = self.Tests[index]
            del self.model.AutoTests.Tests[index]
            del self.Tests[index]
            print 'Test Removed : ' + testName
            self.TestCmb['values'] = self.Tests
            if index >= len(self.Tests):
                index = len(self.Tests) - 1
            self.TestCmb.current(index)
            if self.model.TestIndex >= len(self.Tests):
                self.model.UpdateTest(len(self.Tests) - 1, False)
        else:
            print 'No tests selected'

    def UpdateCombo(self):
        self.Tests = self.model.AutoTests.GetNames()
        self.TestCmb['values'] = self.Tests

class KlaRunner:
    def __init__(self, model):
        self.model = model
        self.SetWorkingDir()

    def OpenPython(self):
        #FileOperations.Delete('{}/libs/testing/myconfig.py'.format(self.model.Source))
        self.CreateMyConfig()
        fileName = os.path.abspath(self.model.Source + '/libs/testing/my.py')
        par = 'start python -i ' + fileName
        OsOperations.System(par, 'Starting my.py')

    def CreateMyConfig(self):
        config = ConfigEncoder.GetBuildConfig(self.model)
        data = 'version = 0\n'
        data += 'console_config = r"{}"\n'.format(config[0])
        data += 'simulator_config = r"{}"\n'.format(config[0])
        data += 'mmiBuildConfiguration = r"{}"\n'.format(config)
        data += 'mmiConfigurationsPath = "{}"\n'.format(self.model.MMiConfigPath.replace('\\', '/'))
        data += 'platform = r"{}"\n'.format(self.model.Platform)
        data += 'mmiSetupsPath = "{}"'.format(self.model.MMiSetupsPath.replace('\\', '/'))
        FileOperations.Write('{}/libs/testing/myconfig.py'.format(self.model.Source), data)

    def GetTestPath(self):
        return os.path.abspath(self.model.Source + '/handler/tests/' + self.model.TestName)

    def OpenTestFolder(self):
        dirPath = self.GetTestPath()
        if not os.path.isdir(dirPath):
            msg = 'Test folder does not exists : ' + dirPath
            print msg
            MessageBox.ShowMessage('KLA Runner', msg)
            return
        subprocess.Popen(['Explorer', dirPath])
        print 'Open directory : ' + dirPath

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

    def SetWorkingDir(self):
        wd = os.path.join(self.model.StartPath, self.model.TempDir)
        if not os.path.isdir(wd):
            os.mkdir(wd)
        os.chdir(wd)

class AppRunner:
    def __init__(self, model, testRunner, vsSolutions):
        self.model = model
        self.testRunner = testRunner
        self.vsSolutions = vsSolutions

    def RunHandler(self):
        Logger.Log('Run Handler in ' + self.model.Source)
        TaskMan.StopTasks()

        handlerPath,consoleExe = self.vsSolutions.GetHandlerPath()
        testTempDir = self.model.Source + '/handler/tests/' + self.model.TestName + '~'

        simulatorExe = self.vsSolutions.GetSimulatorPath()

        for file in [consoleExe, testTempDir, simulatorExe]:
            if not os.path.exists(file):
                print 'File not found : ' + file
                return

        OsOperations.System('start ' + consoleExe + ' ' + testTempDir)
        OsOperations.System('start {} {} {}'.format(simulatorExe, testTempDir, handlerPath))

    def StopMMi(self):
        TaskMan.StopTask('MMi.exe')
        VMWareRunner.RunSlots(self.model)

    def RunMMi(self, fromSrc):
        if self.model.RestartSlotsForMMiAlone:
            self.StopMMi()

        mmiPath = PreTestActions.GetMmiPath(self.model, fromSrc)
        Logger.Log('Run MMi from ' + mmiPath)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            PreTestActions.CopyMockLicense(self.model, fromSrc)
            PreTestActions.CopyLicMgrConfig(self.model, False)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model)
        if self.model.RestartSlotsForMMiAlone:
            OsOperations.Timeout(8)

        mmiExe = os.path.abspath(mmiPath + '/Mmi.exe')
        if not os.path.exists(mmiExe):
            print 'File not found : ' + mmiExe
            return

        OsOperations.System('start ' + mmiExe)

    def RunHandlerMMi(self):
        self.RunHandler()
        self.RunMMi(True)

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

class TaskMan:
    namedTimers = {}

    @classmethod
    def StopTasks(cls):
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

    @classmethod
    def StopTask(cls, exeName, exceptProcId = -1):
        processIds = OsOperations.GetProcessIds(exeName)
        if exceptProcId > 0:
            processIds.remove(exceptProcId)
        if len(processIds) == 0:
            return False
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
        return True

    @classmethod
    def AddTimer(cls, name, timer):
        if name in cls.namedTimers:
            cls.StopTimer(name)
        cls.namedTimers[name] = timer

    @classmethod
    def StopTimer(cls, name):
        if cls.namedTimers[name] is not None:
            cls.namedTimers[name].stop()
            cls.namedTimers[name] = None

    @classmethod
    def StopTimers(cls):
        for name in cls.namedTimers:
            cls.StopTimer(name)

class VMWareRunner:
    @classmethod
    def SelectSlots(cls, model):
        fileName = 'C:/Icos/Mmi_Cnf.xml'
        if not os.path.isfile(fileName):
            MessageBox.ShowMessage('KLA Runner', 'File does not exist: ' + fileName)
            return False
        mydoc = minidom.parse(fileName)
        devices = mydoc.getElementsByTagName('Device')
        slots = []
        for device in devices:
            deviceName = device.firstChild.data
            slots.append(int(deviceName.split('_')[0][3:]))
        model.SelectSlots(slots)
        return True

    @classmethod
    def RunSlots(cls, model, startSlot = True, showMessage = True):
        vMwareWS = model.VMwareWS
        slots = model.slots
        if len(slots) == 0:
            if showMessage:
                MessageBox.ShowMessage('Please select necessary slot(s).')
            return False
        vmRunExe = vMwareWS + '/vmrun.exe'
        vmWareExe = vMwareWS + '/vmware.exe'
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
                if startSlot:
                    subprocess.Popen([vmWareExe, vmxPath])
                    if showMessage:
                        msg = 'Please start ' + slotName
                        MessageBox.ShowMessage(msg)
        return True

    @classmethod
    def TestSlots(cls, model):
        slots = model.slots
        if len(slots) == 0:
            MessageBox.ShowMessage('Please select necessary slot(s).')
            return

        if TaskMan.StopTask('MvxCmd.exe'):
            OsOperations.Timeout(5)
        cd1 = os.getcwd()
        OsOperations.ChDir('C:/MVS7000/slot1/')
        # Bug : only first slot is working.
        for slot in slots:
            os.chdir('../slot{}'.format(slot))
            cmd = 'slot{}.bat'.format(slot)
            OsOperations.System(cmd)
        OsOperations.ChDir(cd1)

class PreTestActions:
    @classmethod
    def CopyMockLicense(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        licencePath = '{}/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/{}/{}/License.dll'
        licenseFile = os.path.abspath(licencePath.format(*args))
        mmiPath = PreTestActions.GetMmiPath(model, toSrc)
        FileOperations.Copy(licenseFile, mmiPath)

    @classmethod
    def GetMmiPath(cls, model, toSrc = True):
        args = (model.Source, model.Platform, model.Config)
        if toSrc:
            mmiPath = os.path.abspath('{}/mmi/mmi/Bin/{}/{}'.format(*args))
        else:
            mmiPath = 'C:/icos'
        return mmiPath

    @classmethod
    def CopyxPortIllumRef(cls, model, delay = False):
        src = model.StartPath + '\\xPort_IllumReference.xml'
        des = 'C:/icos/xPort/'
        if delay:
            TaskMan.AddTimer('xport', FileOperations.Copy(src, des, 8, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def GetTestPath(cls, model):
        return os.path.abspath(model.Source + '/handler/tests/' + model.TestName)

    @classmethod
    def GenerateLicMgrConfig(cls, model):
        src = model.StartPath + '\\LicMgrConfig.xml'
        LicenseConfigWriter(model.Source, src)
        print 'LicMgrConfig.xml has been created from source and placed on ' + src

    @classmethod
    def CopyLicMgrConfig(cls, model, delay = False):
        src = model.StartPath + '\\LicMgrConfig.xml'
        #des = cls.GetTestPath(model) + '~/'
        des = 'C:/Icos'
        if delay:
            TaskMan.AddTimer('LicMgr', FileOperations.Copy(src, des, 9, 3))
        else:
            FileOperations.Copy(src, des)

    @classmethod
    def CopyMmiSaveLogExe(cls, model):
        destin = os.path.abspath("{}/handler/tests/{}~/Icos".format(
            model.Source, model.TestName))
        src = os.path.abspath('{}/mmi/mmi/Bin/{}/{}/MmiSaveLogs.exe'.format(
            model.Source, model.Platform, model.Config))
        FileOperations.Copy(src, destin)

    @classmethod
    def ModifyVisionSystem(cls, model):
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

class MmiSpcTestRunner:
    def __init__(self, model):
        self.model = model

    def RunAllTests(self):
        os.chdir(self.model.Source)
        buildPath = 'mmi/mmi/bin/{}/{}'.format(self.model.Platform, self.model.Config)
        par = 'python libs/testing/testrunner.py'
        par += ' -t mmi/mmi/mmi_stat/integration/tests'
        par += ' -c ' + buildPath
        par += ' -s ' + buildPath
        par += ' -f ' + buildPath
        par += ' -n 1 -r 2'
        par += ' --mmiSetupExe ' + self.model.MMiSetupsPath
        OsOperations.System(par, 'Running Mmi SPC Tests')
        os.chdir(self.model.StartPath)

class AutoTestRunner:
    def __init__(self, model, VM):
        self.model = model
        self.VM = VM
        self.lastSrc = None

    def InitAutoTest(self):
        if self.lastSrc is None:
            self.lastSrc = self.model.Source
        elif self.lastSrc != self.model.Source:
            msg = 'Test has already been executed with {}. So please restart KLA Runner.'.format(self.lastSrc)
            MessageBox.ShowMessage('KLA Runner', msg)
            return False
        TaskMan.StopTasks()
        return VMWareRunner.RunSlots(self.model)

    def RunAutoTest(self):
        testType = 'Start' if self.model.StartOnly else 'Run'
        Logger.Log('{} Auto Test {} in {}'.format(testType, self.model.TestName, self.model.Source))
        PreTestActions.ModifyVisionSystem(self.model)

        if self.model.GenerateLicMgrConfigOnTest:
            PreTestActions.GenerateLicMgrConfig(self.model)
        if self.model.CopyMockLicenseOnTest:
            #PreTestActions.CopyMockLicense(self.model, False)
            PreTestActions.CopyLicMgrConfig(self.model, True)
        if self.model.CopyExportIllumRefOnTest:
            PreTestActions.CopyxPortIllumRef(self.model, True)

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
        my.c.startup = self.model.StartOnly
        my.c.debugvision = self.model.DebugVision
        my.c.copymmi = self.model.CopyMmi
        my.c.mmiBuildConfiguration = ConfigEncoder.GetBuildConfig(self.model)
        my.c.console_config = my.c.simulator_config = my.c.mmiBuildConfiguration[0]
        my.c.platform = self.model.Platform
        my.c.mmiConfigurationsPath = self.model.MMiConfigPath
        my.c.mmiSetupsPath = self.model.MMiSetupsPath
        my.run(tests[0][0])
        if self.VM is not None:
            self.VM.UpdateSlots()
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

class VisualStudioSolutions:
    def __init__(self, model):
        self.model = model
        self.Solutions = [
            '/handler/cpp/CIT100.sln',
            '/mmi/mmi/Mmi.sln'
        ]
        self.OtherSolutions = [
            '/handler/Simulator/CIT100Simulator/CIT100Simulator.sln',
            '/mmi/mmi/MockLicense.sln',
            '/mmi/mmi/Converters.sln',
            '/libs/DLStub/DLStub/DLStub.sln',
        ]

    def GetAllSlnFiles(self):
        #slnFiles = []
        #srcLen = len(self.model.Source) + 1
        #for root, dirs, files in os.walk(self.model.Source):
        #    path = root[srcLen:]
        #    fis = [[path, fi] for fi in files if fi.endswith('.sln')]
        #    slnFiles += fis
        #return slnFiles
        return self.Solutions + self.OtherSolutions

    def OpenSolutionIndex(self, index):
        self.OpenSolutionFile(self.GetSlnPath(index))

    def OpenSolutionFile(self, slnFileName):
        fileName = self.model.Source + slnFileName
        param = [
            self.model.DevEnvExe,
            fileName
        ]
        subprocess.Popen(param)
        print 'Open solution : ' + fileName
        if self.model.Config is not 'Debug' or self.model.Platform is not 'Win32':
            msg = 'Please check configuration and platform in Visual Studio'
            #MessageBox.ShowMessage(msg, 'Visual Studio')
            print msg

    def GetSelectedSolutions(self):
        retVal = []
        allSlns = self.GetAllSlnFiles()
        for inx,sln in enumerate(allSlns):
            if self.SelectedInxs[inx]:
                slnName = self.GetSlnName(sln)
                retVal.append((sln, slnName))
        return retVal

    def GetSlnPath(self, index):
        if index < len(self.Solutions):
            return self.Solutions[index]
        index -= len(self.Solutions)
        return self.OtherSolutions[index]

    def GetSlnName(self, slnFile):
        slnName = slnFile.split('/')[-1][:-4]
        if slnName == 'CIT100Simulator':
            return 'Simulator'
        return slnName

    def GetHandlerPath(self):
        platform = VisualStudioSolutions.GetPlatformStr(self.model.Platform)
        handlerPath = '{}/handler/cpp/bin/{}/{}/system'.format(self.model.Source, platform, self.model.Config)
        return (handlerPath, handlerPath + '/console.exe')

    def GetSimulatorPath(self):
        platform = VisualStudioSolutions.GetPlatformStr(self.model.Platform, True)
        simulatorExe = '{}/handler/Simulator/ApplicationFiles/bin/{}/{}/CIT100Simulator.exe'
        return simulatorExe.format(self.model.Source, platform, self.model.Config)

    @classmethod
    def GetPlatform(cls, slnFile, platform):
        isSimulator = slnFile.split('/')[-1] == 'CIT100Simulator.sln'
        return VisualStudioSolutions.GetPlatformStr(platform, isSimulator)

    @classmethod
    def GetPlatformStr(cls, platform, isSimulator = False):
        if isSimulator and 'Win32' == platform:
            platform = 'x86'
        return platform

class KlaSourceBuilder:
    def __init__(self, model, klaRunner, vsSolutions):
        self.model = model
        self.klaRunner = klaRunner
        self.vsSolutions = vsSolutions

    def NotifyClean(self):
        return self.NotifyUser('Clean')

    def NotifyBuild(self):
        return self.NotifyUser('Build')

    def NotifyReset(self):
        return self.NotifyUser('Reset')

    def NotifyUser(self, message):
        if len(self.model.ActiveSrcs) == 0:
            MessageBox.ShowMessage('There are no active sources. Please select the required one.')
            return False
        title = message + ' Source'
        isAre = ' is'
        if len(self.model.ActiveSrcs) > 1:
            title += 's'
            isAre = 's are'
        fullMessage = 'The following source{} ready for {}ing.\n'.format(isAre, message)
        self.srcTuple = []
        for activeSrc in self.model.ActiveSrcs:
            source, config, platform = self.model.Sources[activeSrc]
            branch = Git.GetBranch(source)
            fullMessage += '\n{} ({} | {})\n{}\n'.format(source, platform, config, branch)
            self.srcTuple.append([source, branch, config, platform])
        fullMessage += '\nDo you want to continue {}ing?'.format(message)
        result = MessageBox.YesNoQuestion(title, fullMessage)
        print 'Yes' if result else 'No'
        return result

    def ResetSource(self):
        excludeDirs = [
            '/mmi/mmi/packages',
            '/Handler/FabLink/cpp/bin',
            '/Handler/FabLink/FabLinkLib/System32',
            ]
        if self.model.CleanDotVsOnReset:
            excludeDirs += [
                '/mmi/mmi/.vs',
                '/handler/cpp/.vs',
            ]
        for srcSet in self.srcTuple:
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
                Git.RevertLastCommit(src)
            #Git.SubmoduleUpdate(src)
            print 'Cleaning completed for ' + src

    def DeleteAllGitIgnoreFiles(self, dirName):
        os.remove('{}/.gitignore'.format(dirName))
        for root, dirs, files in os.walk(dirName):
            if '.gitignore' in files and '.git' not in files:
                os.remove('{}/.gitignore'.format(root))

    def CleanSource(self):
        self.CallDevEnv(True)

    def BuildSource(self):
        self.CallDevEnv(False)

    def CallDevEnv(self, ForCleaning):
        buildOption = '/Clean' if ForCleaning else '/build'
        buildLoger = BuildLoger(self.model, ForCleaning)
        for source, branch, config, srcPlatform in self.srcTuple:
            buildLoger.StartSource(source, branch)
            for sln, slnName in self.vsSolutions.GetSelectedSolutions():
                slnFile = os.path.abspath(source + '/' + sln)
                if not os.path.exists(slnFile):
                    print "Solution file doesn't exist : " + slnFile
                    continue
                platform = VisualStudioSolutions.GetPlatform(sln, srcPlatform)
                BuildConf = config + '|' + platform
                outFile = os.path.abspath(source + '/Out_' + slnName) + '.txt'

                buildLoger.StartSolution(sln, slnName, config, platform)
                params = [self.model.DevEnvCom, slnFile, buildOption, BuildConf, '/out', outFile]
                OsOperations.Popen(params, buildLoger.PrintMsg)
                buildLoger.EndSolution()
            buildLoger.EndSource(source)
        if len(self.model.ActiveSrcs) > 1 and not ForCleaning:
            print buildLoger.ConsolidatedOutput

class BuildLoger:
    def __init__(self, model, ForCleaning):
        if ForCleaning:
            self.fileName = model.StartPath + '/bin/BuildLog.txt'
        else:
            timeStamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.fileName = '{}/bin/BuildLog_{}.txt'.format(model.StartPath, timeStamp)
        self.ForCleaning = ForCleaning
        self.message = 'cleaning' if ForCleaning else 'building'
        if not os.path.exists(self.fileName):
            print "File created : " + self.fileName
            FileOperations.Write(self.fileName, '')
        self.ConsolidatedOutput = ''

    def AddOutput(self, message, doLog):
        self.ConsolidatedOutput += message
        self.ConsolidatedOutput += '\n'
        if doLog:
            self.Log(message)

    def StartSource(self, src, branch):
        self.srcStartTime = datetime.now()
        self.AddOutput('Source : ' + src, True)
        self.AddOutput('Branch : ' + branch, True)
        self.logDataTable = [
            [ 'Solution', 'Config', 'Platform', 'Succeeded', 'Failed', 'Up To Date', 'Skipped', 'Time Taken' ],
            ['-']
        ]

    def EndSource(self, src):
        timeDelta = self.TimeDeltaToStr(datetime.now() - self.srcStartTime)
        self.Log('Completed {} {} in {}'.format(self.message, src, timeDelta))
        if not self.ForCleaning:
            self.logDataTable.append(['-'])
            self.logDataTable.append([''] * 7 + [timeDelta])
            table = '\n' + PrettyTable(TableFormat().SetSingleLine()).ToString(self.logDataTable)
            self.AddOutput(table, True)
            FileOperations.Append(self.fileName, table)

    def StartSolution(self, slnFile, name, config, platform):
        self.Log('Start {} : {}'.format(self.message, slnFile))
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

def main():
    if (len(sys.argv) == 2):
        param1 = sys.argv[1].lower()
        if param1 == 'test':
            UnitTestsRunner().Run()
    elif (__name__ == '__main__'):
        UI().Run()
        print 'Have a nice day...'

main()
