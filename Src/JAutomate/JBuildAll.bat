REM Build Options
REM ~~~~~~~~~~~~~
REM Configurations : Debug Release
REM Platform       : Win32 x64

CALL:JSetSource 1
CALL:Initialize %0
SET IsStartUp=1
SET IsDebugEnabled=0
SET DoCopyMMI=1

 CALL:JPrintMenu

REM python -c "from JAutomate import JAutomate; JAutomate().RunSlots('1_2', 'True')"
REM CALL:BuildSource %JConfig% %JPlatform%
REM CALL:JEveningBuild

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
	
	IF %J_SRC_NUM% == 1 SET JSource=D:\QuEST\CI\Src1
	IF %J_SRC_NUM% == 2 SET JSource=D:\QuEST\CI\Src2
	IF %J_SRC_NUM% == 3 SET JSource=D:\QuEST\CI\Src3
	IF %J_SRC_NUM% == 4 SET JSource=D:\QuEST\CI\Src4
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
	python -c "from JAutomate import JAutomate; JAutomate().PrintMenu('%JSource%', '%JTestName%')"
	SET JInput=%errorlevel%
	
	IF "%JInput%" == "1" START python -i %JSource%\libs\testing\my.py
	IF "%JInput%" == "2" CALL:J_AutoTest %JTestName% %IsStartUp% %IsDebugEnabled% %DoCopyMMI%
	IF "%JInput%" == "3" CALL:J_Handler %JTestName%
	IF "%JInput%" == "4" CALL:J_MMi %JTestName%
	IF "%JInput%" == "5" CALL:J_Handler_MMi
	IF "%JInput%" == "6" COPY D:\QuEST\MyProjects\xPort\xPort_IllumReference.xml C:\icos\xPort
	IF "%JInput%" == "7" COPY %JSource%\libs\testing\VisionSystem.py VisionSystem\VisionSystem%J_SRC_NUM%.py
	IF "%JInput%" == "8" CALL:JOpenTestFolder %JTestName%
	IF "%JInput%" == "9" CALL:JChangeTest
	IF "%JInput%" == "10" CALL:JInstallMMI 10.4a 7
	IF "%JInput%" == "11" START %JSource%\handler\cpp\CIT100.sln
	IF "%JInput%" == "12" START %JSource%\handler\Simulator\CIT100Simulator\CIT100Simulator.sln
	IF "%JInput%" == "13" START %JSource%\mmi\mmi\Mmi.sln
	IF "%JInput%" == "14" START %JSource%\mmi\mmi\MockLicense.sln
	IF "%JInput%" == "15" START %JSource%\mmi\mmi\Converters.sln
	IF "%JInput%" == "20" "C:\Program Files\TortoiseGit\bin\TortoiseGitProc.exe" /command:diff /path:%JSource%
	IF "%JInput%" == "30" "C:\Program Files\Git\mingw64\bin\wish.exe" 
	IF "%JInput%" == "31" python -c "from JAutomate import JAutomate; JAutomate().PrintMenu('%JSource%', '%JTestName%')"
	IF "%JInput%" == "99" CALL KillAll

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

REM ------------------------------  Run Given Slots  -------------------------------------------------------
:JRunSlots
	SET JSlots=%1

	SET JSlots=%JSlots:_= %
	SET JPause=%2

	FOR %%a IN (%JSlots%) DO (
		SET IsRunning=False
		SETLOCAL EnableDelayedExpansion
		FOR /f %%b IN ('"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -vp 1 list') DO (
			SET temp1=%%b
			SET temp2=!temp1:~15,1!
			IF "!temp2!" == "%%a" SET IsRunning=True
		)

		IF "!IsRunning!" == "False" (
			ECHO Starting VMware %%a
			START "C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe" "C:\MVS8000\slot%%a\MVS8000_stage2.vmx"
			PAUSE
			SET JPause=False
		) ELSE (
			ECHO Reseting VMware %%a
			"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -vp 1 reset C:\MVS8000\slot%%a\MVS8000_stage2.vmx
		)
	)
	IF "%JPause%" == "True" TIMEOUT 8
EXIT /B 0

REM ------------------------------  Evening Build  ---------------------------------------------------------
:JEveningBuild
	CALL::Message ********************   STARTING EVENING BUILD    ********************

	REM SET JSrcNums=1 2 3 4
	SET JSrcNums=1

	FOR %%A IN (%JSrcNums%) DO (
		CALL:JSetSource %%A
		CALL:CleanSource
	)

	FOR %%A IN (%JSrcNums%) DO (
		CALL:JSetSource %%A
		CALL:BuildSource %JConfig% %JPlatform%
	)

	 CALL:JShutDown
	REM CALL:JRestart

	CALL::JPrint Evening Build Completed.
