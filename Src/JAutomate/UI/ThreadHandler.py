import threading

from Common.UIFactory import UIFactory


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
