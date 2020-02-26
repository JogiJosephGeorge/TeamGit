import os
import ConfigParser
import testhost
import processtree
import process
import testutils
import ostools
import subprocess
import xml.etree.ElementTree
import shutil
import extratestarguments
import zipfile
import time
import symlink
import threading
import winregutils
import tarfile
import communicationlib
import mmiSender
import console
import socketutils
import re
import mmiModelUtils
import MmiUtilities.CameraImage as CameraImage
import wafermaputil.MvsFileConverter as MvsFileConverter
import MmiComponentModelParser
import sys
import tags
import settings
import RunMmiSetup
import virtualbox
from shutil import copyfile

ICOS_PATH = r"c:\icos"



class MmiUninstaller:
   def __init__(self, mmiPath):
      self.mmiPath = mmiPath
      self.mmiInstallRegistryPath = r"SOFTWARE\ICOS Vision Systems\MMI Install"

   def uninstall(self):
      print "Uninstalling MMI..."
      installedBranch, installedVersion = self.getInstalledVersion()
      if installedVersion is not None:
         parentKey = r"SOFTWARE\ICOS Vision Systems\Icos MMI " + installedVersion
         if installedBranch is not None:
            branchKey = parentKey + "\\" + installedBranch
            winregutils.deleteKey(branchKey)
         winregutils.deleteKey(parentKey)

      winregutils.deleteKey(self.mmiInstallRegistryPath)
      installShieldId = "{B88B1750-8B30-11D5-ABFB-000102D81FAF}"
      winregutils.deleteKey(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" + "\\" + installShieldId)
      winregutils.deleteValue(r"SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs",
                              r"C:\Windows\system32\drivers\MVSdispl.sys")
      installShieldData = os.path.join("C:/Program Files (x86)/InstallShield Installation Information",
                                       installShieldId)
      if os.path.exists(installShieldData):
         ostools.rmtreeRobust(installShieldData)

      self.removeMmiPath()

   def removeMmiPath(self):
      if os.path.exists(self.mmiPath):
         print "Removing '{}'...".format(self.mmiPath)
         symlink.removeSymlinks(self.mmiPath)
         # When the 1 second time out of test.test_support.rmtree() is not enough, keep trying.
         while len(os.listdir(self.mmiPath)) > 0:
            try:
               for entry in os.listdir(self.mmiPath):
                  fullEntry = os.path.join(self.mmiPath, entry)
                  if os.path.isdir(fullEntry):
                     ostools.rmtreeRobust(fullEntry)
                  else:
                     ostools.removeRobust(fullEntry)
            except WindowsError:
               pass
         # Even when it's gone, doesn't mean you won't get Access Denied errors. Wait a little while.
         time.sleep(0.5)

   def getInstalledVersion(self):
      return (winregutils.getValue(self.mmiInstallRegistryPath, "Version"),
              winregutils.getValue(self.mmiInstallRegistryPath, "VersionString"))

def getMMISourceRoot():
   sourceRootParameter = "mmiSourceRoot"
   return extratestarguments.all[sourceRootParameter] if sourceRootParameter in extratestarguments.all else ""

def useLocalMmiSources():
   sourceRootParameter = "mmiSourceRoot"
   copyMmiParameter = "copyMmi"
   sourceRoot = getMMISourceRoot()
   copyMmi = extratestarguments.all[copyMmiParameter] if copyMmiParameter in extratestarguments.all else True # Default True, look at root if copyMmi absent
   if not copyMmi or not sourceRoot:
      print("Using MMI installation binaries because " + (copyMmiParameter + " not set" if copyMmi else sourceRootParameter + " not set or empty"))
      return False, ""
   return True, sourceRoot

class MmiInstaller:
   def __init__(self, mmiPath, configPath, testPath, setups, branch, debugInfo):
      self.mmiPath = mmiPath
      self.configPath = configPath
      self.testPath = testPath
      self.setups = setups
      self.branch = branch
      self.debugInfo = debugInfo

   def getBranchSetups(self, branch):
      path = os.path.join(self.setups, branch)
      assert os.path.exists(path), "{} not found in {}, wrong branch name?".format(path, self.setups)
      return path

   def getStandardInstaller(self, setups, version):
      return os.path.join(setups, version, "_Standard installer")

   def getNSInstaller(self, setups, version):
      if "mmiPlatform" in extratestarguments.all.keys():
 
        platform = extratestarguments.all["mmiPlatform"].lower()
        print("MMI platform is :", platform)
      else:
          platform = "win32"
      if platform == "win32":
          return os.path.join(self.getStandardInstaller(setups, version), 'MMI_'+version + "_setup.exe")
      if platform == "x64":
          return os.path.join(self.getStandardInstaller(setups, version), 'MMI_'+version + "_x64_setup.exe")

   def getSetupMTime(self, setups, version):
      return os.path.getmtime(os.path.join(self.getStandardInstaller(setups, version), "data1.cab"))

   def getNSSetupMTime(self, setups, version):
      return os.path.getmtime(self.getNSInstaller(setups, version))

   def getDebugInfoPath(self, setups, version):
      return os.path.join(setups, version, "_Debug info","mmi_" + version + ".DebugInfo.zip")

   def extractDebugInfo(self, debugInfo):
      print "Extracting debug information..."
      with zipfile.ZipFile(debugInfo) as theZip:
         for zipMember in theZip.namelist():
            fileName = os.path.basename(zipMember)
            if fileName.endswith(".pdb"):
               source = theZip.open(zipMember)
               targetFileName = os.path.join(self.mmiPath, fileName)
               target = file(targetFileName, "wb")
               with source, target:
                  shutil.copyfileobj(source, target)
                  print "'{}' extracted".format(targetFileName)

   def copyFromSnapshot(self, snapshot):
      print "Copying MMI installation from snapshot '{}'...".format(snapshot)
      tar = tarfile.open(snapshot)

      copyLocalBinaries, _ = useLocalMmiSources()
      if copyLocalBinaries:         
         def filterBinaries(members):
            for tarinfo in members:
               extension = (os.path.splitext(tarinfo.name)[1]).lower()
               if extension not in [".exe", ".dll"]:
                  yield tarinfo
         tar.extractall(path="c:/", members=filterBinaries(tar))
      else:
         tar.extractall(path="c:/")

      tar.close()

   def createSnapshot(self, snapshot):
      print "Creating snapshot '{}'...".format(snapshot)
      tar = tarfile.open(snapshot, "w")
      try:
         tar.add(self.mmiPath)
      except WindowsError:
         print "Unable to create snapshot, removing {}...".format(snapshot)
         tar.close()
         ostools.removeRobust(snapshot)
         return
      tar.close()

   def install(self):
      mmiSetupExeParameter = "mmiSetupExe"
      try:
         mmiSetupExe = extratestarguments.all[mmiSetupExeParameter]
      except KeyError:
         mmiSetupExe = ""

      mmiBranchSetups = self.getBranchSetups(self.branch)
      builds = []
      for item in os.listdir(mmiBranchSetups):
         if os.path.isdir(os.path.join(mmiBranchSetups, item, '_Standard installer')):
            builds.append(item)
      assert len(builds) > 0
      convert = lambda text: int(text) if text.isdigit() else text.lower()
      alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
      latestVersion = sorted(builds,key=alphanum_key)[-1]
      latestNSSetup = self.getNSInstaller(mmiBranchSetups, latestVersion)
      if mmiSetupExe == "":
         print latestNSSetup
         if os.path.exists(latestNSSetup):
            useNsisSetup=True
         else:
            useNsisSetup=False
      else:
         useNsisSetup = True
         latestNSSetup=mmiSetupExe

      latestDebugInfo = self.getDebugInfoPath(mmiBranchSetups, latestVersion)

      base, tail = os.path.split(self.mmiPath)
      snapshot = os.path.join(base, tail + "-" + self.branch + "-snapshot.tar")
      useSnapshot = False

      canConnectToBranchSetups = os.path.exists(mmiBranchSetups)
      if not canConnectToBranchSetups and os.path.exists(snapshot):
         print "{} not found, fallback to snapshot".format(mmiBranchSetups)
         useSnapshot = True

      if canConnectToBranchSetups:
         builds = []
         for item in os.listdir(mmiBranchSetups):
            if os.path.isdir(os.path.join(mmiBranchSetups, item, '_Standard installer')):
               builds.append(item)
         assert len(builds) > 0
         latestVersion = sorted(builds,key=alphanum_key)[-1]
         useSnapshot = os.path.exists(snapshot) and os.path.getmtime(snapshot) > self.getNSSetupMTime(mmiBranchSetups, latestVersion)

      if useSnapshot:
         MmiUninstaller(self.mmiPath).removeMmiPath()
         self.copyFromSnapshot(snapshot)
      else:
            if useNsisSetup:
               MmiUninstaller(self.mmiPath).removeMmiPath()
               success, error = RunMmiSetup.runNSInstaller(latestNSSetup,self.testPath)
            else:
               MmiUninstaller(self.mmiPath).uninstall()
               success, error = self.runInstallShield(latestSetup)
            assert success, error
            self.createSnapshot(snapshot)

      if self.debugInfo:
         self.extractDebugInfo(latestDebugInfo)

class MmiProxy(communicationlib.CommunicationBase):
   def __init__(self, port):
      communicationlib.CommunicationBase.__init__(self, port, name="MmiProxy")
      self.sender = mmiSender.Mmi(self)

   def parseResult(self, result):
      return result

   def encodeMessage(self, message):
      return socketutils.encode(message)

   def enterExecute(self, consoleProxy=None):
      self.sender.gotoMenu("Execute")
      if consoleProxy is not None:
         consoleProxy.waitTillAlarmInactive(console.VisionNotReady)

   def exitExecute(self, consoleProxy):
      self.sender.gotoMenu("Component")
      if consoleProxy is not None:
         consoleProxy.waitTillAlarmActive(console.VisionNotReady)

   def loadModel(self, fileName, consoleProxy):
      self.sender.gotoMenu("Component")
      if consoleProxy is not None:
         consoleProxy.waitTillAlarmActive(console.VisionNotReady)
      self.sender.loadModel(fileName)
      self.enterExecute(consoleProxy)

class MMI:
   def __init__(self, configPath=None):
      self.mmiPath = os.path.normpath("c:/icos")
      self.mvsPath = os.path.normpath("c:/MVS7000")
      self.poolTxtPath = os.path.join(self.mmiPath, "pool.txt")
      self.cmpParametersTxtPath = os.path.join(self.mmiPath, "Cmp", "Parameters.txt")
      self.componentLibraryIniPath = os.path.join(self.mmiPath, "cmp", "library", "library.ini")
      self.configPath = configPath
      self.CCRsToInstall = []
      self.autoplayMode=False
      self.mvsType="7000"
      self.sol4WinPreBoot = self.getSol4WinPreBootParameter()
      self.linkMmiBinaries = self.getLinkMmiBinariesParameter()

   def getSol4WinPreBootParameter(self):
      sol4WinParameter = "keepSol4WinRunning"
      return extratestarguments.all[sol4WinParameter] if sol4WinParameter in extratestarguments.all else False

   def getLinkMmiBinariesParameter(self):
      linkMmiBinariesParameter = "linkMmiBinaries"
      return extratestarguments.all[linkMmiBinariesParameter] if linkMmiBinariesParameter in extratestarguments.all else False

   def setMvsType(self, type):
      self.mvsPath = "c:/MVS{}".format(type)
      self.mvsType = type

   def getMvsType(self):
      return self.mvsType

   def shutdownVmBox(self):
      if not self.sol4WinPreBoot:
         processtree.killAllWithName("VirtualBox.exe")
      processtree.killAllWithName("sockserv.exe")

   def cleanup(self):
      self.shutdownVmBox()

   def checkMvsDisplDriverRunning(self):
      import ctypes
      import ctypes.wintypes
      GENERIC_READ = 0x80000000
      GENERIC_WRITE = 0x40000000
      FILE_SHARE_READ = 0x00000001
      FILE_SHARE_WRITE = 0x00000002
      OPEN_EXISTING = 3
      FILE_ATTRIBUTE_NORMAL = 0x00000080
      LPSECURITY_ATTRIBUTES = ctypes.wintypes.c_void_p
      NULL = 0
      rc = ctypes.wintypes.HANDLE(
         ctypes.windll.kernel32.CreateFileW(ctypes.wintypes.LPWSTR(r"\\.\MVSdispl0"),
                                            ctypes.wintypes.DWORD(GENERIC_READ | GENERIC_WRITE),
                                            ctypes.wintypes.DWORD(FILE_SHARE_READ | FILE_SHARE_WRITE),
                                            LPSECURITY_ATTRIBUTES(NULL),
                                            ctypes.wintypes.DWORD(OPEN_EXISTING),
                                            ctypes.wintypes.DWORD(FILE_ATTRIBUTE_NORMAL),
                                            ctypes.wintypes.HANDLE(NULL)))
      INVALID_HANDLE_VALUE = ctypes.wintypes.HANDLE(-1)
      assert rc.value != INVALID_HANDLE_VALUE.value, \
             "MVS display driver not running, make sure you reboot once after an MMI installation"

   def deleteMmiFiles(self, listOfFiles):
      ostools.deleteFilesIfExist(self.mmiPath, listOfFiles)

   def copyMmiFiles(self, fromDirectory, listOfFiles):
      ostools.copyFilesRelative(fromDirectory, self.mmiPath, listOfFiles)
      print "Copied", listOfFiles, "from", fromDirectory, "to", self.mmiPath

   def prepareMmiFolder(self, consolePath, testPath):
      # remove some files to prevent MMI to pop up error boxes or start up savelogs
      self.deleteMmiFiles(["started.txt", "mmi.his"])

      self.copyMmiFiles(self.configPath if self.configPath else os.path.join(testPath, "../common"),
                        {"icos/mmi.his": "mmi.his",
                         "icos/mmi.set": "mmi.set",
                         "icos/jobs/list/startup.job": "jobs/list/startup.job"})

      # make sure mmi connects with the correct console
      mmiHanIniFile = ConfigParser.RawConfigParser()
      mmiHanIniFile.add_section("Settings")
      mmiHanIniFile.set("Settings", "RootDirectory", os.path.dirname(consolePath))
      mmiHanIniFile.write(open("c:/windows/mmi_han.ini", "w"))

      icosTestPath = os.path.join(testPath, "icos")

      # change the default process part folders for MMI
      # This is a quick fix until MMI sends the defaults with the testpath
      consoleIni = "handler/system/console.ini"
      changes = [["Settings", "RecipeSettings", "component_dir", os.path.normpath(os.path.join(icosTestPath, "cmp"))],
                 ["Settings", "RecipeSettings", "mmi_setup_dir", os.path.normpath(icosTestPath)],
                 ["Settings", "RecipeSettings", "execute_layout_dir",
                  os.path.normpath(os.path.join(icosTestPath, "Jobs/Layout"))]]
      testutils.changeConfigurationSetting(consoleIni, consoleIni, changes, False, False)

      copyLocalBinaries, sourceRoot = useLocalMmiSources()
      if copyLocalBinaries:
         self.copyMmiBinaries(sourceRoot)
         self.copyMmiResources(sourceRoot)

         configuration,platform=self.getConfigurationPlatform(sourceRoot)
         os.remove(os.path.join(self.mmiPath,'icos.pwd'))
         shutil.copy(os.path.join(sourceRoot,'init_pwd',platform,configuration,'init_pwd.exe'),os.path.join(self.mmiPath,'init_pwd.exe'))
         subprocess.call([os.path.join(self.mmiPath,'init_pwd.exe'),"1"])

      self.convertMmiCnf(testPath)
      self.convertMmiSet(testPath)
      self.copyApplicationSetup(testPath)
      self.copyTalFiles(testPath)
      self.copyCalibrationFiles(testPath)
      self.setOutputDirectories(testPath)
      self.changePoolSettings(consolePath, testPath)
      self.linkLogFolder(testPath)
      self.linkDiagnosticsFolder(testPath)


   def convertMmiSet(self, testPath):
      try:
         ET=xml.etree.ElementTree.parse(os.path.join(testPath,'icos','mmi.set'))
      except:
         print "Converting 'mmi.set' to xml"
         subprocess.call([r"c:\icos\convert\Conv_SetToXml.exe",os.path.join(testPath,'icos','mmi.set'),os.path.join(testPath,'icos','mmi.set.oldversion')])
         shutil.move(os.path.join(testPath,'icos','mmi.set.oldversion'),os.path.join(testPath,'icos','mmi.set'))

   def convertMmiCnf(self, testPath):
      if os.path.exists(os.path.join(testPath,'icos','mmi.cnf')):
         print "Converting 'mmi.cnf' to 'mmi_cnf.xml'"
         if os.path.exists(os.path.join(testPath,'icos','mmi_cnf.xml')):
            os.remove(os.path.join(testPath,'icos','mmi_cnf.xml'))
         subprocess.call([r"c:\icos\convert\CONV_CNFTOXML.exe",os.path.join(testPath,'icos','mmi.cnf'),os.path.join(testPath,'icos','mmi_cnf.xml')])
         os.remove(os.path.join(testPath,'icos','mmi.cnf'))

   def getCnfPath(self):
      return os.path.join(self.mmiPath, "mmi_cnf.xml")

   def getHistorySettingsPath(self):
      return os.path.join(self.mmiPath, "mmi_his.xml")

   def readCnfContent(self):
      return xml.etree.ElementTree.parse(self.getCnfPath())

   def writeCnfContent(self, tree):
      tree.write(self.getCnfPath())

   def setVakOnAllApplications(self, threadCount):
      tree = self.readCnfContent()
      for vak in tree.findall("./HostInfo/Requests401/Request401/Requests/Request/NrOfLogMvs"):
         vak.text = str(threadCount)
      self.writeCnfContent(tree)

   def setCameraSize(self, physicalCameraId, width, height):
      tree = self.readCnfContent()
      info = tree.find("./PhysicalCameraInfos/PhysicalCameraInfo[@ID='{0}']".format(physicalCameraId + 1))
      if info:
         print "Mmi_cnf.xml: adjusting size of physical camera %i to %ix%i" % (physicalCameraId, width, height)
         info.find("CameraWidth").text = str(width)
         info.find("CameraHeight").text = str(height)
      self.writeCnfContent(tree)

   def getCameraSize(self, physicalCameraId):
      tree = self.readCnfContent()
      info = tree.find("./PhysicalCameraInfos/PhysicalCameraInfo[@ID='{0}']".format(physicalCameraId + 1))
      if info:
         return eval(info.find("CameraWidth").text), eval(info.find("CameraHeight").text)

      return None, None

   def setMmiCnfToIs17(self):
      tree = self.readCnfContent()
      info = tree.find("./HostInfo/Requests401/Request401/Requests/Request[@ID='1']")
      info.find("InspectionStationID").text = "IS_17"
      self.writeCnfContent(tree)

   def getCameraSizeForIS(self, inspectionStation):
      logicalCamera = self.getLogicalCameraForIS(inspectionStation)
      camera = self.getPhysicalCameraForLogicalCamera(logicalCamera)
      return self.getCameraSizeForPhysicalCamera(camera)

   def getCameraSizeForPhysicalCamera(self, physicalCamera):
      if physicalCamera is None:
         return None, None

      return self.getCameraSize(physicalCamera)

   def getPhysicalCameraForLogicalCamera(self, logicalCameraId):
      if logicalCameraId is None: # Simplifies chaining
         return None

      tree = self.readCnfContent()
      xpath = "./LogicalCameraInfos/LogicalCameraInfo[@ID='{0}']".format(logicalCameraId + 1)
      logicalCameraInfo = tree.find(xpath)
      if logicalCameraInfo is None:
         print "Warning: unable to find the logicalCameraInfo for logical camera", logicalCameraId
         return None

      cameraSystemId = logicalCameraInfo.find("CameraSystemId").text
      xpath = "./CameraSystemInfos/CameraSystemInfo[@ID='{0}']".format(cameraSystemId)
      cameraSystemInfo = tree.find(xpath)
      if cameraSystemInfo is None:
         print "Warning: unable to find the application info for camera system ID", int(cameraSystemId) - 1

      return int(cameraSystemInfo.find("PhysicalCamera").get("ID")) - 1

   def getPhysicalCameraForIS(self, inspectionStation):
      return self.getPhysicalCameraForLogicalCamera(self.getLogicalCameraForIS(inspectionStation))

   def getApplicAndModelForIS(self, inspectionStation):
      match = re.match(r'^(IS)?_?(\d+)$', str(inspectionStation))
      if not match:
         print "Warning: unable to find request for", inspectionStation
         return

      inspectionStation = "IS_" + match.group(2)
      tree = self.readCnfContent()
      xpath = "./HostInfo/Requests401/Request401/Requests/Request[InspectionStationID='{0}']".format(inspectionStation)
      request = tree.find(xpath)
      if request is None:
         print "Warning: unable to find the request for", inspectionStation
         return None

      return request.find("RequestId").text, request.find("Model").text

   def getLogicalCameraForIS(self, inspectionStation):
      applic, model = self.getApplicAndModelForIS(inspectionStation)
      applic = mmiModelUtils.h401RequestIdToApplicString(applic)
      xpath = "./ApplicationInfos/ApplicationInfo[Applic='{0}'][Model='{1}']".format(applic, model)
      tree = self.readCnfContent()
      applicationInfo = tree.find(xpath)

      if applicationInfo is None:
         print "Warning: unable to find the application info for", inspectionStation
         return None

      return int(applicationInfo.find("LogicalCameraId").text) - 1

   def getCalibrationFileForIS(self, inspectionStation):
      logicalCam = self.getLogicalCameraForIS(inspectionStation)
      return self.getCalibrationFileForLogicalCamera(logicalCam)

   def getCalibrationFileForLogicalCamera(self, logicalCamera):
      calFile = "XY_CAL{0:02d}.XML".format(logicalCamera)
      return os.path.join(self.mmiPath, "Cal", calFile)

   def getPixelResolutionForIS(self, inspectionStation):
      cam = self.getLogicalCameraForIS(inspectionStation)
      return self.getPixelResolutionForLogicalCamera(cam)

   def getPixelResolutionForLogicalCamera(self, logicalCamera):
      cal = self.getCalibrationFileForLogicalCamera(logicalCamera)
      if not os.path.exists(cal):
         return None

      xycalib = xml.etree.ElementTree.parse(cal).getroot()
      displayUnit = xycalib.find("./DisplayUnit").get('Value')
      unitfactor = mmiModelUtils.unitFactor(displayUnit)

      return float(xycalib.find("./CalibrationPerLens/Lens/Results/Calibration/Resolution").get("Value")) / unitfactor

   def getCameraSize(self, physicalCameraId):
      tree = self.readCnfContent()
      for info in tree.findall("./PhysicalCameraInfos/PhysicalCameraInfo"):
         if eval(info.get("ID")) == physicalCameraId+1:
            return eval(info.find("CameraWidth").text), eval(info.find("CameraHeight").text)

      return None, None

   def getCameraPositioningDetails(self, physicalCameraId):
      tree = self.readCnfContent()
      cameraInfo = tree.find("./PhysicalCameraInfos/PhysicalCameraInfo[@ID='{0}']".format(physicalCameraId + 1))
      fFlip = cameraInfo.find("./FMirroring")
      fAngle = cameraInfo.find("./Rotation")
      bug = cameraInfo.find("./CompTransports/CompTransport")
      pos = cameraInfo.find("./CameraPosition")

      fFlip = fFlip.text == "true"
      fAngle = eval(fAngle.text[3:])
      bug = CameraImage.LIVEBUG if bug.text == "live_bug" else CameraImage.DEADBUG
      pos = CameraImage.ABOVE_COMPONENT if pos.text == "above_comp" else CameraImage.BELOW_COMPONENT

      return fFlip, fAngle, bug, pos

   def createImageForIS(self, inspectionStation, componentImage, testPath, sequenceNr, lighting):
      applic, model = self.getApplicAndModelForIS(inspectionStation)
      applic = int(applic) - 1
      if applic != 2:
         print "Warning: createImageForIS currently only works for package inspections."
         return

      print "Creating image for", inspectionStation
      logicalCamera = self.getLogicalCameraForIS(inspectionStation)
      cam = self.getPhysicalCameraForLogicalCamera(logicalCamera)
      fov = self.getCameraSizeForPhysicalCamera(cam)
      res = self.getPixelResolutionForLogicalCamera(logicalCamera)
      fFlip, fAngle, bug, pos = self.getCameraPositioningDetails(cam)
      print "Parameters: FOV: {} ({} mm/pix), FMap: Mirror? {} Rotate: {}, Livebug? {}, AboveCmp? {}, FrontLight? {}".format(fov, res, fFlip, fAngle, bug, pos, lighting)

      if fov is (None, None):
         print "Warning: FOV for", inspectionStation, "not found. Skipping image generation."
         return

      if res is None:
         print "Warning: resolution for", inspectionStation, "not found. Skipping image generation."
         return

      if None in [fFlip, fAngle, bug, pos]:
         print "Warning: camera details for", inspectionStation, "incomplete. Skipping image generation."

      img = CameraImage.createCameraImage(componentImage, fov, res, fAngle, fFlip, bug, pos, lighting, str(inspectionStation))

      filename = "i{0}{1}_{2:04d}_1.mvs".format(applic, model, sequenceNr)
      outputPath = os.path.join(testPath, "Diagnostics", "IMAGES", filename)
      print "Writing", outputPath
      MvsFileConverter.MvsFileConverter().write(img.getdata(), fov[0], fov[1], outputPath)
      img.save(os.path.splitext(outputPath)[0] + ".bmp")

   def setHostVersion(self, version):
      tree = self.readCnfContent()
      hostId = tree.find("./HostInfo/HostID")
      hostId.text = str(version)
      print hostId.text
      self.writeCnfContent(tree)

   def startSol4Win(self):
      if not self.sol4WinPreBoot:
         return
      slotXPath = "C:\\SOL4WIN2\\slotx.bat"
      def readSlotXBat():
         return open(slotXPath, 'rb').readlines()
      def writeSlotXBat(lines):
         with open(slotXPath, 'wb') as f:
            for line in lines:
               f.write(line)
      def disableBoot():
         lines = readSlotXBat()
         for i, line in enumerate(lines):
            poweroffMatch = re.match(r"^(.*VBoxManage controlvm .+ )poweroff(.*)$", line)
            if poweroffMatch:
               lines[i] = poweroffMatch.group(1) + "reset" + poweroffMatch.group(2)
            if "VBoxManage startvm" in line and not line.startswith("rem"):
               lines[i] = "rem " + line
         writeSlotXBat(lines)

      runningVms = virtualbox.VirtualBox().getRunningVMs()
      devices = self.readCnfContent().findall("./MVSInfos/MVSInfo/Device")
      for device in devices:
         deviceMatch = re.match("PCI(\\d+)_CH1", device.text)
         assert deviceMatch
         slotName = "slot" + deviceMatch.group(1)
         running = ("SOL7000_" + slotName) in runningVms
         backup = readSlotXBat()
         try:
            if running:
               disableBoot()
            else:
               writeSlotXBat(backup)
            base = os.path.join(self.mvsPath, slotName)
            print ("Reconnecting" if running else "Booting") + " Sol4Win '" + slotName + "'"
            subprocess.Popen(os.path.join(base, slotName + ".bat"), cwd=base, stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
         finally:
            writeSlotXBat(backup)

   def getBranch(self,checkPath=True):
      branchParameter = "version"
      if branchParameter in extratestarguments.all and not (extratestarguments.all[branchParameter] is None):
         branchToUse = extratestarguments.all[branchParameter]
      else:
         branchToUse = "10.4a"
         if checkPath and not os.path.exists(os.path.join(self.getMmiSetups(),branchToUse)):
            branchToUse='10.3a'
         print "'{}' not set, using {}".format(branchParameter, branchToUse)
      return branchToUse

   def getMmiSetups(self):
      mmiSetupsPath = "mmiSetupsPath"
      if mmiSetupsPath in extratestarguments.all and not (extratestarguments.all[mmiSetupsPath] is None):
         setupsPath = extratestarguments.all[mmiSetupsPath]
      else:
         setupsPath = r"//klasj/ktfiles/Regions/Belgium/ICOS/RD/RD_Share/Installers/Pre-release"
         print "'{}' not set, using {}".format(mmiSetupsPath, setupsPath)
      print "'{}' set as {}".format(mmiSetupsPath, setupsPath)
      return setupsPath

   def installMmi(self, testPath):
      print "STARTING NS INSTALLER.............................."
      mmiInstallationParameter = "mmiInstallation"
      try:
         doMmiInstallation = extratestarguments.all[mmiInstallationParameter]
      except KeyError:
         doMmiInstallation = True

      debugInfoParameter = "getDebugInfo"
      try:
         debugInfo = extratestarguments.all[debugInfoParameter]
      except KeyError:
         debugInfo = False
         print "'{}' not set, not getting debug info".format(debugInfoParameter)

      if doMmiInstallation:
         branchToUse = self.getBranch()
         installer = MmiInstaller(self.mmiPath,
                                  self.configPath,
                                  testPath,
                                  self.getMmiSetups(),
                                  branchToUse,
                                  debugInfo)
         print "mmiPath = {},configPath = {}, testPath = {}, branchToUse = {}".format(self.mmiPath, self.configPath, testPath, branchToUse)
         installer.install()

   def linkLogFolder(self, testPath):
      standardLogPath = os.path.join(self.mmiPath, "log")
      testLogPath = os.path.join(testPath, "icos/log")
      if not os.path.isdir(testLogPath):
         os.mkdir(testLogPath)
      print "configPath %s" % self.configPath
      ostools.copyFilesRelative(self.configPath, testLogPath, {"icos/log/settings.txt": "settings.txt"})
      if sys.getwindowsversion().major >= 6:
         ostools.symbolicLink(testLogPath, standardLogPath, overwrite=True)

   def setCCRsToInstall(self, CCRsToInstall):
      self.CCRsToInstall = CCRsToInstall

   def copyFilesByType(self, source, target, fileTypes):
      assert type(fileTypes) == list
      regex = r"^.*\.(" + "|".join(fileTypes) + ")$"
      if self.linkMmiBinaries:
         ostools.linkFilesByRegex(source, target, regex, overwrite=True)
      else:
         ostools.copyFilesByRegex(source, target, regex, overwrite=True)

   def copyMmiBinaries(self, sourceRoot):
    if "mmiPlatform" in extratestarguments.all.keys():
      platform = extratestarguments.all["mmiPlatform"].lower()

    else:
      platform = "win32"

    class FileType:
         EXE = "exe"
         DLL = "dll"
         BAT = "bat"
         PDB = "pdb"
         XSL = "xsl"

    if platform == "win32":  #copying win32 binaries
      print("Copying win32 binaries ") ## taking the platform form the commandline arguments(win32/x64)
      def copyReelStatReporter(ccrFolder, binAndConfig):
         # StatsChippac CCR
         statsChippacFolder = os.path.join(ccrFolder, "STATSChipPAC", "reel_stat_reporter")
         statsChippacBuildFolder = os.path.join(statsChippacFolder, "ReelStatReporter", binAndConfig)
         statsChippacXslFolder = os.path.join(statsChippacFolder, "ReelStatReporter", "XSL")
         mmiXslFolder = os.path.join(self.mmiPath, "XSL")
         print "Copying ReelStatReporter"
         if os.path.exists(statsChippacBuildFolder):
            print "statsChippacBuildFolder is available"
            self.copyFilesByType(statsChippacBuildFolder, self.mmiPath, [FileType.EXE, FileType.DLL, FileType.PDB])
            self.copyFilesByType(statsChippacXslFolder, mmiXslFolder, [FileType.XSL])
         else:
            print "STATSChipPAC classic custom reporter not found, not copying files. Looking for: ", statsChippacBuildFolder

      def copyIntelTrayReporter(ccrFolder, binAndConfig):
         print "Copying IntelTrayReporter"
         ITTBuildFolder = os.path.join(ccrFolder, "intel", "tray_reporter", binAndConfig)
         if os.path.exists(ITTBuildFolder):
            print "ITTBuildFolder is available"
            print ITTBuildFolder
            self.copyFilesByType(ITTBuildFolder, self.mmiPath, [FileType.EXE, FileType.DLL, FileType.PDB])
         else:
            print "ITTBuildFolder is NOT available: ", ITTBuildFolder
         # check if all files are really copied
         paths = ["IntelTrayReporter.exe",
                  "ICOS.MMI.Reporting.CustomReporting.MmiTransforms.dll",
                  "ICOS.MMI.Reporting.CustomReporting.dll",
                  "CustomReportLogViewer.exe"]
         for path in paths:
            assert os.path.exists(os.path.join(self.mmiPath, path)), "IntelTrayReporter: {} was not copied properly".format(os.path.join(self.mmiPath, path))

      def copyDatamatrixDlls(sourceRoot):
         source = os.path.join(sourceRoot, "..", "..", "libs", "external", "Euresys", "OpeneVision", "Bin32")
         destination = r'C:\Windows\SysWOW64'
         if not os.path.exists(destination):
            destination = r'C:\Windows\system32'
         print "Copy datamatrix dll's from '" + source + "' to '" + destination + "'"
         self.copyFilesByType(source, destination , [FileType.DLL])

      print "{} MMI binaries from '".format("Linking" if self.linkMmiBinaries else "Copying") + sourceRoot + "' to '" + self.mmiPath + "'..."
      configuration, platform = self.getConfigurationPlatform(sourceRoot)
      binaries = "bin"
      defaultLocation = os.path.join(binaries, platform)
      # MMI
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration),
                      self.mmiPath,
                      [FileType.EXE, FileType.DLL, FileType.PDB])

      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation,  configuration, "convert"),
                       os.path.join(self.mmiPath, "convert"),
                      [FileType.EXE, FileType.DLL])

      self.copyFilesByType(os.path.join(sourceRoot, "installShield_setup"), self.mmiPath, [FileType.EXE]) # Job list
      self.copyFilesByType(os.path.join(sourceRoot, "license"), self.mmiPath, [FileType.DLL])
      self.copyFilesByType(os.path.join(sourceRoot, "ocrtools"), self.mmiPath, [FileType.DLL])

      # CDA reporters
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration, "reporters"),
                      self.mmiPath,
                      [FileType.DLL, FileType.BAT, FileType.PDB])

      # CCRs
      availableCCRs = { "ReelStatReporter" : copyReelStatReporter,
                        "IntelTrayReporter" : copyIntelTrayReporter}
      ccrFolder = os.path.join(os.path.dirname(sourceRoot), "classic_custom_reporters")
      binAndConfig = os.path.join(binaries, configuration)
      for CCR in self.CCRsToInstall:
         assert CCR in availableCCRs
         availableCCRs[CCR](ccrFolder, binAndConfig)

      copyDatamatrixDlls(sourceRoot=sourceRoot)
    if platform == "x64": #copying x64 binaries
      print("Copying x64 binaries ") ## taking the platform form the commandline arguments(win32/x64)
      def copyReelStatReporter(ccrFolder, binAndConfig):
         # StatsChippac CCR
         statsChippacFolder = os.path.join(ccrFolder, "STATSChipPAC", "reel_stat_reporter")
         statsChippacBuildFolder = os.path.join(statsChippacFolder, "ReelStatReporter", binAndConfig)
         statsChippacXslFolder = os.path.join(statsChippacFolder, "ReelStatReporter", "XSL")
         mmiXslFolder = os.path.join(self.mmiPath, "XSL")
         print "Copying ReelStatReporter"
         if os.path.exists(statsChippacBuildFolder):
            print "statsChippacBuildFolder is available"
            self.copyFilesByType(statsChippacBuildFolder, self.mmiPath, [FileType.EXE, FileType.DLL, FileType.PDB])
            self.copyFilesByType(statsChippacXslFolder, mmiXslFolder, [FileType.XSL])
         else:
            print "STATSChipPAC classic custom reporter not found, not copying files. Looking for: ", statsChippacBuildFolder

      def copyIntelTrayReporter(ccrFolder, binAndConfig):
         print "Copying IntelTrayReporter"
         ITTBuildFolder = os.path.join(ccrFolder, "intel", "tray_reporter", binAndConfig)
         if os.path.exists(ITTBuildFolder):
            print "ITTBuildFolder is available"
            print ITTBuildFolder
            self.copyFilesByType(ITTBuildFolder, self.mmiPath, [FileType.EXE, FileType.DLL, FileType.PDB])
         else:
            print "ITTBuildFolder is NOT available: ", ITTBuildFolder
         # check if all files are really copied
         paths = ["IntelTrayReporter.exe",
                  "ICOS.MMI.Reporting.CustomReporting.MmiTransforms.dll",
                  "ICOS.MMI.Reporting.CustomReporting.dll",
                  "CustomReportLogViewer.exe"]
         for path in paths:
            assert os.path.exists(os.path.join(self.mmiPath, path)), "IntelTrayReporter: {} was not copied properly".format(os.path.join(self.mmiPath, path))

      def copyDatamatrixDlls(sourceRoot):
         source = os.path.join(sourceRoot, "..", "..", "libs", "external", "Euresys", "OpeneVision", "Bin32")
         destination = r'C:\Windows\SysWOW64'
         if not os.path.exists(destination):
            destination = r'C:\Windows\system32'
         print "Copy datamatrix dll's from '" + source + "' to '" + destination + "'"
         self.copyFilesByType(source, destination , [FileType.DLL])

      print "Copying MMI binaries from '" + sourceRoot + "' to '" + self.mmiPath + "'..."
      configuration, platform = self.getConfigurationPlatform(sourceRoot)
      binaries = "bin"
      defaultLocation = os.path.join(binaries, platform)
      # MMI
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration),
                      self.mmiPath,
                      [FileType.EXE, FileType.DLL, FileType.PDB])
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration), self.mmiPath, [FileType.PDB])
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation,  configuration, "convert"),
                       os.path.join(self.mmiPath, "convert"),
                      [FileType.EXE])
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration),
                      os.path.join(self.mmiPath, "convert"),
                      [FileType.EXE, FileType.DLL])

      self.copyFilesByType(os.path.join(sourceRoot, "installShield_setup"), self.mmiPath, [FileType.EXE]) # Job list
      self.copyFilesByType(os.path.join(sourceRoot, "license"), self.mmiPath, [FileType.DLL])
      self.copyFilesByType(os.path.join(sourceRoot, "ocrtools"), self.mmiPath, [FileType.DLL])

      # CDA reporters
      self.copyFilesByType(os.path.join(sourceRoot, defaultLocation, configuration, "reporters"),
                      self.mmiPath,
                      [FileType.DLL, FileType.BAT, FileType.PDB])

      # CCRs
      availableCCRs = { "ReelStatReporter" : copyReelStatReporter,
                        "IntelTrayReporter" : copyIntelTrayReporter}
      ccrFolder = os.path.join(os.path.dirname(sourceRoot), "classic_custom_reporters")
      binAndConfig = os.path.join(binaries, configuration)
      for CCR in self.CCRsToInstall:
         assert CCR in availableCCRs
         availableCCRs[CCR](ccrFolder, binAndConfig)

      copyDatamatrixDlls(sourceRoot=sourceRoot)

   def getConfigurationPlatform(self, sourceRoot):
      class Configuration:
         RELEASE = "release"
         DEBUG = "debug"

         ALL = [RELEASE, DEBUG]
         PLATFORM =["win32", "x64"]

      buildConfigurationParameter = "mmiBuildConfiguration"
      assert buildConfigurationParameter in extratestarguments.all, \
         "Missing test parameter: '" + buildConfigurationParameter + " (" + "/".join(Configuration.ALL) + ")'"

      configuration = extratestarguments.all[buildConfigurationParameter].lower()
      if "mmiPlatform" in extratestarguments.all.keys():
         platform = extratestarguments.all["mmiPlatform"].lower()
      else:
         platform="win32"

      assert platform in Configuration.PLATFORM, "Valid Platform: " + ", ".join(Configuration.PLATFORM)
      assert configuration in Configuration.ALL, "Valid build configurations: " + ", ".join(Configuration.ALL)

      return configuration, platform

   def copyMmiResources(self, sourceRoot):
      print "copy error.txt from " + sourceRoot
      ostools.deleteFilesIfExist(self.mmiPath, ["error.txt"])
      self.copyMmiFiles(sourceRoot, {"mmi/error.txt": "error.txt"})

   def copyIcosFiles(self, testPath, fileNames):
      for file in fileNames:
         if os.path.exists(testPath + "/icos/" + file):
            ostools.deleteFilesIfExist(self.mmiPath, [file])
            self.copyMmiFiles(testPath, {"icos/"+file: file})

   def copyApplicationSetup(self, testPath):
      if os.path.exists(testPath + "/icos/PassiveComponentsDefinition.xml"):
         self.copyMmiFiles(testPath, {"icos/PassiveComponentsDefinition.xml": "PassiveComponentsDefinition.xml"})

      if os.path.exists(testPath + "/icos/mmi_his.xml"):
         ostools.deleteFilesIfExist(self.mmiPath, ["mmi.his"])
         self.copyMmiFiles(testPath, {"icos/mmi_his.xml": "mmi_his.xml"})

      icosFileNames = ["IlluminationTypes.xml", "Style.txt", "PcCameraDescriptions.xml", "TeachLay.xml"]
      self.copyIcosFiles(testPath, icosFileNames)

      self.copyMmiFiles(testPath, {"icos/mmi_cnf.xml": "mmi_cnf.xml"})
      mvsSlots = os.path.join(testPath, "MVS{}".format(self.getMvsType()))

      boards = self.readCnfContent().findall("./MVSInfos/MVSInfo/Device")
      for board in boards:  # assume the text is PCInn_CH1 where nn is the slot number
         slotNumber = board.text[3:-4]
         slot = "slot" + slotNumber
         paramFile = os.path.join(self.mvsPath, slot, "param_file.txt")
         if slot.startswith('slot') and os.path.isfile(paramFile):
            print "Removing " + str(paramFile)

         shutil.copy2(os.path.join(mvsSlots, slot, "param_file.txt"), os.path.join(self.mvsPath, slot, "param_file.txt"))
         #shutil.copy2(os.path.join(mvsSlots, slot, slot + ".bat"), os.path.join(self.mvsPath, slot, slot + ".bat"))
         hostCamTCFile = os.path.join(mvsSlots, slot, "hostcam.bat")
         if os.path.exists(hostCamTCFile):
            self.hostCamStartFile = os.path.join(self.mvsPath, slot, "cdaStartHostCam.bat")
            shutil.copy2(hostCamTCFile, self.hostCamStartFile)

   def copyCalibrationFiles(self, testPath):
      ostools.copyFilesByRegex(os.path.join(testPath, "icos/cal"),
                               os.path.join(self.mmiPath, "cal"),
                               r"^.*\.*$",
                               overwrite=True)

   def copyTalFiles(self, testPath):
      fromPath = os.path.join(testPath, "icos/tal")
      toPath = os.path.join(self.mmiPath, "tal")
      ostools.copyFilesRelative(fromPath, toPath, {"tal link.txt": "tal link.txt"})
      ostools.copyFilesByRegex(fromPath,
                               toPath,
                               r"^.+\.(tal).*",
                               overwrite=True)

   def changePoolSettings(self, consolePath, testPath):
      self.changePoolSetting([["General", "CompleteRescan", "1"],
                              ["General", "EnableJobs", "1"],
                              ["General", "TimeoutOnSendMsg", "300"],
                              ["General", "CamerasConnected", "0"],
                              ["MVS6000Boot", "BootOnStartup", "0" if self.sol4WinPreBoot else "1"],
                              ["MVS6000Boot", "TimeoutOnPollingForSyncFile", "300"],
                              ["General", "HandlerDirectory",
                               os.path.normpath(os.path.join(testPath, "_Results/batch"))],
                              ["General", "XmlFileDirectory",
                               os.path.normpath(os.path.join(testPath, "_Results/xml"))],
                              ["CustomActions", "ExecutableAfterCrash",
                               os.path.normpath(os.path.join(consolePath, "SaveLogs.exe"))],
                              ["BGA", "ReflowZCompensation", 1]],
                              assertWhenSettingNotFound=True)
      self.changePoolSetting([["debug", "Sol4Win2", 1],
                              ["debug", "SkipMvsVersionCheck", 1],
                              ["debug", "ShowLoggingWarning", 0],
                              ["debug", "SuppressImageLoadingDialog", 1],
                              ["debug", "TestPath", os.path.normpath(testPath)],
                              ["debug", "EnableScriptingInterface", 1],
                              ["debug", "UseRelativePathForTakiSettingsFile", 1],
                              ["CDA", "Enabled", 1],
                              ["CDA", "IntegrationTest", 1],
                              ["CDA", "EnforceDatabaseIntegrity", 2],
                              ["General", "MinDiskFreeGbIcosFolder", 0],
                              ["General", "MinDiskFreeGbBatchFolder", 0],
                              ],
                             assertWhenSettingNotFound=False)
      if tags.Datamatrix.DATAMATRIX_EVISION in settings.tags or tags.Barcode.BARCODE_EVISION in settings.tags or tags.Textcode.TEXTCODE_EVISION in settings.tags:
         self.changePoolSetting([["debug", "DataMatrixType", "3"]], assertWhenSettingNotFound=False)
      elif  tags.Datamatrix.DATAMATRIX_OPEN_EVISION in settings.tags:
            self.changePoolSetting([["debug", "DataMatrixType", "4"]], assertWhenSettingNotFound=False)
      else:
         self.changePoolSetting([["debug", "DataMatrixType", "1"]], assertWhenSettingNotFound=False)

      self.activateAllBgaItemsInPool()

   def setCustomReporter(self, testPath, trigger, executableFileName, reportFileName=None):
      self.changePoolSetting([["General", "CustomReport", 1]], assertWhenSettingNotFound=True)
      self.changePoolSetting([["debug", "SkipMhtSaving", 1]], assertWhenSettingNotFound=False)

      mmiSetPath = os.path.join(testPath, "icos", "mmi.set")
      tree = xml.etree.ElementTree.parse(mmiSetPath)
      customReportingTag = tree.find("GlobalSettings").find("CustomReporting")
      if (trigger != "ReportOnEob" and trigger != "ReportOnOffload"):
         assert False, "The only triggers are 'ReportOnEob' or 'ReportOnOffload'"
      reportTag = customReportingTag.find(trigger)
      print reportTag.attrib
      reportTag.attrib["Enabled"] = "1"
      print reportTag.attrib
      reportTag.find("Executable").text = os.path.join(self.mmiPath, executableFileName)
      if (reportFileName):
         reportTag.find("Report").text = reportFileName
      tree.write(mmiSetPath)

   def setOutputDirectories(self, testPath, reportDirectory="_results/ascii", batchDirectory="_results/batch", icosRootPath=None):
      mmiSetPath = os.path.join(testPath, "icos", "mmi.set") if icosRootPath is None else  os.path.join(icosRootPath, "mmi.set")
      print mmiSetPath
      tree = xml.etree.ElementTree.parse(mmiSetPath)
      generalSettings = tree.find("GlobalSettings").find("General")
      generalSettings.find("ASCIIDir").text = os.path.normpath(os.path.join(testPath, reportDirectory))
      generalSettings.find("ReportDir").text = os.path.normpath(os.path.join(testPath, batchDirectory))
      tree.write(mmiSetPath)

   def disablePluginReporter(self, testPath, id, name):
      mmiSetPath = os.path.join(testPath, "icos", "mmi.set")
      tree = xml.etree.ElementTree.parse(mmiSetPath)
      try:
         xml.etree.ElementTree.SubElement(tree.find("./GlobalSettings/PluginReporting"), "Report", {"Id" : id, "Name" : name, "Enabled" : "0"})
         tree.write(mmiSetPath)
      except:
         pass

   def changeMmiSettingsElement(self, testPath,change,assertWhenSettingNotFound):
      """
         Usage:
            change="/GlobalSettings/General/Unit","Micron"
            changeMmiSettingsElement(change,False)
      """
      mmiSetPath = os.path.join(testPath, "icos", "mmi.set")
      tree = xml.etree.ElementTree.parse(mmiSetPath)
      section,newValue=change
      try:
        element=tree.find(section)
      except:
        assert not assertWhenSettingNotFound,section
      element.text=newValue
      tree.write(mmiSetPath)

   def removeMmiSettingsElement(self, testPath,section,assertWhenSettingNotFound):
      """
         Usage:
            change="/GlobalSettings/General/Unit"
            removeMmiSettingsElement(change,False)
      """

      mmiSetPath = os.path.join(testPath, "icos", "mmi.set")

      tree = xml.etree.ElementTree.parse(mmiSetPath)

      try:
        element=tree.find(section)
        tree.remove(element)
      except:
        assert not assertWhenSettingNotFound,section
      tree.write(mmiSetPath)

   def changeMmiSettingsAttrib(self, testPath,change,assertWhenSettingNotFound):
      """
         Usage:
            change="/GlobalSettings/Reporting/Report","Enabled","1"
            changeMmiSettingsAttrib(change,False)
      """

      mmiSetPath = os.path.join(testPath, "icos", "mmi.set")
      tree = xml.etree.ElementTree.parse(mmiSetPath)
      section,attrib,newValue=change
      try:
        element=tree.find(section)
      except:
        assert not assertWhenSettingNotFound,section
      if assertWhenSettingNotFound and not attrib in element.attrib:
          assert False,attrib
      element.attrib[attrib]=newValue
      tree.write(mmiSetPath)

   def linkDiagnosticsFolder(self, testPath):
      relativeLocation = "diagnostics/diagnostics.xml"
      self.copyMmiFiles(self.configPath, {"icos/diagnostics/diagnostics.xml": relativeLocation})
      sourcePath = os.path.join(testPath, "Diagnostics")
      diagnosticsXmlPath = os.path.join(self.mmiPath, relativeLocation)
      tree = xml.etree.ElementTree.parse(diagnosticsXmlPath)
      guiFolder = tree.find("GuiFolder")
      guiFolder.text = os.path.normpath(sourcePath)
      tree.write(diagnosticsXmlPath)

   def disableImageLoading(self):
      relativeLocation = "diagnostics/diagnostics.xml"
      diagnosticsXmlPath = os.path.join(self.mmiPath, relativeLocation)
      tree = xml.etree.ElementTree.parse(diagnosticsXmlPath)
      loadSaveOnOff = tree.find("LoadSaveOnOff")
      loadSaveOnOff.text = "0"
      tree = xml.etree.ElementTree.parse(diagnosticsXmlPath)
      loadImage = tree.find("LoadImage")
      loadImage.text = "0"
      tree.write(diagnosticsXmlPath)

   def changeConfigSettings(self, changes, toFile=None, assertWhenSettingNotFound=True, ignoreChangeWhenSettingNotFound=True):
      pass

   def getVisionSystemProcess(self, consolePath, testPath, hideProcess, portOffset, waitForDebugger):
      self.checkMvsDisplDriverRunning()

      mmiArgs = []
      if self.autoplayMode:
         mmiArgs.append("autoplay")

      if waitForDebugger:
         mmiArgs.append("-waitForDebugger")

      processtree.functions.append(self.shutdownVmBox)

      mmiProcess = process.Process(self.mmiPath,
                                   "mmi.exe",
                                   port=9900,
                                   proxyConstructor=MmiProxy,
                                   args=mmiArgs,
                                   portOffset=portOffset,
                                   hideProcess=hideProcess)

      def waitForMmiToFinish():
         while any((p.name.lower() == "mmi.exe" for p in processtree.getChildren(os.getpid()))):
            time.sleep(0.5)
      processtree.functions.append(waitForMmiToFinish)

      return mmiProcess

   def changeComponentModelSetting(self, testPath, changes, modelFileName="test.cmp", assertWhenSettingNotFound=True):
      def addPath(toTree, path):
         if len(path)==2:
            toTree[path[0]] = path[1]
         else:
            if not path[0] in toTree:
               toTree[path[0]] = dict()
            addPath(toTree[path[0]], path[1:])
      def toDict(changes):
         result = {}
         for path in changes:
            addPath(result, path)
         return result
      modelFilePath = os.path.join(testPath, "icos/Cmp", modelFileName)
      parsed = MmiComponentModelParser.parse(modelFilePath)
      print(changes)
      print(toDict(changes))
      parsed.update(toDict(changes), assertWhenSettingNotFound=assertWhenSettingNotFound)
      parsed.save(modelFilePath)

   def createRankedRejectFile(self, testPath, modelFileName="test.cmo", subApplicationNames=[]):
      modelFilePath = os.path.join(testPath, "icos", "Cmp", modelFileName)
      rankedRejectPath = os.path.join(testPath, "icos", "rankedreject.xml")
      parsed = MmiComponentModelParser.parse(modelFilePath)
      query = {}
      for subApplication in subApplicationNames:
         query[subApplication] = {"Name":""}
      parsed.executeQuery(query=query)
      YieldDefinitions = xml.etree.ElementTree.Element("YieldDefinitions")
      YieldTable = xml.etree.ElementTree.SubElement(YieldDefinitions, "YieldTable")
      xml.etree.ElementTree.SubElement(YieldTable, "Title").text = "Some Meaningful Title"
      RankedYieldDefinition = xml.etree.ElementTree.SubElement(YieldTable, "RankedYieldDefinition")
      for key in sorted(query):
         xml.etree.ElementTree.SubElement(RankedYieldDefinition, "Yield").text = query[key]["Name"]
      tree = xml.etree.ElementTree.ElementTree(YieldDefinitions)
      tree.write(rankedRejectPath)

   def changePoolSetting(self, changes, assertWhenSettingNotFound,ignoreChangeWhenSettingNotFound=False):
      testutils.changeWindowsIniFile(self.poolTxtPath,
                                     self.poolTxtPath,
                                     changes,
                                     assertWhenSettingNotFound=assertWhenSettingNotFound,
                                     ignoreChangeWhenSettingNotFound=ignoreChangeWhenSettingNotFound)

   def hasPoolSetting(self, section, option):
      pool = ConfigParser.ConfigParser()
      pool.optionxform = str
      pool.read(self.poolTxtPath)
      return pool.has_option(section, option)

   def changeCmpParametersSetting(self, changes, assertWhenSettingNotFound=True, ignoreChangeWhenSettingNotFound=False):
      testutils.changeWindowsIniFile(self.cmpParametersTxtPath,
                                     self.cmpParametersTxtPath,
                                     changes,
                                     assertWhenSettingNotFound=assertWhenSettingNotFound,
                                     ignoreChangeWhenSettingNotFound=ignoreChangeWhenSettingNotFound)

   def installMockLicense(self):
      print "Install MMI Mock License ..."
      buildConfigurationParameter = "mmiBuildConfiguration"
      assert buildConfigurationParameter in extratestarguments.all,\
             "Missing test parameter: '" + buildConfigurationParameter + " (" + "/".join(Configuration.ALL) + ")'"


      if buildConfigurationParameter in extratestarguments.all.keys():
         configuration = extratestarguments.all[buildConfigurationParameter].lower()
      else:
         configuration="release"

      if "mmiPlatform" in extratestarguments.all.keys():
         platform = extratestarguments.all["mmiPlatform"].lower()
      else:
         platform="win32"

      sourceRoot = extratestarguments.all["mmiSourceRoot"]
      if sourceRoot==None:
         print "Warning mocklicense will not be copied!!!"
      configuration = extratestarguments.all[buildConfigurationParameter].lower()
      mockDllPath = os.path.join(sourceRoot, r"mmi_stat\integration\code\MockLicenseDll", platform, configuration,
                                 "License.dll")
      print 'Mock License.dll path: ' + mockDllPath
      assert os.path.exists(mockDllPath)
      shutil.copy(mockDllPath, r'c:\icos')

   def getKnownLicenses(self):
      licenses = {
         "CI-T2x0u": "{996EB19B-4CAA-4E1C-AF47-B8AE825A141C}",
         "Detaping": "{6DA6994E-3D1B-41ED-8F5B-B22BE89396A3}",
         "Handler Library Tool": "{8C38AFC3-5E5C-4703-B0F6-B53D5DAF8DA0}",
         "CI library and audit tool": "{8C38AFC3-5E5C-4703-B0F6-B53D5DAF8DA0}",
         "MMI SPC Review tool": "{54C86CD4-1D00-47be-A720-D21FB9A64EA9}",
         "Lead3d with pads": "{5AE03427-8BE1-4170-96E6-FF843A778DA1}",
         "Illumination Calibration": "{71B821AF-55CA-457a-A8DD-524051C781CF}",
         "Extended PVI": "{98C2B801-ADD1-4875-A5C1-F279D1D2230F}",
         "Extended Surface Criteria": "{98C2B801-ADD1-4875-A5C1-F279D1D2230F}",
         "Extreme Overlapping Holes": "{CA18AC21-C99B-491d-9F2A-4AED4750E273}",
         "Available MVS Channels": "{2ba3c6b1-f3c5-4b15-af4c-667dcc477154}",
         "OCR Based Text Code Reading": "{23bf3abf-9c3a-4a35-8905-9418c2aaf310}",
         "Directional Grouping": "{9c8c10a1-0351-4b21-b43f-1a7b575a145d}",
         "Automatic Light Control": "{A6A985E0-9A46-401E-AC7D-72605DF048E1}",
         "Advanced QFN2D/5S Parameters": "{7FCCBB2E-7F87-4EDE-8FB8-08C343D6F0E6}",
         "Combined Surface Inspection": "{6F6498D2-45FF-4e4e-8F89-59CA86D9EAB0}",
         "Ball and Land Grid Autoteach": "{CA405D13-1F23-42CC-9604-9FCF6E92E8AC}",
         "Waffle Pack Handling": "{D77735BE-A1BF-455D-83F8-50EA54CA2231}",
         "Edge Tracking": "{67A53591-D081-4572-A912-2431259AB8D7}",
         "Surface Generic Shape Areas": "{798CE692-4CE0-4181-88FF-91FAD86FC05C}",
         "Brushing": "{47AF368C-0D81-41F3-8DC2-9FE8EFD89246}",
         "Advanced Generic Measurement": "{109C8C97-019A-41B3-81F7-6411F64CB790}",
         "Medium ID Inspection": "{2F57CA03-7D25-4B2F-A318-FF37EFA10177}",
         "Multi-pitch PoP": "{D2D86202-482A-4CF9-BBE2-F70A388AC016}",
         "Tray jobs with partial tray, empty pockets from X1": "{E64C3CFE-B8BD-450C-A4EA-285A35004357}",
         "Custom Pad Shapes": "{BA494962-4B7B-43CB-B987-EB8F7FB3C51A}",
         "Topology": "{28354A20-87E0-4FC6-BAE8-AD384758B2BA}",
         "Automatic calibration and light degradation check": "{C6097AD5-5F50-4818-B8C7-7ED346D6178D}",
         "TH4": "{CBD5BF4B-9482-46D0-A065-0C3C9D545A95}",
         "3D_PVI" : "{647D4158-497A-46AA-BADC-2012E800D334}",
         "Edge Tracking" : "{67A53591-D081-4572-A912-2431259AB8D7}",
         "Deep Learning" : "{A88D5A0D-C7E6-42CD-B397-48A18BF15BF3}",
         "UI Upgrade" : "{1D115E58-36A1-43E5-8601-BA145FAF2EE2}",
      }
      return licenses

   #create a license config file, but the file needs to be installed in the test folder (mockLicense.dll requiement).
   def enableLicense(self, testPath, licenseNames):
      contents="""<?xml version="1.0" encoding="utf-8"?><LicMgr xmlns="http://schemas.icos.be/global/LicMgrConfigFile-1.0"><Department name="Component Inspector MMI"><Modules>"""
      lics = self.getKnownLicenses()
      licenses={k.lower():v for k,v in lics.iteritems()}
      for licenseName in licenseNames:
         assert licenseName.lower() in licenses.keys(), "License '" + licenseName + "' not found. Please update list."
         contents+= '<Add name="'+licenseName+'" id="'+ licenses[licenseName.lower()] +'" />'

      contents += """</Modules></Department></LicMgr>"""
      with open(os.path.join(testPath, "LicMgrConfig.xml"), "w") as f:
         f.write(contents)

   def changeComponentLibraryIniSetting(self, changes, toFile=None, assertWhenSettingNotFound=False, ignoreChangeWhenSettingNotFound=False):
      if toFile == None:
         toFile = self.componentLibraryIniPath

      testutils.changeWindowsIniFile(self.componentLibraryIniPath,
                                     toFile,
                                     changes,
                                     assertWhenSettingNotFound=assertWhenSettingNotFound,
                                     ignoreChangeWhenSettingNotFound=ignoreChangeWhenSettingNotFound)

   def changeLogSetting(self, testPath, changes, assertWhenSettingNotFound,ignoreChangeWhenSettingNotFound=False):
      testLogPathSettings = os.path.join(testPath, "icos\log\settings.txt")
      # the settings file is not a real ini file (it contains a header that is not part of a section and some obscure formatting)
      # To workaround this we:
      with open(testLogPathSettings) as file:
         lines = file.read()
      # 1. remove first lines until first section header
      pos = lines.find("\n[")
      with open(testLogPathSettings, 'w') as file:
         file.write(lines[pos:])
      # 2. do the changes using the ini parser
      testutils.changeWindowsIniFile(testLogPathSettings,
                                     testLogPathSettings,
                                     changes,
                                     assertWhenSettingNotFound=assertWhenSettingNotFound,
                                     ignoreChangeWhenSettingNotFound=ignoreChangeWhenSettingNotFound)
      # 3. Do some reformatting
      newlines=list()
      with open(testLogPathSettings) as file:
         for line in file.read().splitlines():
            if len(line) > 1 and not line.startswith("["):
               newlines.append(line.rstrip("\r") + "\t; \n")
            else:
               newlines.append(line.rstrip("\r") + "\n")
      # 4. Write the result back to file and remove the last newline statement
      with open(testLogPathSettings, 'w') as file:
         file.write(lines[:pos] + "\n")
         file.writelines(newlines[0:-1])


   def changeMmiHistorySetting(self, testPath, change, assertWhenSettingNotFound=True):
      """
         Usage:
            change="/GlobalSettings/Reporting/Report/Enabled","1"
            changeMmiSettingsAttrib(change,False)
      """
      mmihispath = self.getHistorySettingsPath()
      print "Changing mmi history setting at {}".format(mmihispath)
      tree = xml.etree.ElementTree.parse(mmihispath)
      section,newValue=change
      with open(mmihispath, 'r') as fin:
         print fin.read()
      try:
        element=tree.find(section)
      except:
        assert not assertWhenSettingNotFound,section
      print "changing {} from {} to {}".format(section, element.text, newValue)
      element.text=newValue
      tree.write(mmihispath)

   def activateAllBgaItemsInPool(self):
      self.changePoolSetting([["BGA", "CC", 1],
                              ["BGA", "GR", 1],
                              ["BGA", "EH", 1],
                              ["BGA", "EB", 1],
                              ["BGA", "ES", 1],
                              ["BGA", "EP", 1],
                              ["BGA", "EO", 1],
                              ["BGA", "MB", 1],
                              ["BGA", "CH", 1],
                              ["BGA", "S1", 1],
                              ["BGA", "S2", 1],
                              ["BGA", "S3", 1],
                              ["BGA", "PQ", 1],
                              ["BGA", "ST", 1],
                              ["BGA", "AR", 1],
                              ["BGA", "BV", 1],
                              ["BGA", "LV", 1],
                              ["BGA", "HV", 1],
                              ["BGA", "LN", 1],
                              ["BGA", "TH", 1],
                              ["BGA", "SC", 1],
                              ["BGA", "AH", 1],
                              ["BGA", "BB", 1],
                              ["BGA", "AX", 1],
                              ["BGA", "AV", 1],
                              ["BGA", "AS", 1],
                              ["BGA", "AO", 1],
                              ["BGA", "TW", 1],
                              ["BGA", "RI", 1],
                              ["BGA", "HN", 1],
                              ["BGA", "DX", 1],
                              ["BGA", "DY", 1],
                              ["BGA", "W1", 1],
                              ["BGA", "W2", 1],
                              ["BGA", "W3", 1],
                              ["BGA", "W4", 1],
                              ["BGA", "W5", 1],
                              ["BGA", "W6", 1],
                              ["BGA", "W7", 1],
                              ["BGA", "W8", 1],
                              ["BGA", "RC", 1],
                              ["BGA", "FX", 1],
                              ["BGA", "FV", 1],
                              ["BGA", "FS", 1],
                              ["BGA", "FO", 1],
                              ["BGA", "KX", 1],
                              ["BGA", "KV", 1],
                              ["BGA", "KS", 1],
                              ["BGA", "KO", 1],
                              ["BGA", "SX", 1],
                              ["BGA", "SY", 1],
                              ["BGA", "SR", 1],
                              ["BGA", "HO", 1],
                              ["BGA", "TA", 1],
                              ["BGA", "CU", 1],
                              ["BGA", "CL", 1],
                              ["BGA", "UX", 1],
                              ["BGA", "UV", 1],
                              ["BGA", "US", 1],
                              ["BGA", "UO", 1],
                              ["BGA", "XW", 1],
                              ["BGA", "XX", 1],
                              ["BGA", "XY", 1],
                              ["BGA", "GC", 1],
                              ["BGA", "AC", 1],
                              ["BGA", "CA", 1],
                              ["BGA", "CA", 1],
                              ["BGA", "NQ", 1],
                              ["BGA", "PH", 1],
                              ["BGA", "PS", 1],
                              ["BGA", "PX", 1],
                              ["BGA", "PY", 1],
                              ["BGA", "PR", 1],
                              ["BGA", "PO", 1]],
                             assertWhenSettingNotFound=True)

   def setSurfaceOnlyTrayReporting(self):
       shutil.copy(os.path.join(self.configPath, "icos", "CustomReporterConfiguration.xml"), self.mmiPath)

   def certifyEverything(self):
      for f in os.listdir(os.path.join(self.mmiPath, "Cer", "Cer000")):
         shutil.copy(os.path.join(self.mmiPath, "Cer", "Cer000", f), os.path.join(self.mmiPath, "Cer"))

   def setRegistryMvs(self,testPath):
      #check if this is a sol4win2-pc or a rack with real mvs-boards
      with open(os.path.join(self.mvsPath, "slot1", "slot1.bat"), 'r') as content_file:
         content = content_file.read()
         if not content.lower().find('sol4win2'):
            return #real mvs-boards

      regfile=os.path.join(testPath,'icos','mvs{}.reg'.format(self.getMvsType()))
      if os.path.exists(regfile):
         print "found mvs{}".format(self.getMvsType())
         with open(regfile, 'r') as content_file:
            content = content_file.read()
         if not content.lower().find(r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\ICOS Vision Systems\MVS{}'.format(self.getMvsType()).lower()):
            print "converted mvs{}".format(self.getMvsType())
            escape_key1 = r'HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{}'.format(self.getMvsType())
            escape_key2 = r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\ICOS Vision Systems\MVS{}'.format(self.getMvsType())
            content=re.sub("(?i)"+re.escape(escape_key1),re.escape(escape_key2), content)
      else:
         print "default mvs{}".format(self.getMvsType())
         content=r"""Windows Registry Editor Version 5.00
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}]
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\General]
"NumberOfBoards"=dword:00000008
"PCType"="Autodetected MVS{0} slotmapping: VC100056 - rev1 - with PCIe device"
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 1]
"PCISlotNumber"=dword:00000000
"PCIBusNumber"=dword:00000003
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 2]
"PCISlotNumber"=dword:00000000
"PCIBusNumber"=dword:00000009
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 3]
"PCISlotNumber"=dword:00000000
"PCIBusNumber"=dword:00000007
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 4]
"PCISlotNumber"=dword:00000000
"PCIBusNumber"=dword:00000005
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 5]
"PCISlotNumber"=dword:00000001
"PCIBusNumber"=dword:00000003
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 6]
"PCIBusNumber"=dword:00000009
"PCISlotNumber"=dword:00000001
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 7]
"PCISlotNumber"=dword:00000001
"PCIBusNumber"=dword:00000007
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
[HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS{0}\Slot 8]
"PCISlotNumber"=dword:00000001
"PCIBusNumber"=dword:00000005
"BoardId"=dword:00001b58
"BoardRevision"=dword:00002003
"SerialNumber"=dword:00000000
"DspClock"=dword:000006b0
"NumberOfNodes"=dword:00000006
"XilinxId"=dword:00000001
"ExtSerialNumber"=hex:41,53,30,39,31,39,30,30,30,30,36,00,00,00,00,00
"ACAId"=dword:00000000
""".format(self.getMvsType())
      with open(regfile, 'w') as content_file:
         content_file.write(content)
      if "mmiPlatform" in extratestarguments.all.keys():
         platform = extratestarguments.all["mmiPlatform"].lower()
      else:
         platform="win32"
      index = platform.rfind("x64")
      regType = '/reg:64'
      if -1 == index:
         regType = '/reg:32'
      NULL=open(os.devnull,'wb')
      #delete existing registry contents
      subprocess.call([r"reg.exe",'DELETE',r'HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS7000','/f', regType],stdout=NULL,stderr=NULL)
      subprocess.call([r"reg.exe",'DELETE',r'HKEY_LOCAL_MACHINE\SOFTWARE\ICOS Vision Systems\MVS8000','/f', regType],stdout=NULL,stderr=NULL)
      #insert new registry contents
      subprocess.call([r"reg.exe", 'import', regfile, regType])
      



class TestHost:
   def __init__(self):
      self.testHostConfigFileName = "handler/system/MMI_TH.INI"

   def changeConfigSettings(self, changes, toFile=None, assertWhenSettingNotFound=True, ignoreChangeWhenSettingNotFound=True):
      if toFile is None:
         toFile = self.testHostConfigFileName
      testutils.changeWindowsIniFile(self.testHostConfigFileName, toFile, changes, assertWhenSettingNotFound=assertWhenSettingNotFound, ignoreChangeWhenSettingNotFound=ignoreChangeWhenSettingNotFound)
      
   def cleanup(self):
      pass

   def getVisionSystemProcess(self, consolePath, testPath, hideProcess, portOffset, waitForDebugger):
      testhostArgs = [testPath]
      if waitForDebugger:
         testhostArgs.append("-waitForDebugger")
      if portOffset != 0:
         testhostArgs.append("-portOffset=" + str(portOffset))
         
      return process.Process(consolePath,
                             "testhost.exe",
                             8049,
                             proxyConstructor=testhost.Testhost,
                             args=testhostArgs,
                             portOffset=portOffset,
                             hideProcess=hideProcess)
