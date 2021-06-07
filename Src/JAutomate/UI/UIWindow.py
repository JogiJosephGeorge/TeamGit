from Common.UIFactory import UIFactory


class UIWindow(object):
    def __init__(self, parent, model, title):
        self.Parent = parent
        self.model = model
        self.Title = title

    def Show(self):
        self.window = UIFactory.CreateWindow(self.Parent, self.Title, self.model.StartPath)
        self.frame = UIFactory.AddFrame(self.window, 0, 0, 20, 20)
        self.model.Geometry.ReadGeomInfo(self.window, self.Title)
        self.CreateUI(self.frame)
        self.window.protocol('WM_DELETE_WINDOW', self.OnClosing)
        if self.Parent is None:
            self.window.mainloop()

    def CreateUI(self, parent):
        pass

    def OnClosing(self):
        if self.Parent is not None:
            self.model.Geometry.WriteGeomInfo(self.window, self.Title)
            self.Parent.deiconify()
            self.Parent = None
        self.model.WriteConfigFile()
        self.window.destroy()

    def AddBackButton(self, parent, r, c):
        UIFactory.AddButton(parent, 'Back', r, c, self.OnClosing, None, 19)
