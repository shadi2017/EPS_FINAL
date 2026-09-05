Set WinScriptHost = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
WinScriptHost.CurrentDirectory = FSO.GetParentFolderName(WScript.ScriptFullName)
WinScriptHost.Run Chr(34) & FSO.BuildPath(WinScriptHost.CurrentDirectory, "run_eps.bat") & Chr(34), 0
Set WinScriptHost = Nothing
