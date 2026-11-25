[Setup]
AppId=3A.SmartBannerManager
AppName=3A_Smart_Banner_Manage
AppVersion=1.0.1
AppVerName=3A_Smart_Banner_Manage
AppPublisher=3A
DefaultDirName={localappdata}\Programs\3A_Smart_Banner_Manage
DefaultGroupName=3A_Smart_Banner_Manage
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
Name: "{group}\3A_Smart_Banner_Manage"; Filename: "{app}\3A_Smart_Banner_Manage.exe"
Name: "{autodesktop}\3A_Smart_Banner_Manage"; Filename: "{app}\3A_Smart_Banner_Manage.exe"
[Run]
Filename: "{app}\3A_Smart_Banner_Manage.exe"; Description: "Launch 3A_Smart_Banner_Manage"; Flags: nowait postinstall skipifsilent
