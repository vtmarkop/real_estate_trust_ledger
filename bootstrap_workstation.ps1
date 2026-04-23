[CmdletBinding()]
param(
    [switch]$SkipSeed,
    [switch]$SkipNpmInstall,
    [switch]$SkipPythonInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PythonBootstrapCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3.11 --version *> $null
            return @("py", "-3.11")
        }
        catch {
            return @("py")
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }

    throw "Python was not found. Install Python 3.11+ and rerun bootstrap_workstation.ps1."
}

function Invoke-CommandArray {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Command,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if ($Command.Length -gt 1) {
        & $Command[0] $Command[1..($Command.Length - 1)] @Arguments
    }
    else {
        & $Command[0] @Arguments
    }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonBootstrap = Get-PythonBootstrapCommand

Write-Host ""
Write-Host "Trust Ledger workstation bootstrap" -ForegroundColor Cyan
Write-Host "Repository: $repoRoot"
Write-Host ""

Push-Location $repoRoot
try {
    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating local virtual environment..." -ForegroundColor Yellow
        Invoke-CommandArray -Command $pythonBootstrap -Arguments @("-m", "venv", ".venv")
    }
    else {
        Write-Host "Virtual environment already exists." -ForegroundColor Green
    }

    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $venvPython -m pip install --upgrade pip

    if (-not $SkipPythonInstall) {
        Write-Host "Installing backend requirements..." -ForegroundColor Yellow
        & $venvPython -m pip install -r (Join-Path $apiRoot "requirements.txt")
    }
    else {
        Write-Host "Skipping backend requirements install." -ForegroundColor DarkYellow
    }

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm was not found. Install Node.js 20+ and rerun bootstrap_workstation.ps1."
    }

    if (-not $SkipNpmInstall) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Push-Location $webRoot
        try {
            npm install
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Skipping frontend dependency install." -ForegroundColor DarkYellow
    }

    Write-Host "Running database migrations..." -ForegroundColor Yellow
    Push-Location $apiRoot
    try {
        & $venvPython -m alembic upgrade head

        if (-not $SkipSeed) {
            Write-Host "Seeding demo data..." -ForegroundColor Yellow
            & $venvPython "dev_seed.py"
        }
        else {
            Write-Host "Skipping demo seed." -ForegroundColor DarkYellow
        }
    }
    finally {
        Pop-Location
    }

    Write-Host ""
    Write-Host "Bootstrap complete." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next commands:" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\python run_api.py"
    Write-Host "  .\.venv\Scripts\python run_web.py"
    Write-Host ""
}
finally {
    Pop-Location
}
