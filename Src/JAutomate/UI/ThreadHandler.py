import threading

from Common.UIFactory import UIFactory


class ControlCollection:
    def __init__(self):
        self.Buttons = {}
        self.ActiveButtons = []

    def AddButton(self, button, name):
        name = self.GetValidName(name)
        self.Buttons[name] = button
        if name in self.ActiveButtons:
            self.SetButtonActive(name)

    def GetValidName(self, name):
        return name.replace(' ', '')

    def SetButtonActive(self, name):
        name = self.GetValidName(name)
        but = self.Buttons[name]
        but['state'] = 'disabled'
        but.config(background='red')
        if name not in self.ActiveButtons:
            self.ActiveButtons.append(name)

    def SetButtonNormal(self, name):
        name = self.GetValidName(name)
        but = self.Buttons[name]
        but['state'] = 'normal'
        but.config(background='SystemButtonFace')
        self.ActiveButtons.remove(name)

class ThreadHandler: # Name is not correct
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
        self.controlCollection.SetButtonActive(name)
        threading.Thread(target=self.WaitForThread, args=(name,)).start()

    def WaitForThread(self, name):
        self.threads[name].join()
        self.controlCollection.SetButtonNormal(name)
        del self.threads[name]

    def GetButtonName(self, but):
        return ' '.join(but.config('text')[-1])

    def AddButton(self, parent, label, r, c, FunPnt, args = None, InitFunPnt = None, width = 19):
        argSet = (label, FunPnt, args, InitFunPnt)
        but = UIFactory.AddButton(parent, label, r, c, self.Start, argSet, width)
        name = self.GetButtonName(but)
        self.controlCollection.AddButton(but, name)
        return but
