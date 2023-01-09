import subprocess

from Common.MessageBox import MessageBox
from OsOperations import OsOperations

class Git:
    GitPath = 'C:/PROGRA~1/Git/cmd/git'
    GitBin = 'C:/PROGRA~1/Git/bin'

    @classmethod
    def GetBranch(cls, source):
        params = [cls.GitPath, '-C', source, 'branch']
        output = OsOperations.ProcessOpen(params)
        isCurrent = False
        for part in output.split():
            if isCurrent:
                return part
            if part == '*':
                isCurrent = True

    @classmethod
    def GetCommitId(cls, source, localBranch=''):
        cmd = 'log --pretty=format:"%h" -n 1'
        if len(localBranch) > 0:
            cmd += ' heads/' + localBranch
        commitId = cls.GitSilent(source, cmd)
        return commitId.replace('\r', '').replace('\n', '')

    @classmethod
    def Git(cls, source, cmd):
        OsOperations.Call(cls.GitPath + ' -C {} {}'.format(source, cmd))

    @classmethod
    def ProcessOpen(cls, cmd):
        return OsOperations.ProcessOpen(cls.GitPath + ' {}'.format(cmd))

    @classmethod
    def GitSilent(cls, source, cmd):
        params = cls.GitPath + ' -C {} {}'.format(source, cmd)
        return OsOperations.Popen(params, None, True)

    @classmethod
    def ModifiedFiles(cls, source):
        params = [cls.GitPath, '-C', source, 'status', '-s']
        return OsOperations.ProcessOpen(params).split('\n')[:-1]

    @classmethod
    def Clean(cls, source):
        cls.Git(source, 'clean -fd')

    @classmethod
    def ResetHard(cls, source):
        cls.Git(source, 'reset --hard')

    @classmethod
    def SubmoduleUpdate(cls, model):
        if model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = model.Src.GetCur()
        source = curSrc.Source
        cls.Git(source, 'submodule sync --recursive')
        cls.Git(source, 'submodule update --init --recursive')
        #cls.Git(source, 'submodule foreach git reset --hard') # It seems this is not working
        #cls.Git(source, 'submodule update')
        print 'Git All Submodules Updated.'

    @classmethod
    def OpenGitGui(cls, model):
        if model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = model.Src.GetCur()
        param = [ cls.GitPath + '-gui', '--working-dir', curSrc.Source ]
        print 'Staring Git GUI'
        subprocess.Popen(param)

    @classmethod
    def OpenGitBash(cls, model):
        if model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = model.Src.GetCur()
        par = 'start {}/sh.exe --cd={}'.format(cls.GitBin, curSrc.Source)
        OsOperations.System(par, 'Staring Git Bash')

    @classmethod
    def FetchPull(cls, model):
        if model.Src.IsEmpty():
            MessageBox.ShowMessage('No source available.')
            return
        curSrc = model.Src.GetCur()
        Git.Git(curSrc.Source, 'pull')
        print 'Git fetch and pull completed.'

    @classmethod
    def Commit(cls, model, msg):
        curSrc = model.Src.GetCur()
        cls.Git(curSrc.Source, 'add -A')
        cls.Git(curSrc.Source, 'commit -m "' + msg + '"')

    @classmethod
    def RevertLastCommit(cls, source):
        cls.Git(source, 'reset --mixed HEAD~1')

    @classmethod
    def GetLocalBranches(cls, source):
        branches = Git.GitSilent(source, 'branch')
        if len(branches) == 0:
            return []
        return branches.splitlines()
