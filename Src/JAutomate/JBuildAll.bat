IF "%1" NEQ "" (
	ECHO Calling %*
	CALL:%*
	EXIT /B 0
)

rem python -c "from JAutomate import JAutomate; JAutomate().StartLoop()"
rem pause

ECHO OFF
REM Build Options
REM ~~~~~~~~~~~~~
REM Configurations : Debug Release
REM Platform       : Win32 x64

CALL:JSetSource 4
CALL:Initialize %0
SET IsDebugEnabled=0
SET DoCopyMMI=1

 rem CALL:JEveningBuild
 rem CALL:CleanSource
rem CALL:JPrintMenu

REM CALL:BuildSource %JConfig% %JPlatform%

REM SET JCdaTestName=GageRnR
REM RUN CDA TEST WITH (IsDebugEnabled)
REM CALL:JRunCdaTest %JSource% %JCdaTestName% False

REM --------------------------------------------------------------------------------------------------------
REM ----------------------------              End of Execution              --------------------------------
REM --------------------------------------------------------------------------------------------------------
EXIT /B %ERRORLEVEL%

REM ------------------------------  Set Source  ------------------------------------------------------------
:JSetSource
	SET J_SRC_NUM=%1
	SET JSource=.
	SET JConfig=Debug
	SET JPlatform=Win32

	IF %J_SRC_NUM% == 1 SET JSource=D:\CI\Src1
	IF %J_SRC_NUM% == 2 SET JSource=D:\CI\Src2
	IF %J_SRC_NUM% == 3 SET JSource=D:\CI\Src3
	IF %J_SRC_NUM% == 4 SET JSource=D:\CI\Src4
EXIT /B 0

REM ------------------------------  Initialize  ------------------------------------------------------------
:Initialize
	REM The following change directory request is needed only to run from NotePad++
	For %%A in (%1) do (
		SET JCD=%%~dpA
		SET JDrive=%%~dA
	)

	%JDrive%
	CD %JCD%
	SET JCD=%CD%

	REM Set Python 2.7 as default
	SET py2=Python27
	SET py3=Users\1014769\AppData\Local\Programs\Python\Python36-32
	CALL SET path=%%path:%py3%=%py2%%%

	CALL:JSetTestName
EXIT /B 0

REM ------------------------------  Print Menu  ------------------------------------------------------------
:JPrintMenu
	ECHO OFF
	CALL:SetBranch
	CALL:JPython PrintMenu(%J_SRC_NUM%, '%JTestName%')

	SET JInput=%errorlevel%

	IF "%JInput%" == "1" START python -i %JSource%\libs\testing\my.py
	IF "%JInput%" == "2" CALL:J_AutoTest %JTestName% 0 %IsDebugEnabled% %DoCopyMMI%
	IF "%JInput%" == "3" CALL:J_AutoTest %JTestName% 1 %IsDebugEnabled% %DoCopyMMI%
	IF "%JInput%" == "4" CALL:J_Handler %JTestName%
	IF "%JInput%" == "5" CALL:J_MMi %JTestName%
	IF "%JInput%" == "6" CALL:J_Handler_MMi

	IF "%JInput%" == "10" CALL:JInstallMMI 10.4a 9
	IF "%JInput%" == "11" START %JSource%\handler\cpp\CIT100.sln
	IF "%JInput%" == "12" START %JSource%\handler\Simulator\CIT100Simulator\CIT100Simulator.sln
	IF "%JInput%" == "14" START %JSource%\mmi\mmi\Mmi.sln
	IF "%JInput%" == "15" START %JSource%\mmi\mmi\MockLicense.sln
	IF "%JInput%" == "16" START %JSource%\mmi\mmi\Converters.sln

	IF "%JInput%" == "20" CALL:JOpenTestFolder %JSource% %JTestName%
	IF "%JInput%" == "21" CALL:JPython OpenLocalDif(%J_SRC_NUM%)
	IF "%JInput%" == "22" CALL:JChangeTest
	IF "%JInput%" == "23" CALL:JPython PrintMissingIds(%J_SRC_NUM%)
	IF "%JInput%" == "24" COPY D:\QuEST\MyProjects\xPort\xPort_IllumReference.xml C:\icos\xPort
	IF "%JInput%" == "25" CALL:JPython ModifyVisionSystem(%J_SRC_NUM%)
	IF "%JInput%" == "26" CALL:JPython CopyMockLicense(%J_SRC_NUM%, '%JPlatform%', '%JConfig%')
	IF "%JInput%" == "27" CALL:JPython PrintBranches()

	IF "%JInput%" == "91" CALL:JEveningBuild
	IF "%JInput%" == "92" CALL:JEveningBuild True

	IF "%JInput%" == "99" CALL:JPython KillTask()

	IF "%JInput%" NEQ "0" GOTO :JPrintMenu
