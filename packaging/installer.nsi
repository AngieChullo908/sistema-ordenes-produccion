Unicode true
Target amd64-unicode
!include "MUI2.nsh"
!include "x64.nsh"
Name "Gestión de Órdenes de Producción"
OutFile "../Gestion_Ordenes_Produccion_Instalador.exe"
InstallDir "$LOCALAPPDATA\Programs\GestionOrdenesProduccion"
InstallDirRegKey HKCU "Software\GestionOrdenesProduccion" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"
Function .onInit
 ${IfNot} ${RunningX64}
  MessageBox MB_ICONSTOP "Se requiere Windows de 64 bits."
  Abort
 ${EndIf}
FunctionEnd
Section "Aplicación"
 SetOutPath "$INSTDIR"
 File "../Gestion_Ordenes_Produccion.exe"
 File "../main.py"
 File "../verificar_entorno.py"
 File "../VERIFICAR_WINDOWS.bat"
 File "../requirements.txt"
 File /oname=LEER_PRIMERO.txt "LEER_PRIMERO_WINDOWS.txt"
 File /r /x __pycache__ "../app"
 File /r /x __pycache__ "../runtime"
 File /r /x __pycache__ "../vendor"
 File /r "../database"
 CreateDirectory "$SMPROGRAMS\Gestión de Órdenes de Producción"
 CreateShortcut "$SMPROGRAMS\Gestión de Órdenes de Producción\Gestión de Órdenes de Producción.lnk" "$INSTDIR\Gestion_Ordenes_Produccion.exe"
 CreateShortcut "$DESKTOP\Gestión de Órdenes de Producción.lnk" "$INSTDIR\Gestion_Ordenes_Produccion.exe"
 WriteUninstaller "$INSTDIR\Desinstalar.exe"
 WriteRegStr HKCU "Software\GestionOrdenesProduccion" "InstallDir" "$INSTDIR"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion" "DisplayName" "Gestión de Órdenes de Producción"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion" "DisplayVersion" "1.1.1"
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion" "NoModify" 1
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion" "NoRepair" 1
SectionEnd
Section "Uninstall"
 Delete "$DESKTOP\Gestión de Órdenes de Producción.lnk"
 Delete "$SMPROGRAMS\Gestión de Órdenes de Producción\Gestión de Órdenes de Producción.lnk"
 RMDir "$SMPROGRAMS\Gestión de Órdenes de Producción"
 Delete "$INSTDIR\Gestion_Ordenes_Produccion.exe"
 Delete "$INSTDIR\main.py"
 Delete "$INSTDIR\verificar_entorno.py"
 Delete "$INSTDIR\VERIFICAR_WINDOWS.bat"
 Delete "$INSTDIR\requirements.txt"
 Delete "$INSTDIR\LEER_PRIMERO.txt"
 RMDir /r "$INSTDIR\app"
 RMDir /r "$INSTDIR\runtime"
 RMDir /r "$INSTDIR\vendor"
 RMDir /r "$INSTDIR\database"
 Delete "$INSTDIR\Desinstalar.exe"
 RMDir "$INSTDIR"
 DeleteRegKey HKCU "Software\GestionOrdenesProduccion"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GestionOrdenesProduccion"
SectionEnd
