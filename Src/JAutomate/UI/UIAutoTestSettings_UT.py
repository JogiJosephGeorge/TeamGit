from Common.Test import Test
from UI.UIAutoTestSettings import FilterTestSelector

class FilterTestSelector_UT:
    def __init__(self):
        allFiles = self.CreateFilterTestSelector().GetAllTests()
        Test.Assert(len(allFiles) > 1000, True, 'TestCount')
        #Test.Assert(allFiles[2], 'Bora/changeRejectBinConfigurationForRescanBatch', 'TestName')
        Test.Assert(allFiles[2], 'Bora/ColorCheckOnX1loader', 'TestName')

    class Model_UT:
        def __init__(self):
            pass

    def CreateFilterTestSelector(self):
        model = self.Model_UT()
        model.Source = 'D:/CI/Src1'
        filterTestSelector = FilterTestSelector()
        filterTestSelector.model = model
        return filterTestSelector