EXIT /B 0

REM ------------------------------  Install MMI  -----------------------------------------------------------
:JInstallMMI
	SET JMajorVer=%1
	SET JMinorVer=%2
	DEL /F/S/Q C:\Icos\*
	RMDIR /S/Q C:\Icos
	"D:\MmiSetups\%JMajorVer%\%JMajorVer%%JMinorVer%\_Standard installer\MMI_%JMajorVer%%JMinorVer%_setup.exe"
EXIT /B 0

REM REM ------------------------------  Run Given Slots  -------------------------------------------------------
REM :JRunSlots
REM 	SET JSlots=%1
REM 
REM 	SET JSlots=%JSlots:_= %
REM 	SET JPause=%2
REM 
REM 	FOR %%a IN (%JSlots%) DO (
REM 		SET IsRunning=False
REM 		SETLOCAL EnableDelayedExpansion
REM 		FOR /f %%b IN ('"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -vp 1 list') DO (
REM 			SET temp1=%%b
REM 			SET temp2=!temp1:~15,1!
REM 			IF "!temp2!" == "%%a" SET IsRunning=True
REM 		)
REM 
REM 		IF "!IsRunning!" == "False" (
REM 			ECHO Starting VMware %%a
REM 			START "C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe" "C:\MVS8000\slot%%a\MVS8000_stage2.vmx"
REM 			PAUSE
REM 			SET JPause=False
REM 		) ELSE (
REM 			ECHO Reseting VMware %%a
REM 			"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -vp 1 reset C:\MVS8000\slot%%a\MVS8000_stage2.vmx
REM 		)
REM 	)
REM 	IF "%JPause%" == "True" TIMEOUT 8
REM EXIT /B 0

REM ------------------------------  Evening Build  ---------------------------------------------------------
:JEveningBuild
	REM SET JSrcNums=1 2 3 4
	SET JSrcNums=3

	ECHO The following sources are included in build.
	CALL:JPython PrintBranches('%JSrcNums%')
	IF "%1" == "True" (
		CALL::Message ********************   STARTING EVENING BUILD    ********************

		FOR %%A IN (%JSrcNums%) DO (
			CALL:JSetSource %%A
			CALL:CleanSource
		)
	)

	FOR %%A IN (%JSrcNums%) DO (
		CALL:JSetSource %%A
		CALL:BuildSource %JConfig% %JPlatform%
	)

	rem CALL:JShutDown
	REM CALL:JRestart

	CALL::JPrint Evening Build Completed.
EXIT /B 0

REM ------------------------------  Start Handler Console  -------------------------------------------------
:J_Handler
	CALL:JPython StartHandler('%JSource%', '%1')

	REM SET HandlerPath=%JSource%/handler
	REM SET TestName=%1
	REM SET JSlots=%2
	REM
	REM REM Kill MMI
	REM CALL KillAll
	REM
	REM ECHO Starting Console
	REM start %HandlerPath%/cpp/bin/Win32/debug/system/console.exe %HandlerPath%/tests/%TestName%~
	REM
	REM ECHO Starting Simulator
	REM start %HandlerPath%/Simulator/ApplicationFiles/bin/x86/Debug/CIT100Simulator.exe %HandlerPath%/tests/%TestName%~ %HandlerPath%/cpp/bin/Win32/debug/system
	REM
	REM REM ECHO Starting HostCamServer
	REM REM start C:/MVS7000/software_29.6.0_MVS7000_Daily.20150212_1/hostsw/hostcam/HostCamServer.exe
