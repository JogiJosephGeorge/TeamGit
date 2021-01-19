
class NumValDict(dict):
    def Add(self, key, value):
        if key in self:
            self[key] = self[key] + value
        else:
            self[key] = value

class TestNumValDict:
    def __init__(self):
        self.StrInt()

    def StrInt(self):
        d = NumValDict()
        d.Add('hi', 23)
        d.Add('hi', 5)
        d.Add('bye', 3)
        Test.Assert(d, {'bye': 3, 'hi': 28})
