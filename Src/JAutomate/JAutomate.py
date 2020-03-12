from collections import OrderedDict
import json
import os
import re
import subprocess
import sys
import shutil

class JAutomate:

	sources = []

	def PrintMenu(self, srcNumber, testName):
		try:
			source = self.GetSource(srcNumber)
			branch = self.GetBranch(source)
			data = [
				['Src', source],
				['Test', testName],
				['Branch', branch],
				['-'],
				[1, 'Open Python'],
				[2, 'Run Auto test'],
				[3, 'Run Auto test (Startup only)'],
				[4, 'Run Handler alone'],
				[5, 'Run MMi from Src'],
				[6, 'Run Handler and MMi'],
				[],
				[10, 'Install MMi'],
				[11, 'Open Solution CIT100'],
				[12, 'Open Solution CIT100Simulator'],
				[14, 'Open Solution Mmi'],
				[15, 'Open Solution MockLicense'],
				[16, 'Open Solution Converters'],
				[],
				[20, 'Open Test Folder'],
				[21, 'Open Local Differences'],
				[22, 'Change Test'],
				[23, 'Print Missing IDs in mmi.h'],
				[24, 'Copy xPort_IllumReference.xml'],
				[25, 'Modify VisionSystem'],
				[26, 'Copy Mock License'],
				[27, 'Print All Branches'],
				[],
				[91, 'Build'],
				[92, 'Clean Build'],
				[99, 'Kill All'],
				[0, 'EXIT']
			]
			
			self.PrintTable(data)
			userIn = input('Type the number then press ENTER: ')
			exit (userIn)
		except Exception as ex:
			print(ex)
			exit (999)

	def PrintTable(self, data):
		try:
			colCnt = 0
			colWidths = []

			for line in data:
				i = 0
				for cell in line:
					if len(colWidths) > i:
						colWidths[i] = max(colWidths[i], len(str(cell)))
					else:
						colWidths.append(len(str(cell)))
					i = i + 1
					colCnt = max(colCnt, i)

			chTopLef = chr(218)
			chTopMid = chr(194)
			chTopRig = chr(191)
			chMidLef = chr(195)
			chMidMid = chr(197)
			chMidRig = chr(180)
			chBotLef = chr(192)
			chBotMid = chr(193)
			chBotRig = chr(217)
			chVertic = chr(179)
			chHorizo = chr(196)

			self.PrintLine(colWidths, chTopLef, chTopMid, chTopRig, chHorizo)

			for line in data:
				if len(line) == 0:
					self.PrintLine(colWidths, chVertic, chVertic, chVertic, ' ')
				elif len(line) == 1 and line[0] == '-':
					self.PrintLine(colWidths, chMidLef, chMidMid, chMidRig, chHorizo)
				else:
					toPrint = chVertic
					for i in range(0, colCnt):
						cell = ''
						if i < len(line):
							cell = str(line[i])
						cell = cell.ljust(colWidths[i])
						toPrint += cell + ' ' + chVertic
					print toPrint
			self.PrintLine(colWidths, chBotLef, chBotMid, chBotRig, chHorizo)
		except Exception as ex:
			print(ex)

	def PrintLine(self, colWidths, left, mid, right, fill):
		line = left
		colCnt = len(colWidths)
		for i in range(0, colCnt - 1):
			line += fill * (colWidths[i] + 1) + mid
		line += fill * (colWidths[-1] + 1) + right
		print line

	def PrintTable1(self, data):
		try:
			for line in data:
				for cell in line:
					print cell,
				print ''
		except Exception as ex:
			print(ex)

	def SelectTest(self):
		try:
			data = [
				['Num', 'Test Name'],
				['-']
			]
			fileName = 'Tests.txt' 
			with open(fileName) as file:
				lines = file.read().splitlines()
			i = 1
			for line in lines:
				# print (str(i) + ' ' + line)
				data.append([i, line])
				i += 1

			self.PrintTable(data)

			number = input('Select number : ')
			number -= 1

			selLine = lines[number]
			if len(selLine) == 0:
				print 'Wrong input...'
			else:
				lines.remove(selLine)
				lines.append(selLine)
				
				with open(fileName, 'w') as f:
					f.write('\n'.join(lines))
		except Exception as ex:
			print(ex)

	def OpenLocalDif(self, srcNumber):
		try:
			source = self.GetSource(srcNumber)
			par = 'C:\\Progra~1\\TortoiseGit\\bin\\TortoiseGitProc.exe /command:diff /path:"' + source + '"'
			print 'par : ' + par
			os.system(par)
			# proc = subprocess.Popen(['C:\\Progra~1\\TortoiseGit\\bin\\TortoiseGitProc.exe', '/command:diff', '/path:"' + source + '"'], stdin=subprocess.PIPE)
			# s,e = proc.communicate(None)
			# proc.poll()
			# print 'Out : ' + str(s)
			# print 'Err : ' + str(e)
		except Exception as ex:
			print(ex)

	def CopyDir(self, Src, Des):
		try:
			par = 'XCOPY /S /Y "' + Src + '" "' + Des + '"'
			print 'Src : ' + Src
			print 'Des : ' + Des
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def CopyMockLicense(self, srcNumber, Platform, Config):
		try:
			print '*' * 10 + ' NOT IMPLEMENTED ' + '*' * 10
			# self.CopyFile(MockPath, 'C:/Icos')
		except Exception as ex:
			print(ex)

	def CopyFile(self, Src, Des):
		try:
			par = 'COPY /Y "' + Src + '" "' + Des + '"'
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def ModifyVisionSystem(self, srcNumber):
		try:
			source = self.GetSource(srcNumber)

			line = 'shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))'
			oldLine = ' ' + line
			newLine = ' #' + line
			fileName = source + '\\libs\\testing\\visionsystem.py'
			with open(fileName) as f:
				newText = f.read().replace(oldLine, newLine)
			with open(fileName, "w") as f:
				f.write(newText)

		except Exception as ex:
			print(ex)

	def RunSlots(self, slots, canPause):
		try:
			slots = slots.split('_')
			vmWS = "C:\\Program Files (x86)\\VMware\\VMware Workstation\\"
			vmRunExe = vmWS + "vmrun.exe"
			vmWareExe = vmWS + "vmware.exe"
			vmxGenericPath = r'C:\\MVS8000\\slot{}\\MVS8000_stage2.vmx'

			output = subprocess.Popen([vmRunExe, '-vp', '1', 'list'], stdout=subprocess.PIPE).communicate()[0]
			runningSlots = []
			searchPattern = r'C:\\MVS8000\\slot(\d*)\\MVS8000_stage2\.vmx'
			for line in output.split():
				m = re.search(searchPattern, line, re.IGNORECASE)
				if m:
					runningSlots.append(m.group(1))

			for slot in slots:
				vmxPath = vmxGenericPath.format(slot)
				if slot in runningSlots:
					print 'Slot : ' + str(slot) + ' restarted.'
					subprocess.Popen([vmRunExe, '-vp', '1', 'reset', vmxPath])
				else:
					subprocess.Popen([vmWareExe, vmxPath])
					print 'Start Slot : ' + str(slot)
					raw_input("Press any key to continue...")
					print 'Slot : ' + str(slot) + ' started.'
		except Exception as ex:
			print(ex)

	def RunTest(self, JTestPath, JTestName, JStartUp, JDebugVision, JCopyMmi, JConfig, JPlatform):
		try:
			JStartUp = True if JStartUp == "1" else False
			JDebugVision = True if JDebugVision == "1" else False
			JCopyMmi = True if JCopyMmi == "1" else False
			JConfig1 = 'r' if JConfig == 'Release' else 'd'

			# print 'JTestPath    : ' + JTestPath
			# print 'JTestName    : ' + JTestName
			# print 'JStartUp     : ' + str(JStartUp)
			# print 'JDebugVision : ' + str(JDebugVision)
			# print 'JCopyMmi     : ' + str(JCopyMmi)
			# print 'JConfig      : ' + JConfig
			# print 'JPlatform    : ' + JPlatform
			# raw_input('Press any key to continue...')

			sys.path.append(os.path.abspath(JTestPath));
			import my

			my.c.startup = JStartUp
			my.c.debugvision = JDebugVision
			my.c.copymmi = JCopyMmi
			my.c.console_config = JConfig1
			my.c.simulator_config = JConfig1

			if JConfig == 'Release':
			   if JPlatform == 'Win32':
				  my.c.mmiBuildConfiguration = 'release'
			   else:
				  my.c.mmiBuildConfiguration = 'releasex64'
			else:
			   if JPlatform == 'Win32':
				  my.c.mmiBuildConfiguration = 'debug'
			   else:
				  my.c.mmiBuildConfiguration = 'debugx64'
			my.c.platform = JPlatform
			my.c.mmiConfigurationsPath = "D:\\"
			my.c.mmiSetupsPath = 'D:\MmiSetups'
			#print str(my.c)

			my.run(JTestName)
		except Exception as ex:
			print(ex)

	def KillTask(self, exeName = ''):
		try:
			print 'exeName : ' + exeName
			par = 'KillAll ' + exeName
			print 'par : ' + par
			os.system(par)
		except Exception as ex:
			print(ex)

	def StartHandler(self, source, testName):
		try:
			self.KillTask()

			consoleExe = source + '/handler/cpp/bin/Win32/debug/system/console.exe'
			testTempDir = source + '/handler/tests/' + testName + '~'
			par = 'start ' + consoleExe + ' ' + testTempDir
			print par
			os.system(par)

			simulatorExe = source + '/handler/Simulator/ApplicationFiles/bin/x86/Debug/CIT100Simulator.exe'
			handlerSysPath = source + '/handler/cpp/bin/Win32/debug/system'
			par = 'start ' + simulatorExe + ' ' + testTempDir + ' ' + handlerSysPath
			print par
			os.system(par)
		except Exception as ex:
			print(ex)

	def StartMMi(self, source, slots, platform, config):
		try:
			self.KillTask('MMi.exe')
			self.RunSlots(slots, True)

			MmiPath = source + '\\mmi\\mmi\\Bin\\' + platform + '\\' + config
			print 'MmiPath  :' + MmiPath
			MockPath = source + '\\mmi\\mmi\\mmi_stat\\integration\\code\\MockLicenseDll\\' + platform + '\\' + config
			print 'MockPath : ' + MockPath

			self.CopyFile(MockPath, MmiPath)
			self.CopyFile('D:\\QuEST\\MyProjects\\xPort\\xPort_IllumReference.xml', 'C:\\icos\\xPort')

			self.Timeout(8)

			mmiExe = MmiPath + '\\Mmi.exe'
			par = 'start ' + mmiExe
			print par
			os.system(par)
		except Exception as ex:
			print(ex)

	def Timeout(self, seconds):
		try:
			par = 'timeout ' + str(seconds)
			print par
			os.system(par)
		except Exception as ex:
			print(ex)

	def PrintBranches(self, branchNums = ''):
		try:
			self.ReadConfigFile()
			data = [
				['Source', 'Branch'],
				['-']
			]
			tempSources = []
			if branchNums == '':
				tempSources = self.sources
			else:
				for branchNum in branchNums.split():
					num = int(branchNum)
					if num > len(self.sources):
						print 'Wrong source index is given !!!'
					else:
						tempSources.append(self.sources[num - 1])
			for source in tempSources:
				data.append([source, self.GetBranch(source)])
			self.PrintTable(data)
		except Exception as ex:
			print(ex)

	def GetBranch(self, source):
		try:
			params = ['git', '-C', source, 'branch']
			output = subprocess.Popen(params, stdout=subprocess.PIPE).communicate()[0]
			isCurrent = False
			for part in output.split():
				if isCurrent:
					return part
				if part == '*':
					isCurrent = True
		except Exception as ex:
			print(ex)

	def PrintMissingIds(self, srcNumber):
		try:
			source = self.GetSource(srcNumber)
			lastId = 1
			fileName = source + '\mmi\mmi\mmi_lang\mmi.h'
			print 'Missing IDs in ' + fileName
			singles = []
			sets = []
			with open(fileName) as file:
				lines = file.read().splitlines()
			for line in lines:
				parts = line.split()
				if len(parts) == 3:
					id = int(parts[2])
					if lastId + 1 < id:
						setStart = lastId + 1
						setEnd = id - 1
						if setStart == setEnd:
							singles.append(str(setStart).rjust(5))
						else:
							sets.append(('[' + str(setStart)).rjust(6) + ', ' + (str(setEnd) + ']').ljust(6))
					lastId = max(lastId, id)
			for i in range(0, len(singles)):
				if i % 15 == 0:
					print 
				print singles[i],
			for i in range(0, len(sets)):
				if i % 6 == 0:
					print 
				print sets[i],
		except Exception as ex:
			print(ex)

	def ReadConfigFile(self):
		with open('JAutomate.ini') as f:
			data = json.load(f)
		self.sources = data['sources']

	def GetSource(self, srcNumber):
		try:
			self.ReadConfigFile()
			srcNumber = int(srcNumber)
			if len(self.sources) < srcNumber:
				print 'Wrong index'
				return
			return self.sources[srcNumber - 1]
		except Exception as ex:
			print(ex)
