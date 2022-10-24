CALL:Initialize %0

REM            ┌──────────────────────────┐
REM            │       Clean Source       │
REM            ├──────────────────────────┤
REM            │ 2 │ CIT100.sln  │ Han    │
REM            │ 3 │ Mmi.sln     │ Mmi    │
REM            └───┴─────────────┴────────┘

rem CALL:JCleanSource D:\CI\Src1 -Han Mmi 


REM       ┌─────────────────────────────────────┐
REM       │           Build Source              │
REM       ├─────────────────────────────────────┤
REM       │ 2 │ Configurations  │ Debug Release │
REM       │ 3 │ Platform        │ Win32 x64     │
REM       │ 4 │ Visual Studio   │ 2017 2022     │
REM       │ 5 │ CIT100.sln      │ HanAll Han    │
REM       │ 6 │ Mmi.sln         │ Mmi           │
REM       │ 7 │ Other Solutions │ Others        │
REM       └───┴─────────────────┴───────────────┘

 CALL:BuildSource D:\CI\Src1 Debug Win32 2017 -Han Mmi Others
rem CALL:BuildSource D:\CI\Src3 Debug Win32 2022 Han -Mmi -Others

SET JSource=D:\CI\Src3
DEL /Q %JSource%\mmi\mmi\Bin\Win32\Debug\DisplayDLLWrapper.*
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\DisplayClient\DISPLAY\Debug
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\DisplayClient\DisplayRes\Debug
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\DisplayClient\DisplayRes\x64
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\DisplayClient\DISPLAYTASK\Debug
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\DisplayClient\DISPLAYTASK\x64
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\*_i.c
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\*_p.c
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\*.tlb
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\Display.h
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\DisplayTask.h
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\INTERFACE\dlldata.c
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\Output\*_i.c
DEL /Q %JSource%\mmi\mmi\display_libs\DisplayClient\Output\*.h
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\IcosDisplay\x64
RMDIR /S /Q %JSource%\mmi\mmi\display_libs\IPL\x64\Debug

REM --------------------------------------------------------------------------------------------------------
REM ----------------------------              End of Execution              --------------------------------
REM --------------------------------------------------------------------------------------------------------
TYPE %JCD%\JTemp.txt
EXIT /B %ERRORLEVEL%

REM ------------------------------  Initialize  ------------------------------------------------------------
:Initialize
	REM The following change directory request is needed only to run from NotePad++
	For %%A in (%1) do (
		SET JCD=%%~dpA
	)
	CD /d %JCD%
	SET JCD=%CD%
	ECHO     Build Status > %JCD%/JTemp.txt
	ECHO     ------------ >> %JCD%/JTemp.txt
EXIT /B 0

REM ------------------------------  Build Source  ----------------------------------------------------------
:BuildSource
	SET JSource=%1
	SET JConfig=%2
	SET JPlatform=%3

	SET JVS2017="C:/Program Files (x86)/Microsoft Visual Studio 12.0/Common7/IDE/devenv.com"
	SET JVS2022="C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/devenv.com"
	IF "%4" == "2022" (
		SET JDevEnvExe=%JVS2022%
	) ELSE (
		SET JDevEnvExe=%JVS2017%
	)

	SET JConPlat="%JConfig%|%JPlatform%"

	FOR /f %%i IN ('git -C %JSource% rev-parse HEAD') DO SET JCommit=%%i
	FOR /F "tokens=2" %%a IN ('git -C %JSource% branch ') DO SET JBranch=%%a

	CALL::JPrint Source : %JSource% [%JConPlat%]
	CALL::JPrint Branch : %JBranch% (%JCommit:~0,11%)
	CALL::JPrint DevEnv : Microsoft Visual Studio %4

	IF "%5" == "HanAll" (
		CALL:BuildSln handler/cpp/CIT100 %JConPlat% Handler
	)
	IF "%5" == "Han" (
		CALL:BuildSln handler/cpp/CIT100 %JConPlat% Handler
		CALL:JCleanHanTemp %JSource%
	)
	IF "%6" == "Mmi" (
		CALL:BuildSln mmi/mmi/mmi %JConPlat% MMi
	)
	SET JSimPath=handler/Simulator/CIT100Simulator/CIT100Simulator
	IF "%7" == "Others" (
		IF "%JPlatform%" == "Win32" (
			CALL:BuildSln %JSimPath% "%JConfig%|X86" Simulator
		) ELSE (
			CALL:BuildSln %JSimPath% "%JConfig%|X64" Simulator
		)

		CALL:BuildSln mmi/mmi/MockLicense %JConPlat% MockLicense
		CALL:BuildSln mmi/mmi/Converters %JConPlat% Converters
		REM CALL:BuildSln libs/DLStub/DLStub/DLStub %JConPlat% DLStub
		REM CALL:BuildSln libs/DLStub/ICOSDaemonStub/ICOSDaemonStub %JConPlat% ICOSDaemonStub
	)
