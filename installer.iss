#define AppName "3A_Smart_Banner_Manage"
#define AppVersion "1.1.0"
#define AppExe AppName + ".exe"
#ifndef SetupIcon
  #define SetupIcon "assets\icon.ico"
#endif

[Setup]
AppId=3A_Smart_Banner_Manage.Seller
AppName={#AppName}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}.0
DefaultDirName={localappdata}\Programs\{#AppName}
PrivilegesRequired=lowest
OutputDir=release
OutputBaseFilename={#AppName}_Setup
SetupIconFile={#SetupIcon}
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"

[Icons]
Name: "{userprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon
