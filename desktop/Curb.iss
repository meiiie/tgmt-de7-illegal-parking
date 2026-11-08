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
  WizardForm.Color := $F0F3F3;
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
  Track.Color := $E3E9E8;
  Fill := TPanel.Create(WizardForm);
  Fill.Parent := Track;
  Fill.SetBounds(0, 0, 0, Track.Height);
  Fill.BevelOuter := bvNone;
  Fill.ParentBackground := False;
  Fill.Color := $2E59ED;
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
    WizardForm.PageDescriptionLabel.Caption := 'Quan sát rõ. Xử lý có căn cứ.';
  end;
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
var Percent: Integer;
begin
  if MaxProgress > 0 then begin
    Percent := Round(CurProgress * 100.0 / MaxProgress);
    Fill.Width := Round(Track.Width * Percent / 100.0);
    Fill.Visible := True;
    ProgressText.Caption := IntToStr(Percent) + '% · Đang thiết lập trên máy của bạn';
  end;
end;

function HasWebView: Boolean;
var V: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V) or
    RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V)) and (V <> '') and (V <> '0.0.0.0');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not IsDotNetInstalled(net48, 0) then begin
    Result := 'Curb requires Microsoft .NET Framework 4.8. Install it from Microsoft and run this installer again.';
    Exit;
  end;
  if not HasWebView then begin
    ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'Could not install Microsoft WebView2. Check your Internet connection and try again.'
    else if not HasWebView then
      Result := 'Microsoft WebView2 is required. Install it from Microsoft and run this installer again.';
  end;
end;