EXIT /B 0

REM ------------------------------  Restart MMi  -----------------------------------------------------------
:J_MMi
	CALL:JPython StartMMi('%JSource%', '%2', '%JPlatform%', '%JConfig%')

	REM SET JSlots=%2
	REM
	REM SET JMMI_PATH=%JSource%\mmi\mmi\Bin\%JPlatform%\%JConfig%
	REM SET JMOCK_PATH=%JSource%\mmi\mmi\mmi_stat\integration\code\MockLicenseDll\%JPlatform%\%JConfig%
	REM
	REM REM Kill MMI
	REM CALL KillAll Mmi.exe
	REM
	REM REM Running VMware Workstations
	REM IF "%JSlots%" NEQ "" CALL:JPython RunSlots('%JSlots%', 'True')
	REM
	REM REM COPY MOCK LICENCE
	REM IF NOT EXIST %JMOCK_PATH%\License.dll PAUSE
	REM COPY %JMOCK_PATH%\License.dll %JMMI_PATH% /Y
	REM COPY D:\QuEST\MyProjects\xPort\xPort_IllumReference.xml C:\icos\xPort
	REM
	REM TIMEOUT 8
	REM
	REM start %JMMI_PATH%\Mmi.exe
EXIT /B 0

REM ------------------------------  Start Handler and MMi  -------------------------------------------------
:J_Handler_MMi
	CALL:J_Handler %JTestName%
	CALL:J_MMi %JTestName%
EXIT /B 0

REM ------------------------------  Open Test Folder  ------------------------------------------------------
:JOpenTestFolder
	start %1\handler\tests\%2
EXIT /B 0

REM ------------------------------  Change Test  -----------------------------------------------------------
:JChangeTest
	CALL:JPython SelectTest()
	CALL:JSetTestName
EXIT /B 0

REM ------------------------------  Call Python  -----------------------------------------------------------
:JPython
	python -c "from JAutomate import JAutomate; JAutomate().%*"
EXIT /B %errorlevel%

REM ------------------------------  Set Test Name  ---------------------------------------------------------
:JSetTestName
	rem for /f "delims=" %%a in (Tests.txt) do set JTestName=%%a
EXIT /B 0

REM ------------------------------  Build Source  ----------------------------------------------------------
:BuildSource
	SET JConfig=%1
	SET JPlatform=%2

	SET JOutPath=%JSource%\Out_

	SET JSimuPF=x86
	IF %JPlatform% == "x64" (SET JSimuPF=x64)

	SET JErrorLevel=0
	CALL:SetBranch
	SET JSimulPath=%JSource%/handler/Simulator/CIT100Simulator/CIT100Simulator
	CALL::JPrint Start building : %JSource% ["%JConfig%|%JPlatform%"] %JBranch%
	CALL:BuildSolution %JSource%/handler/cpp/CIT100 "%JConfig%|%JPlatform%" %JOutPath%Handler
	IF %ERRORLEVEL% NEQ 0 (SET JErrorLevel=%ERRORLEVEL%)
	CALL:BuildSolution %JSimulPath% "%JConfig%|%JSimuPF%" %JOutPath%Simulator
	IF %ERRORLEVEL% NEQ 0 (SET JErrorLevel=%ERRORLEVEL%)
	CALL:BuildSolution %JSource%/mmi/mmi/mmi "%JConfig%|%JPlatform%" %JOutPath%MMi
	IF %ERRORLEVEL% NEQ 0 (SET JErrorLevel=%ERRORLEVEL%)
	CALL:BuildSolution %JSource%/mmi/mmi/MockLicense "%JConfig%|%JPlatform%" %JOutPath%MockLicense
	IF %ERRORLEVEL% NEQ 0 (SET JErrorLevel=%ERRORLEVEL%)
	CALL:BuildSolution %JSource%/mmi/mmi/Converters "%JConfig%|%JPlatform%" %JOutPath%Converters
	IF %ERRORLEVEL% NEQ 0 (SET JErrorLevel=%ERRORLEVEL%)
EXIT /B 0

