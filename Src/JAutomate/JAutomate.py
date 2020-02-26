import os
import re
import subprocess
import sys

class JAutomate:
	def PrintMenu(self, source, testName):
		try:
			menu = {}
			menu[1] = 'Open Python'
			menu[2] = 'Run Auto test'
			menu[3] = 'Run Handler alone'
			menu[4] = 'Run MMi alone'
			menu[5] = 'Run Handler and MMi'
			menu[6] = 'Copy xPort_IllumReference.xml'
			menu[7] = 'Copy backup VisionSystem'
			menu[8] = 'Open Test Folder'
			menu[9] = 'Change Test'
			menu[10] = 'Install MMi'
			menu[11] = 'Open Solution CIT100'
			menu[12] = 'Open Solution CIT100Simulator'
			menu[13] = 'Open Solution Mmi'
			menu[14] = 'Open Solution MockLicense'
			menu[15] = 'Open Solution Converters'
			menu[20] = 'Open Local Differences'
			menu[21] = 'Print Missing IDs in mmi.h'
			menu[99] = 'Kill All'
			menu[0] = 'EXIT'
			
			totalLen = 60
			print ''
			print ''
			print '#' + '-' * totalLen + '#'
			print '#   Source    : ' + source.ljust(totalLen - 15) + '#'
			print '#   Test Name : ' + testName.ljust(totalLen - 15) + '#'
			print '#' + '.' * totalLen + '#'
			print '#' + ' ' * totalLen + '#'
			for number in menu:
				print '#' + str(number).rjust(5) + ' - ' + menu[number].ljust(totalLen - 8) + '#'
			print '#' + ' ' * totalLen + '#'
			print '#' + '-' * totalLen + '#'
			userIn = input('Type the number then press ENTER: ')
			exit (userIn)
		except Exception as ex:
			print(ex)
			exit (999)

	def SelectTest(self):
		try:
			fileName = 'Tests.txt' 
			with open(fileName) as file:
				lines = file.read().splitlines()
			i = 1
			for line in lines:
				print (str(i) + ' ' + line)
				i += 1

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

	def RunSlots(self, slots, canPause):
		try:
			slots = slots.split('_')

			vmRunExe = "C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmrun.exe"
			vmWareExe = "C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmware.exe"
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

	def PrintMissingIds(self, source):
		try:
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
