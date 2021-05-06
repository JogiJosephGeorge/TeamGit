import webbrowser

from Common.Test import Test


class JiraOpener:
    def __init__(self, model):
        self.Model = model
        self.TeamCity = 'http://icoslx01/teamcity/buildConfiguration/'

    def OpenIntegrationTests(self):
        self.OpenJira(False)

    def OpenUnitTests(self):
        self.OpenJira(True)

    def OpenJira(self, isUnitTest):
        jiraPath = self.GetPath(isUnitTest)
        webbrowser.get('windows-default').open(jiraPath)

    def GetPath(self, isUnitTests):
        branch = self.Model.Branch.replace('/', '%2F')
        if branch.startswith('feature'):
            if isUnitTests:
                pathBase = 'Git_Test_MmiVscppunitTests?branch={}&mode=builds'
            else:
                branch = branch[10:]
                pathBase = 'CiSw_IntegrationTests_FeatureBranches_IntegrationTestOverview?branch={}&mode=builds'
        else:
            if isUnitTests:
                pathBase = 'Git_Test_MmiVscppunitTests?branch={}&buildTypeTab=overview&mode=builds#all-projects'
            else:
                pathBase = 'Git_Test_TestWithMmiSetup_CandidateBranchesRealMmiTestsWithSetup?branch={}&buildTypeTab=overview&mode=builds#all-projects'
        return self.TeamCity + pathBase.format(branch)

class JiraOpenerTest:
    def __init__(self):
        self.TestFeatureBranch()
        self.TestCandidateBranch()

    def GetInstance(self, branch):
        class JiraModel:
            def __init__(self, branch):
                self.Branch = branch
        return JiraOpener(JiraModel(branch))

    def TestFeatureBranch(self):
        jio = self.GetInstance('feature/mmi/10.5a2/mci-33771')

        p1 = jio.TeamCity + 'CiSw_IntegrationTests_FeatureBranches_IntegrationTestOverview?branch=mmi%2F10.5a2%2Fmci-33771&mode=builds'
        Test.Assert(p1, jio.GetPath(False), 'Integration Tests')

        p2 = jio.TeamCity + 'Git_Test_MmiVscppunitTests?branch=feature%2Fmmi%2F10.5a2%2Fmci-33771&mode=builds'
        Test.Assert(p2, jio.GetPath(True), 'Unit Tests')

    def TestCandidateBranch(self):
        jio = self.GetInstance('candidate/10.5_11.0a11')

        p1 = jio.TeamCity + 'Git_Test_TestWithMmiSetup_CandidateBranchesRealMmiTestsWithSetup?branch=candidate%2F10.5_11.0a11&buildTypeTab=overview&mode=builds#all-projects'
        Test.Assert(p1, jio.GetPath(False), 'Integration Tests')

        p2 = jio.TeamCity + 'Git_Test_MmiVscppunitTests?branch=candidate%2F10.5_11.0a11&buildTypeTab=overview&mode=builds#all-projects'
        Test.Assert(p2, jio.GetPath(True), 'Unit Tests')
