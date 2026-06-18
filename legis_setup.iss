; legis_setup.iss — Inno Setup Script — Legis Beta
#define MyAppName      "Legis"
#define MyAppVersion   "Beta"
#define MyAppPublisher "Lima e Paixão Advocacia"
#define MyAppURL       "https://legis.app"
#define MyAppExeName   "Legis.exe"
#define MyAppDesc      "Sistema de Gestão Jurídica"

[Setup]
AppId={{B7F2D1A3-5E9C-4F8B-A3D2-2C9E8F7A6B5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf64}\Legis
DefaultGroupName=Legis
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=Legis_Beta_Setup
SetupIconFile=legis.ico
UninstallDisplayIcon={app}\legis.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=130
PrivilegesRequired=admin
MinVersion=10.0
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDesc}
VersionInfoProductName={#MyAppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[CustomMessages]
brazilianportuguese.WelcomeLabel1=Bem-vindo ao instalador do {#MyAppName}
brazilianportuguese.WelcomeLabel2=Este assistente irá instalar o {#MyAppName} — {#MyAppDesc} no seu computador.%n%nOs dados serão salvos em Documentos\Legis com permissão total de acesso.%n%nClique em Avançar para continuar.

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\Legis\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "legis.ico";    DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";             Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\legis.ico"; Comment: "{#MyAppDesc}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";       Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\legis.ico"; Tasks: desktopicon; Comment: "{#MyAppDesc}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backups"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
