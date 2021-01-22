import sys

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
