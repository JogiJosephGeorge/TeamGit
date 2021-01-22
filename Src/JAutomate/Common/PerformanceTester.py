from datetime import datetime


class PerformanceTester:
    lastTime = datetime.now()

    @classmethod
    def ResetNow(cls):
        cls.lastTime = datetime.now()

    @classmethod
    def Print(cls, msg):
        t = datetime.now()
        print '{} {}> {}'.format(t.time(), (t - cls.lastTime), msg)
        cls.lastTime = t
