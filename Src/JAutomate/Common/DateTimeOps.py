
class DateTimeOps:
    @classmethod
    def IsSameDate(cls, datetime1, datetime2, dayStarts):
        if datetime1 is None or datetime2 is None:
            return False
        a1 = datetime1 - dayStarts
        b1 = datetime2 - dayStarts
        return a1.day == b1.day and a1.month == b1.month and a1.year == b1.year

    @classmethod
    def Strftime(cls, myTimeDelta, format):
        hours, remainder = divmod(myTimeDelta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return format.format(int(hours), int(minutes), int(seconds))
