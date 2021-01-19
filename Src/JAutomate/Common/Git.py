import subprocess

from OsOperations import OsOperations

class Git:
    @classmethod
    def GetBranch(cls, source):
        params = ['git', '-C', source, 'branch']
        output = OsOperations.ProcessOpen(params)
        isCurrent = False
        for part in output.split():
            if isCurrent:
                return part
            if part == '*':
                isCurrent = True

    @classmethod
    def Git(cls, source, cmd):
        OsOperations.Call('git -C {} {}'.format(source, cmd))

    @classmethod
    def GitSilent(cls, source, cmd):
        return OsOperations.Popen('git -C {} {}'.format(source, cmd), None, True)

    @classmethod
    def ModifiedFiles(cls, source):
        params = ['git', '-C', source, 'status', '-s']
        return OsOperations.ProcessOpen(params).split('\n')[:-1]

    @classmethod
    def Clean(cls, source, options):
        cls.Git(source, 'clean ' + options)

    @classmethod
    def ResetHard(cls, source):
        cls.Git(source, 'reset --hard')

    @classmethod
    def SubmoduleUpdate(cls, model):
        source = model.Source
        cls.Git(source, 'submodule update --init --recursive')
        cls.Git(source, 'submodule foreach git reset --hard') # It seems this is not working
        cls.Git(source, 'submodule sync --recursive')
        cls.Git(source, 'submodule update')
        print 'Git All Submodules Updated.'

    @classmethod
    def OpenGitGui(cls, model):
        param = [ 'git-gui', '--working-dir', model.Source ]
        print 'Staring Git GUI'
        subprocess.Popen(param)

    @classmethod
    def OpenGitBash(cls, model):
        gitBin = model.GitBin.replace('Program Files (x86)', 'PROGRA~2')
        gitBin = gitBin.replace('Program Files', 'PROGRA~1')
        par = 'start {}/sh.exe --cd={}'.format(gitBin, model.Source)
        OsOperations.System(par, 'Staring Git Bash')

    @classmethod
    def FetchPull(cls, model):
        Git.Git(model.Source, 'pull')
        print 'Git fetch and pull completed.'

    @classmethod
    def Commit(cls, model, msg):
        cls.Git(model.Source, 'add -A')
        cls.Git(model.Source, 'commit -m "' + msg + '"')

    @classmethod
    def RevertLastCommit(cls, source):
        cls.Git(source, 'reset --mixed HEAD~1')

    @classmethod
    def GetLocalBranches(cls, source):
        branches = Git.GitSilent(source, 'branch')
        if len(branches) == 0:
            return []
        return branches.splitlines()
