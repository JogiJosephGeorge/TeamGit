import os
import Tkinter as tk
import ttk

from Common.MessageBox import MessageBox


class UIFactory:
    @classmethod
    def CreateWindow(cls, parent, title, startPath):
        if parent is None:
            window = tk.Tk()
        else:
            parent.withdraw()
            window = tk.Toplevel(parent)
        window.title(title)
        iconPath = startPath + r'/DataFiles/Plus.ico'
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
    def AddTextBox(cls, parent, text, r, c, width = 0):
        txtVar = tk.StringVar()
        entry = tk.Entry(parent, width=width, textvariable = txtVar)
        txtVar.set(text)
        entry.grid(row=r, column=c, sticky='w')
        return txtVar

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


class CheckBoxCreator:
    def __init__(self):
        self.CheckBoxes = dict()

    def AddCheckBox(self, parent, r, c, txt, model, attrName, msgOn, msgOff, showMsgOn, showMsgOff):
        isChecked = getattr(model, attrName) # self.model.__dict__[modelVar] also works
        args = (model, attrName, msgOn, msgOff, showMsgOn, showMsgOff)
        self.CheckBoxes[attrName] = UIFactory.AddCheckBox(parent, txt, isChecked, r, c, self.OnClickCheckBox, args)

    def OnClickCheckBox(self, model, attrName, msgOn, msgOff, showMsgOn, showMsgOff):
        isChecked = self.CheckBoxes[attrName].get()
        setattr(model, attrName, isChecked)
        msg = msgOn if isChecked else msgOff
        if msg:
            if (isChecked and showMsgOn) or ((not isChecked) and showMsgOff):
                MessageBox.ShowMessage(msg)
            else:
                print msg


class TextBoxCreator:
    def __init__(self, model):
        self.model = model
        self.TextVars = dict()
        self.Validators = dict()

    def Add(self, parent, r, c, attrName, validate, width = 19):
        txt = getattr(self.model, attrName, '-')
        self.TextVars[attrName] = UIFactory.AddTextBox(parent, txt, r, c, width)
        self.Validators[attrName] = validate

    def UpdateModel(self):
        for key in self.TextVars:
            txt = self.TextVars[key].get()
            validate = self.Validators[key]
            if validate:
                val = validate(txt)
                if val:
                    setattr(self.model, key, val)
            else:
                setattr(self.model, key, txt)