EXIT /B 0

REM ------------------------------  Build Solution  --------------------------------------------------------
:BuildSln
	SET SolutionFile=%JSource%/%1.sln
	SET JBuildConf=%2
	SET JOutFile=%JSource%/Out_%3.txt
	
	ECHO Building %SolutionFile% [%JBuildConf%]
	%JDevEnvExe% %SolutionFile% /build %JBuildConf% /out %JOutFile%
	REM IF %ERRORLEVEL% == 0 (
	REM 	CALL::JPrint Build Success  : %SolutionFile%
	REM ) ELSE (
	REM 	CALL::JPrint Build Failed   : %SolutionFile%
	REM )
 
	ECHO OFF
	FOR /F "UseBackQ Delims==" %%A IN ("%JOutFile%") DO SET lastline=%%A
	ECHO ON
	SET SolName=%3                .
	CALL::JPrint %SolName:~0,15%:%lastline%
EXIT /B 0

REM ------------------------------  Clean Source  ----------------------------------------------------------
:JCleanSource
	SET JSource=%1
	IF "%2" == "Han" (
		RD /S /Q "%JSource%/handler/cpp/bin"
		RD /S /Q "%JSource%/handler/cpp/output"
	)
	IF "%3" == "Mmi" (
		RD /S /Q "%JSource%/mmi/mmi/output"
		RD /S /Q "%JSource%/mmi/mmi/Bin"
		RD /S /Q "%JSource%/mmi/mmi/Temp/Win32"
		RD /S /Q "%JSource%/mmi/mmi/Temp/x64"
		RD /S /Q "%JSource%/mmi/mmi/mmi/Debug
		RD /S /Q "%JSource%/mmi/mmi/mmi_stat/Debug
		RD /S /Q "%JSource%/mmi/mmi/display_libs/DisplayClient/DISPLAY/Debug
		RD /S /Q "%JSource%/mmi/mmi/display_libs/DisplayClient/DISPLAY/x64
		REM RD /S /Q "%JSource%/mmi/mmi/.vs
	)
EXIT /B 0

REM ------------------------------  Clean Handler Temp  ----------------------------------------------------
:JCleanHanTemp
	SET JSource=%1

	SET AbsPat=import os;import sys;sys.path.append(os.path.abspath('..\JAutomate'))
	SET ImpCle=from KLA.KlaSourceBuilder import KlaSourceCleaner
	python -c "%AbsPat%;%ImpCle%;KlaSourceCleaner(0).RemoveHandlerTemp('%JSource%')"
	CALL::JPrint Removing temp files from : %JSource%\handler
EXIT /B 0

REM ------------------------------  Print  -----------------------------------------------------------------
:JPrint
	ECHO %DATE% %TIME:~0,5% %*>> %JCD%/JLog.txt
	ECHO %DATE% %TIME:~0,5% %*>> %JCD%/JTemp.txt
EXIT /B 0
