import tkMessageBox as messagebox

class MessageBox:
    @classmethod
    def ShowMessage(cls, msg, caption = 'KLA Runner'):
        print msg
        messagebox.showinfo(caption, msg)

    @classmethod
    def YesNoQuestion(cls, title, msg):
        print msg
        return messagebox.askquestion(title, msg) == 'yes'
