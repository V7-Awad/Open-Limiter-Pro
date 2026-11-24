; Script generated for Inno Setup 6
; OpenLimiter Pro Windows Setup Script - Current User Only Installation

#define MyAppName "OpenLimiter Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "OpenLimiter Team"
#define MyAppURL "https://github.com/V7-Awad/Open-Limiter-Pro"
#define MyAppExeName "OpenLimiterPro.exe"

[Setup]
AppId={{E72A8B49-38DF-4E11-9A8C-8F492E9A6C01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Current User Only (Per-User Installation)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=no
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Process Management & Overwrite Protection
AppMutex=OpenLimiterPro_SingleInstance_Mutex
CloseApplications=force
CloseApplicationsFilter=OpenLimiterPro.exe

OutputDir=dist
OutputBaseFilename=OpenLimiterPro_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "build\bin\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "OpenLimiterPro"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  // Terminate any running instance before file replacement
  Exec('cmd.exe', '/c taskkill /F /IM OpenLimiterPro.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Exec('cmd.exe', '/c taskkill /F /IM OpenLimiterPro.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
