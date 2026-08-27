# build.ps1
# Construye Esquemático en Windows: genera la carpeta distribuible,
# el paquete portable .zip y el instalador (si Inno Setup está disponible).
#
# Uso:
#   .\build.ps1              # todo
#   .\build.ps1 -SkipInstaller
#   .\build.ps1 -SkipPortable
#   .\build.ps1 -NoPyInstaller  # solo re-empaqueta lo ya construido

param(
    [switch]$SkipInstaller,
    [switch]$SkipPortable,
    [switch]$NoPyInstaller,
    [string]$Arch = "x64"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $Root
try {
$distDir = Join-Path $Root "dist"
$buildDir = Join-Path $Root "build"
$portableName = "Esquematico-portable"
$appVersion = "1.0.0"

Write-Host "=== Esquematico build script ===" -ForegroundColor Cyan
Write-Host "Arch: $Arch"

# 1) PyInstaller
if (-not $NoPyInstaller) {
    Write-Host "[1/3] Ejecutando PyInstaller..." -ForegroundColor Yellow
    pyinstaller --noconfirm --clean Esquematico.spec
    if (-not (Test-Path (Join-Path $distDir "Esquematico\Esquematico.exe"))) {
        throw "No se encontró el ejecutable de PyInstaller"
    }
} else {
    Write-Host "[1/3] Saltando PyInstaller (modo -NoPyInstaller)" -ForegroundColor Yellow
}

# 2) Copiar recursos y crear zip portable
if (-not $SkipPortable) {
    Write-Host "[2/3] Preparando paquete portable..." -ForegroundColor Yellow
    $portableDir = Join-Path $distDir $portableName
    if (Test-Path $portableDir) { Remove-Item -Recurse -Force $portableDir }

    # Copiar la salida de PyInstaller
    Copy-Item -Recurse -Force (Join-Path $distDir "Esquematico") $portableDir

    # Añadir recursos extra (icono, README)
    Copy-Item -Force (Join-Path $Root "esquematico\resources\icon.png") $portableDir
    if (Test-Path (Join-Path $Root "README.md")) {
        Copy-Item -Force (Join-Path $Root "README.md") $portableDir
    }

    # Documento de inicio
    $start = @"
Esquematico v$appVersion
=======================
Generador visual de esquemas electricos.

USO
  1. Ejecute Esquematico.exe
  2. Elija un simbolo en la biblioteca (izquierda)
  3. Coloquelo sobre el lienzo con un clic
  4. Use la herramienta Cable para conectar
  5. Guarde (Ctrl+S) o exporte (PNG/PDF)

No requiere instalacion. Ponte la carpeta donde quiera.
"@
    Set-Content -Path (Join-Path $portableDir "LEEME.txt") -Value $start -Encoding UTF8

    # Zip
    $zipPath = Join-Path $distDir "$portableName.zip"
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    Compress-Archive -Path "$portableDir\*" -DestinationPath $zipPath
    Write-Host "Portable creado: $zipPath" -ForegroundColor Green
}

# 3) Inno Setup installer
if (-not $SkipInstaller) {
    Write-Host "[3/3] Ejecutando Inno Setup..." -ForegroundColor Yellow
    $innoCandidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $iscc = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $iscc) {
        Write-Host "Inno Setup no encontrado. Instalador omitido." -ForegroundColor Red
        Write-Host "Descárgalo en: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    } else {
        $installerScript = Join-Path $Root "scripts\installer.iss"
        & $iscc "/DAppVersion=$appVersion" "/DDistDir=$distDir" $installerScript
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup falló"
        }
        Write-Host "Instalador creado en dist/Instalador-Esquematico-$appVersion.exe" -ForegroundColor Green
    }
}

Write-Host "=== Construcción finalizada ===" -ForegroundColor Green
Get-ChildItem $distDir | Select-Object Name, Length
} finally {
    Pop-Location
}
