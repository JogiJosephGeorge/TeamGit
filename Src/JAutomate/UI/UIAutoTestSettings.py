import threading
import tkFileDialog

from Common.UIFactory import UIFactory
from UI.UIWindow import UIWindow


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
