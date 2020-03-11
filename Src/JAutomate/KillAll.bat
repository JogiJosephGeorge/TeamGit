ECHO OFF
IF "%1" NEQ "" (
	echo kill only one %1
	CALL:JTaskKill %1
) ELSE (
	CALL:JTaskKill Mmi.exe
	CALL:JTaskKill console.exe
	CALL:JTaskKill CIT100Simulator.exe
	CALL:JTaskKill HostCamServer.exe
	CALL:JTaskKill Ves.exe
)

REM --------------------------------------------------------------------------------------------------------
REM ----------------------------              End of Execution              --------------------------------
REM --------------------------------------------------------------------------------------------------------
EXIT /B %ERRORLEVEL%

REM ------------------------------  Set Source  ------------------------------------------------------------
:JTaskKill
	TASKLIST /FI "IMAGENAME eq %1" 2>NUL | FIND /I /N "%1">NUL
	IF "%ERRORLEVEL%" == "0" (

		TASKKILL /IM %1 /T /F
			
		TASKLIST /FI "IMAGENAME eq %1" 2>NUL | FIND /I /N "%1">NUL
		IF "%ERRORLEVEL%" NEQ "0" (
			ECHO %1 still running!!!
		) ELSE (
			ECHO %1 has been killed.
		)
	)
	
EXIT /B 0
