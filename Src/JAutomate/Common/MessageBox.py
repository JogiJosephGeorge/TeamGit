import tkMessageBox as messagebox
#import Tkinter as tk
#import ttk


class MessageBox:
    @classmethod
    def ShowMessage(cls, msg, caption = 'KLA Runner'):
        print msg
        messagebox.showinfo(caption, msg)

    @classmethod
    def YesNoQuestion(cls, title, msg):
        print msg
        return messagebox.askquestion(title, msg) == 'yes'

'''
class InputMessageBox:
    def __init__(self, parent, title, CallBackOnOk):
        self.callBackOnOk = CallBackOnOk

        width = 300
        parentPosX = parent.winfo_x()
        parentPosY = parent.winfo_y()
        geom = "{}x{}+{}+{}".format(width, 100, parentPosX, parentPosY)
        #geom = "+{}+{}".format(parentPosX, parentPosY)

        self.window = tk.Tk()
        self.window.title(title)
        self.window.overrideredirect(1)
        self.window.geometry(geom)

        self.textBox = tk.Entry(self.window)
        self.textBox.focus_set()
        self.textBox.grid(row=0, column=0, sticky='we', padx=10, pady=10, columnspan=2)

        frame = ttk.Frame(self.window)
        frame.grid(row=1, column=1, sticky='we', padx=10, pady=10)

        button = tk.Button(frame, text='Ok', command=self.OnReadLineOk)
        #button['width'] = 20
        button.grid(sticky='w')

        self.window.mainloop()

    def OnReadLineOk(self):
        msg = self.textBox.get()
        self.window.destroy()
        self.callBackOnOk(msg)
'''
