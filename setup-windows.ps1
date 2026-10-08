<#
  Growth Intelligence Platform: Windows setup
  Creates  <Parent>\<RepoName>  from the downloaded zip, makes the first commit, creates a PRIVATE GitHub repository,
  pushes, and opens the project in VS Code. Run from the folder that contains the zip (normally Downloads):

      powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1

  Options: -Parent "C:\Users\Pooja Mattey"  -RepoName growth-intelligence-platform  -Visibility private|public  -SkipGitHub  -SkipPython
  Sign-in to GitHub uses GitHub's own browser login (gh auth login). This script never asks for or stores a password or token.
#>
param(
  [string]$Parent = "C:\Users\Pooja Mattey",
  [string]$RepoName = "growth-intelligence-platform",
  [ValidateSet("private","public")][string]$Visibility = "private",
  [string]$ZipPath = (Join-Path $PSScriptRoot "growth-intelligence-platform-repo.zip"),
  [switch]$SkipGitHub,
  [switch]$SkipPython
)
# Compatible with Windows PowerShell 5.1 and PowerShell 7. Native tools (git, gh) report errors via exit codes,
# which are checked explicitly; "Stop" would turn their normal stderr output into fatal errors on 5.1.
$ErrorActionPreference = "Continue"
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "Failed: $what (exit $LASTEXITCODE)" -ForegroundColor Red; exit 1 } }
function Need($cmd, $install) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Write-Host "Missing: $cmd. Install with:  $install" -ForegroundColor Yellow; return $false }; return $true }

Write-Host "`n1/6 Checking prerequisites" -ForegroundColor Cyan
$ok = (Need "git" "winget install --id Git.Git -e") -and (Need "code" "winget install --id Microsoft.VisualStudioCode -e")
if (-not $SkipGitHub) { $ok = (Need "gh" "winget install --id GitHub.cli -e") -and $ok }
if (-not $ok) { Write-Host "Install the missing tools, open a NEW PowerShell window, and run this script again." -ForegroundColor Red; exit 1 }
if (-not (Test-Path $ZipPath)) { Write-Host "Zip not found: $ZipPath  (use -ZipPath to point to it)" -ForegroundColor Red; exit 1 }

$Target = Join-Path $Parent $RepoName
Write-Host "2/6 Creating $Target" -ForegroundColor Cyan
if (Test-Path $Target) { Write-Host "Folder already exists: $Target. Not overwriting. Rename or remove it, or use -RepoName." -ForegroundColor Red; exit 1 }
New-Item -ItemType Directory -Path $Parent -Force | Out-Null
$tmp = Join-Path $env:TEMP ("gip-" + [guid]::NewGuid())
Expand-Archive -Path $ZipPath -DestinationPath $tmp -ErrorAction Stop
$inner = Join-Path $tmp $RepoName; if (-not (Test-Path $inner)) { $inner = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName }
Move-Item -Path $inner -Destination $Target -ErrorAction Stop
Remove-Item $tmp -Recurse -Force

Write-Host "3/6 First commit" -ForegroundColor Cyan
Set-Location $Target
if (-not (git config --global user.name)) { Write-Host "Git needs your name and email once:  git config --global user.name ""Your Name""  and  git config --global user.email you@example.com" -ForegroundColor Yellow; exit 1 }
git init -b main | Out-Null; Check "git init"
git add -A; Check "git add"
git commit -m "Growth Intelligence Platform v8.0.0: initial import" | Out-Null; Check "git commit"
Write-Host ("   committed " + (git ls-files | Measure-Object).Count + " files")

if (-not $SkipPython) {
  Write-Host "4/6 Python environment (.venv) and test dependencies" -ForegroundColor Cyan
  if (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" } else { $py = "python" }
  & $py -m venv .venv; Check "python venv"
  & .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
  & .\.venv\Scripts\python.exe -m pip install --quiet -r requirements-dev.txt; Check "pip install"
  & .\.venv\Scripts\python.exe -m playwright install chromium
  $env:PYTHONUTF8 = "1"
  & .\.venv\Scripts\python.exe tests\run_offline.py
} else { Write-Host "4/6 Skipped Python setup" }

if (-not $SkipGitHub) {
  Write-Host "5/6 GitHub: creating $Visibility repository and pushing" -ForegroundColor Cyan
  gh auth status *> $null
  if ($LASTEXITCODE -ne 0) { gh auth login --web --git-protocol https; Check "GitHub sign-in" }
  $visFlag = "--" + $Visibility
  gh repo create $RepoName $visFlag --source . --remote origin --push --description "AI-native Enterprise Growth & Decision Intelligence Platform (Claude plugin)"; Check "gh repo create / push"
  Write-Host ("   " + (gh repo view --json url -q .url))
} else { Write-Host "5/6 Skipped GitHub" }

Write-Host "6/6 Opening VS Code" -ForegroundColor Cyan
code $Target
Write-Host "`nDone. In VS Code: Terminal > Run Task > 'Test: all suites'." -ForegroundColor Green