EXIT /B 0

REM ------------------------------  Start Handler Console  -------------------------------------------------
:J_Handler
	SET HandlerPath=%JSource%/handler
	SET TestName=%1
	SET JSlots=%2

	REM Running VMware Workstations
	REM CALL:JRunSlots %JSlots% False

	REM Kill MMI
	CALL KillAll

	ECHO Starting Console
	start %HandlerPath%/cpp/bin/Win32/debug/system/console.exe %HandlerPath%/tests/%TestName%~

	ECHO Starting Simulator
	start %HandlerPath%/Simulator/ApplicationFiles/bin/x86/Debug/CIT100Simulator.exe %HandlerPath%/tests/%TestName%~ %HandlerPath%/cpp/bin/Win32/debug/system

	REM ECHO Starting HostCamServer
	REM start C:/MVS7000/software_29.6.0_MVS7000_Daily.20150212_1/hostsw/hostcam/HostCamServer.exe
EXIT /B 0

REM ------------------------------  Restart MMi  -----------------------------------------------------------
:J_MMi
	SET JSlots=%2

	SET JMMI_PATH=%JSource%\mmi\mmi\Bin\%JPlatform%\%JConfig%
	SET JMOCK_PATH=%JSource%\mmi\mmi\mmi_stat\integration\code\MockLicenseDll\%JPlatform%\%JConfig%

	REM Kill MMI
	CALL KillAll Mmi.exe

	REM Running VMware Workstations
	IF "%JSlots%" NEQ "" CALL:JRunSlots %JSlots% True

	REM COPY MOCK LICENCE
	IF NOT EXIST %JMOCK_PATH%\License.dll PAUSE
	COPY %JMOCK_PATH%\License.dll %JMMI_PATH% /Y
	COPY D:\QuEST\MyProjects\xPort\xPort_IllumReference.xml C:\icos\xPort

	start %JMMI_PATH%\Mmi.exe
EXIT /B 0

REM ------------------------------  Start Handler and MMi  -------------------------------------------------
:J_Handler_MMi
	CALL:J_Handler %JTestName%
	CALL:J_MMi %JTestName%
EXIT /B 0

REM ------------------------------  Open Test Folder  ------------------------------------------------------
:JOpenTestFolder
	start %JSource%\handler\tests\%1
EXIT /B 0

REM ------------------------------  Change Test  -----------------------------------------------------------
:JChangeTest
	python -c "from JAutomate import JAutomate; JAutomate().SelectTest()"
	CALL:JSetTestName
EXIT /B 0

REM ------------------------------  Set Test Name  ---------------------------------------------------------
:JSetTestName
	for /f "delims=" %%a in (Tests.txt) do set JTestName=%%a
EXIT /B 0

REM ------------------------------  Build Source  ----------------------------------------------------------
:BuildSource
	SET JConfig=%1
	SET JPlatform=%2

	SET JOutPath=%JSource%/Out_

	SET JSimuPF=x86
	IF %JPlatform% == "x64" (SET JSimuPF=x64)

	SET JErrorLevel=0
	FOR /F "tokens=2" %%a IN ('git -C %JSource% branch ') DO (SET JBranch=%%a)
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

REM ------------------------------  Clean Source  ----------------------------------------------------------
:CleanSource
	CALL::JPrint Start cleaning : %JSource%
	GIT -C %JSource% clean -fx -d

	GIT -C %JSource% submodule update --init --recursive

	%JSource%\mmi\mmi\Mmi.sln

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
	%JDevEnvExe% %SolutionFile% /build %JBuildConf% /out %JOutFile%.txt
	IF %ERRORLEVEL% == 0 (
		CALL::JPrint Build Success  : %SolutionFile%
	) ELSE (
		CALL::JPrint Build Failed   : %SolutionFile%
	)
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

	REM Kill All
	CALL KillAll

	REM Running VMware Workstations
	CALL:JRunSlots %JSlots% False

	COPY VisionSystem\VisionSystem%J_SRC_NUM%.py %JTestPath%\VisionSystem.py
	REM "C:\Program Files\7-Zip\7z.exe" x -oC:\ -y "C:\MVSSlots.7z"

	SET params='%JTestPath%', '%JTName%', '%JStartUp%', '%JDebugVision%', '%JCopyMmi%', '%JConfig%', '%JPlatform%'
	python -c "from JAutomate import JAutomate; JAutomate().RunTest(%params%)"
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
