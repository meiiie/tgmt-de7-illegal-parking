#ifndef Stage
  #error Stage must be supplied by build-desktop.ps1
#endif
#ifndef Dist
  #error Dist must be supplied by build-desktop.ps1
#endif
#ifndef Downloads
  #error Downloads must be supplied by build-desktop.ps1
#endif

[Setup]
AppId={{A9D68AA1-6FD8-4B29-A558-87CF1ED5EC46}
AppName=Curb
AppVersion={#AppVersion}
AppPublisher=Meiiie
AppPublisherURL=https://github.com/meiiie/tgmt-de7-illegal-parking
AppSupportURL=https://github.com/meiiie/tgmt-de7-illegal-parking/issues
AppUpdatesURL=https://github.com/meiiie/tgmt-de7-illegal-parking/releases/latest
VersionInfoVersion={#AppVersion}
VersionInfoDescription=Curb Quick Install
DefaultDirName={localappdata}\Programs\Curb
DefaultGroupName=Curb
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#Dist}
OutputBaseFilename=Curb-Package-{#AppVersion}-x64
SetupIconFile={#Stage}\curb.ico
UninstallDisplayIcon={app}\Curb.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
ShowLanguageDialog=no
CloseApplications=yes
RestartApplications=no
AppMutex=Local\Curb.Desktop
UninstallDisplayName=Curb — Giám sát dừng đỗ
WizardSmallImageFile={#Stage}\installer-mark.bmp

[Files]
Source: "{#Stage}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*,*.pyc,outputs\*"
Source: "{#Downloads}\MicrosoftEdgeWebview2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{group}\Curb"; Filename: "{app}\Curb.exe"; AppUserModelID: "Curb.Desktop"
Name: "{autodesktop}\Curb"; Filename: "{app}\Curb.exe"; AppUserModelID: "Curb.Desktop"

[Run]
Filename: "{app}\Curb.exe"; Description: "Open Curb"; Flags: nowait; Check: ShouldLaunchApp

[Code]
var
  BrandTitle, BrandNote, ProgressText: TNewStaticText;
  Track, Fill: TPanel;

function ShouldLaunchApp: Boolean;
begin
  Result := ExpandConstant('{param:NOOPEN|0}') <> '1';
end;

procedure InitializeWizard;
begin
  WizardForm.Caption := 'Curb {#AppVersion}';
  WizardForm.Color := $E4E4E4;
  WizardForm.MainPanel.Color := clWhite;
  WizardForm.BackButton.Visible := False;
  WizardForm.NextButton.Visible := False;
  WizardForm.CancelButton.Caption := 'Hủy';
  WizardForm.FilenameLabel.Visible := False;
  WizardForm.StatusLabel.Visible := False;
  WizardForm.ProgressGauge.Visible := False;
  BrandTitle := TNewStaticText.Create(WizardForm);
  BrandTitle.Parent := WizardForm.InstallingPage;
  BrandTitle.SetBounds(0, ScaleY(20), WizardForm.ProgressGauge.Width, ScaleY(42));
  BrandTitle.Font.Name := 'Segoe UI';
  BrandTitle.Font.Size := 21;
  BrandTitle.Font.Style := [fsBold];
  BrandTitle.Caption := 'Đang cài đặt Curb';
  BrandNote := TNewStaticText.Create(WizardForm);
  BrandNote.Parent := WizardForm.InstallingPage;
  BrandNote.AutoSize := False;
  BrandNote.SetBounds(0, ScaleY(70), WizardForm.ProgressGauge.Width, ScaleY(55));
  BrandNote.Font.Size := 10;
  BrandNote.WordWrap := True;
  BrandNote.Caption := 'Phiên bản {#AppVersion} · Giám sát dừng đỗ đường phố' + #13#10 + 'Ứng dụng sẽ tự mở khi hoàn tất.';
  Track := TPanel.Create(WizardForm);
  Track.Parent := WizardForm.InstallingPage;
  Track.SetBounds(0, ScaleY(145), WizardForm.ProgressGauge.Width, ScaleY(7));
  Track.BevelOuter := bvNone;
  Track.ParentBackground := False;
  Track.Color := $D4D4D4;
  Fill := TPanel.Create(WizardForm);
  Fill.Parent := Track;
  Fill.SetBounds(0, 0, 0, Track.Height);
  Fill.BevelOuter := bvNone;
  Fill.ParentBackground := False;
  Fill.Color := $793B2B;
  ProgressText := TNewStaticText.Create(WizardForm);
  ProgressText.Parent := WizardForm.InstallingPage;
  ProgressText.AutoSize := False;
  ProgressText.SetBounds(0, ScaleY(170), WizardForm.ProgressGauge.Width, ScaleY(45));
  ProgressText.Font.Size := 10;
  ProgressText.Caption := 'Đang chuẩn bị các thành phần…';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpInstalling then begin
    WizardForm.CancelButton.Caption := 'Hủy';
    WizardForm.PageNameLabel.Caption := 'Curb';
    WizardForm.PageDescriptionLabel.Caption := 'Phiên bản {#AppVersion}';
  end;
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
var Percent: Integer;
begin
  if MaxProgress > 0 then begin
    Percent := Round(CurProgress * 100.0 / MaxProgress);
    Fill.Width := Round(Track.Width * Percent / 100.0);
    Fill.Visible := True;
    ProgressText.Caption := IntToStr(Percent) + '%';
  end;
end;

function HasWebView: Boolean;
var V: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V) or
    RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V)) and (V <> '') and (V <> '0.0.0.0');
end;

function HasVCRuntime: Boolean;
var Installed, Major, Minor: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) and
    RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Major', Major) and
    RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Minor', Minor) and
    (Installed = 1) and ((Major > 14) or ((Major = 14) and (Minor >= 44))) and
    FileExists(ExpandConstant('{sys}\msvcp140.dll'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not IsDotNetInstalled(net48, 0) then begin
    Result := 'Curb cần Microsoft .NET Framework 4.8. Cài thành phần này từ Microsoft rồi mở lại bộ cài Curb.';
    Exit;
  end;
  if not HasVCRuntime then begin
    try
      DownloadTemporaryFile('https://download.visualstudio.microsoft.com/download/pr/ebdab8e5-1d7b-4d9f-a11b-cbb1720c3b12/843068991DAAA1F73AD9F6239BCE4D0F6A07A51F18C37EA2A867E9BECA71295C/VC_redist.x64.exe',
        'vc_redist.x64.exe', '843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c', nil);
      if not ShellExec('runas', ExpandConstant('{tmp}\vc_redist.x64.exe'), '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, Code) then
        Result := 'Cần Microsoft Visual C++ x64 để phân tích video. Cho phép Windows cài thành phần Microsoft rồi chạy lại Curb Setup.'
      else if Code = 3010 then
        Result := 'Microsoft Visual C++ đã cài và yêu cầu khởi động lại Windows. Lưu công việc, khởi động lại máy rồi mở bộ cài Curb.'
      else if not HasVCRuntime then
        Result := 'Chưa cài được Microsoft Visual C++ x64. Cài runtime từ Microsoft rồi chạy lại bộ cài Curb.';
    except
      Result := 'Không tải được Microsoft Visual C++ x64. Kiểm tra Internet và chạy lại. ' + GetExceptionMessage;
    end;
    if Result <> '' then Exit;
  end;
  if not HasWebView then begin
    ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'Không cài được Microsoft WebView2. Kiểm tra kết nối Internet rồi thử lại.'
    else if not HasWebView then
      Result := 'Curb cần Microsoft WebView2. Cài thành phần này từ Microsoft rồi mở lại bộ cài Curb.';
  end;
end;