REM ------------------------------  Set Branch  ------------------------------------------------------------
:SetBranch
	FOR /F "tokens=2" %%a IN ('git -C %JSource% branch ') DO (SET JBranch=%%a)
EXIT /B 0

REM ------------------------------  Clean Source  ----------------------------------------------------------
:CleanSource
	CALL::JPrint Start cleaning : %JSource%
	REM GIT -C %JSource% clean -fx -d

	GIT -C %JSource% submodule update --init --recursive

	REM %JSource%\mmi\mmi\Mmi.sln

	RMDIR /S /Q %JSource%\Ifcs
	RMDIR /S /Q %JSource%\mmi\mmi\Bin
	RMDIR /S /Q %JSource%\mmi\mmi\Temp
	RMDIR /S /Q %JSource%\handler\cpp\bin
	RMDIR /S /Q %JSource%\handler\cpp\output

	RMDIR /S /Q %JSource%\handler\Simulator\ApplicationFiles\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\ExternalUtility\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITFootPrint\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimAdapter\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimDevices\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimConfiguration\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimCommon\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIT100SimCore\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIDHRDevices\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\UnitTest\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIT50Devices\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\MapForms\bin
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimCommon\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIT100Simulator\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIT100SimCore\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIDHRDevices\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\UnitTest\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CIT50Devices\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\MapForms\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\ReportAnalyser\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\ExternalUtility\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIFilterDefinition\obj
	RMDIR /S /Q %JSource%\mmi\mmi\XSideAlignment\obj
	RMDIR /S /Q %JSource%\mmi\mmi\RecipeOverviewModule.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIAreas\obj
	RMDIR /S /Q %JSource%\mmi\mmi\Ocv.WPF.SurfaceModule.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerWaCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIWaferAlignment\obj
	RMDIR /S /Q %JSource%\mmi\mmi\Authentication\obj
	RMDIR /S /Q %JSource%\mmi\mmi\RecipeOverviewModule\obj
	RMDIR /S /Q %JSource%\mmi\mmi\MainModule\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerRecipeOverviewCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\SurfaceModule\obj
	RMDIR /S /Q %JSource%\mmi\mmi\OcvMainModule\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIOcv.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerOcvCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIOcv\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UICalib.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerCalibCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerCadCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerLead3DCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UICalib\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerLead2DCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\ProtocolLayerCommonLeadedCS\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UILeadDefinition\obj
	RMDIR /S /Q %JSource%\mmi\mmi\WPFGUI\obj
	RMDIR /S /Q %JSource%\mmi\mmi\WPF_Mmi_SPC_GUI_WPF\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UIWPF\obj
	RMDIR /S /Q %JSource%\mmi\mmi\CommonLeaded\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UILead3D\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UICommonLeaded\obj
	RMDIR /S /Q %JSource%\mmi\mmi\UILead2D\obj
	RMDIR /S /Q %JSource%\mmi\mmi\WPF_Mmi_SPC_GUI_WPF.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\WPFCommon.Test\obj
	RMDIR /S /Q %JSource%\mmi\mmi\WPFCommon\obj
	RMDIR /S /Q %JSource%\mmi\mmi\Helixtoolkit\HelixToolkit.Wpf\obj
	RMDIR /S /Q %JSource%\mmi\mmi\HtmlPrinter\obj
	RMDIR /S /Q %JSource%\mmi\mmi\luxbeam_64dll\obj
	RMDIR /S /Q %JSource%\mmi\mmi\MmiSaveLogs\obj
	RMDIR /S /Q %JSource%\mmi\mmi\XSL\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITFootPrint\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimAdapter\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimDevices\obj
	RMDIR /S /Q %JSource%\handler\Simulator\CIT100Simulator\CITSimConfiguration\obj

EXIT /B 0

REM ------------------------------  Copy Mock Licence  -----------------------------------------------------
:CopyMockLicence
	SET JSource=%1

	SET LicenseFile=%JSource%/mmi/mmi/mmi_stat/integration/code/MockLicenseDll/Win32/Debug/License.dll
	copy %LicenseFile% %JSource%/mmi/mmi/Bin/Win32/Debug
	copy %LicenseFile% C:/icos
