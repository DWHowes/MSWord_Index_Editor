; Word Index Editor -- Inno Setup script. Step 10b.
;
; Compile with:
;     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\WordIndexEditor.iss
;
; after the PyInstaller build has put a tree in dist\WordIndexEditor. See
; PACKAGING.md for the whole procedure and for what has to be verified in the
; installed copy rather than in a build log.
;
; MyAppVersion is kept in step with pyproject.toml by hand, because Inno cannot
; read it. tests/test_packaging_version.py asserts the two agree: two answers
; to "which version is this" would be found by a tester and by nobody else.

#define MyAppName "Word Index Editor"
#define MyAppVersion "0.1.0a0"
#define MyAppPublisher "D. W. Howes"
#define MyAppExeName "WordIndexEditor.exe"
#define MySourceDir "..\dist\WordIndexEditor"

[Setup]
AppId={{7A3C1E44-9C2B-4F71-B0D5-2E6A8F4D91C7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=WordIndexEditor-Setup-{#MyAppVersion}
SetupIconFile=..\src\wordindex\icons\wdx.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; `x64`, not `x64compatible`: the latter needs Inno Setup 6.3 and the build
; here is the 2023 one, which rejects it outright. The sibling installer uses
; the same spelling.
ArchitecturesInstallIn64BitMode=x64

; **Per-user, no UAC prompt, deliberately.** With `lowest`, `{autopf}` resolves
; to %LOCALAPPDATA%\Programs rather than C:\Program Files. An alpha tester is
; an indexer rather than an administrator, and nothing here needs machine-wide
; installation: this application writes its profiles, preferences and session
; logs to the user's own data directory and nothing at all beside the
; executable.
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; No [UninstallDelete], and that is a decision rather than an omission.
;
; The LaTeX editor needs one because it keeps a writable cache and its session
; logs beside the executable, so an uninstall there leaves a directory behind
; unless it is told not to. This application keeps nothing in {app}: profiles,
; preferences and logs all go to the user's own data directory, which an
; uninstaller has no business deleting. Somebody reinstalling should find their
; style profiles where they left them.
