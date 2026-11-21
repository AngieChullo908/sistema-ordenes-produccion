Unicode true
Target amd64-unicode
Name "Gestión de Órdenes de Producción"
OutFile "../Gestion_Ordenes_Produccion.exe"
RequestExecutionLevel user
SilentInstall silent
AutoCloseWindow true
Var ReturnCode
Section
 IfFileExists "$EXEDIR\runtime\pythonw.exe" runtime_ok
 MessageBox MB_ICONSTOP "No se encuentra el entorno Python. Reinstale la aplicación."
 SetErrorLevel 1
 Quit
 runtime_ok:
 SetOutPath "$EXEDIR"
 ExecWait '"$EXEDIR\runtime\pythonw.exe" "$EXEDIR\main.py"' $ReturnCode
 SetErrorLevel $ReturnCode
SectionEnd
