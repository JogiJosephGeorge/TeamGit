from Common.UIFactory import UIFactory


class UIWindow(object):
    def __init__(self, parent, model, title, onClosed = None):
        self.Parent = parent
        self.model = model
        self.Title = title
        self.OnClosed = onClosed

    def Show(self):
        startPath = self.model.StartPath if self.model else ''
        self.window = UIFactory.CreateWindow(self.Parent, self.Title, startPath)
        self.frame = UIFactory.AddFrame(self.window, 0, 0, 20, 20)
        if self.model:
            self.model.Geometry.ReadGeomInfo(self.window, self.Title)
        self.CreateUI(self.frame)
        self.window.protocol('WM_DELETE_WINDOW', self.OnClosing)
        if self.Parent is None:
            self.window.mainloop()

    def CreateUI(self, parent):
        pass

    def OnClosing(self):
        if self.Parent is not None:
            if self.model:
                self.model.Geometry.WriteGeomInfo(self.window, self.Title)
            self.Parent.deiconify()
            self.Parent = None
        if self.model:
            self.model.WriteConfigFile()
        self.window.destroy()
        if self.OnClosed:
            self.OnClosed()

    def AddBackButton(self, parent, r, c):
        UIFactory.AddButton(parent, 'Back', r, c, self.OnClosing, None, 19)
