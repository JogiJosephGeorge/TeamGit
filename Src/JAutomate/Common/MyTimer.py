import time
import threading


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
            time.sleep(self.initWait)
        while True:
            if self.stopped():
                return
            if self.target(*self.args):
                return
            time.sleep(self.interval)