EXIT /B 0

REM ------------------------------  Build Solution  --------------------------------------------------------
:BuildSolution
	SET SolutionFile=%1.sln
	SET JBuildConf=%2
	SET JOutFile=%3
	
	ECHO Building %SolutionFile% [%JBuildConf%]
	SET JDevEnvExe="%VS120COMNTOOLS%../IDE/devenv.com"
	%JDevEnvExe% %SolutionFile% /build %JBuildConf% /out %JOutFile%.txt | findstr ">------"
	CALL::JPrint Solution File : %SolutionFile%
	TYPE %JOutFile%.txt | findstr "Build:" | findstr "====" >> %JCD%/JLog.txt
EXIT /B 0

REM ------------------------------  Run CDA Tests  ---------------------------------------------------------
:JRunCdaTest
	SET JTestPath=%1\\cda\\integration
	SET JTName=%2
	SET JDebug=%3

	SET MethodName=e
	IF NOT %JDebug% == False (SET MethodName=debug)

	SET PyImpo=import os;import sys;sys.path.append(os.path.abspath('%JTestPath%'));import cda
	python -c "%PyImpo%;cda.debug.%MethodName%('%JTName%')"

	PAUSE
EXIT /B 0

REM ------------------------------  Run Auto Tests  --------------------------------------------------------
:J_AutoTest
	SET JTName=%1
	SET JSlots=%2
	SET JStartUp=%3
	SET JDebugVision=%4
	SET JCopyMmi=%5
	SET JTestPath=%JSource%\\libs\\testing

	CALL:JPython KillTask()

	REM Running VMware Workstations
	CALL:JPython RunSlots('%JSlots%', 'False')

	CALL:JPython ModifyVisionSystem(%J_SRC_NUM%)

	SET params='%JTestPath%', '%JTName%', '%JStartUp%', '%JDebugVision%', '%JCopyMmi%', '%JConfig%', '%JPlatform%'
	CALL:JPython RunTest(%params%)
EXIT /B 0

REM ------------------------------  Run All Tests  ---------------------------------------------------------
:RunAllTests
	SET JSource=%1
	
	SET JTestRunner=%JSource%/libs/testing/testrunner.py -g MMI_AUTOPLAY_TEST
	SET JTests=-t %JSource%/handler/tests
	SET JSystem=-c %JSource%/handler/cpp/bin/%JConfig%/system
	SET JSimul=-s %JSource%/handler/Simulator/ApplicationFiles/bin/%JConfig%
	SET JFab=-f %JSource%/handler/FabLink
	SET JSetupPath=mmiSetupsPath='//klasj/ktfiles/Regions/Belgium/ICOS/RD/RD_Share/CI/Software/MMI/Daily builds'
	SET JOutFile=TestReport.txt
	python %JTestRunner% %JTests% %JSystem% %JSimul% %JFab% -n 1 -r 2 --%JSetupPath% > %JOutFile%
	CALL::JPrint Completed      : All Tests
EXIT /B 0

REM ------------------------------  Shut down  -------------------------------------------------------------
:JShutDown
	CALL::JPrint Shuting down the machine.
	SHUTDOWN /s /f
EXIT /B 0

REM ------------------------------  Restart  ---------------------------------------------------------------
:JRestart
	CALL::JPrint Restarting the machine.
	SHUTDOWN /r /f
EXIT /B 0

REM ------------------------------  Clean Directory  -------------------------------------------------------
:JCleanDir
	SET JSource=%1

	del /q %JSource%\*
	for /d %%x in (%JSource%\*) do @rd /s /q "%%x"
EXIT /B 0

REM ------------------------------  Print  -----------------------------------------------------------------
:JPrint
	ECHO %DATE:~0,3% %TIME:~0,5% %*>> %JCD%/JLog.txt
EXIT /B 0

REM ------------------------------  Message  ---------------------------------------------------------------
:Message
	ECHO OFF
	ECHO '
	ECHO ' ****************************************************************************
	ECHO ' %*
	ECHO ' ****************************************************************************
	ECHO '
	ECHO ON
	PAUSE
EXIT /B 0
