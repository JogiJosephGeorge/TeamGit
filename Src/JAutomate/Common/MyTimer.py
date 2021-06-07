import time
import threading
import datetime


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
            #print str(datetime.datetime.now()) + ' JJG MyTimer.run() Before Init Wait' + str(self.args[0])
            time.sleep(self.initWait)
            #print str(datetime.datetime.now()) + ' JJG MyTimer.run() After Init Wait' + str(self.args[0])
        while True:
            #print str(datetime.datetime.now()) + ' JJG MyTimer.run() ' + str(self.args[0]) + ' Inside While loop'
            if self.stopped():
                #print str(datetime.datetime.now()) + ' JJG MyTimer.run() ' + str(self.args[0]) + ' While loop stopped'
                return
            if self.target(*self.args):
                #print str(datetime.datetime.now()) + ' JJG MyTimer.run() ' + str(self.args[0]) + ' Target return true'
                return
            time.sleep(self.interval)
