[Setup]
AppId=3A.SmartBannerManager
AppName=3A Smart Banner Manager
AppVersion=1.0.0
AppVerName=3A Smart Banner Manager 1.0.0
AppPublisher=3A
DefaultDirName={localappdata}\Programs\3A Smart Banner Manager
DefaultGroupName=3A Smart Banner Manager
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=3A_Smart_Banner_Manage_Setup
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\3A_Smart_Banner_Manage.exe
Compression=lzma2
SolidCompression=yes
[Files]
Source: "dist\3A_Smart_Banner_Manage.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\3A Smart Banner Manager"; Filename: "{app}\3A_Smart_Banner_Manage.exe"
Name: "{autodesktop}\3A Smart Banner Manager"; Filename: "{app}\3A_Smart_Banner_Manage.exe"
[Run]
Filename: "{app}\3A_Smart_Banner_Manage.exe"; Description: "Launch 3A Smart Banner Manager"; Flags: nowait postinstall skipifsilent
