; Telos Installer Script for Inno Setup
; This creates a professional Windows installer

#define MyAppName "Telos"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Telos Team"
#define MyAppURL "https://telos.dev"
#define MyAppExeName "Telos.exe"

[Setup]
; Basic app information
AppId={{8F9E4A2C-1B3D-4E5F-9A7B-2C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output configuration
OutputDir=dist
OutputBaseFilename=TelosSetup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes

; User interface
WizardStyle=modern
SetupIconFile=icon.ico
; UninstallDisplayIcon={app}\{#MyAppExeName}

; Privileges (run as normal user)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Architecture
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "autostart"; Description: "Start Telos automatically when Windows starts"; GroupDescription: "Additional options:"; Flags: checked

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Config example
Source: "config.yaml.example"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
Source: "docs\PRIVACY_POLICY.md"; DestDir: "{app}\docs"; Flags: ignoreversion; DestName: "PRIVACY_POLICY.txt"
; Prompts folder (if needed)
Source: "prompts\*"; DestDir: "{app}\prompts"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Quick Launch shortcut (if selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
; Autostart shortcut (if selected)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
; Option to launch after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional)
Type: filesandordirs; Name: "{userappdata}\Telos"

[Code]
// Custom installation messages
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption := 
    'This will install Telos, an AI-powered productivity tracker, on your computer.' + #13#10#13#10 +
    'Telos runs quietly in the background and helps you understand how you spend your time.' + #13#10#13#10 +
    'Click Next to continue.';
end;

// Check if app is running before install
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if CheckForMutexes('TelosAppMutex') then
  begin
    if MsgBox('Telos is currently running. Please close it before continuing installation.' + #13#10#13#10 + 
              'Click OK to close Telos and continue, or Cancel to exit setup.', 
              mbConfirmation, MB_OKCANCEL) = IDOK then
    begin
      // Try to close the app gracefully
      Exec('taskkill.exe', '/IM Telos.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Result := True;
    end
    else
      Result := False;
  end;
end;

// Show completion message
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-install tasks can go here
  end;
end;

