# PowerShell build script for Nuitka (Windows)
# Run from project root. Assumes a virtualenv at .venv with python & packages installed.

$venvPython = "$PSScriptRoot\\.venv\\Scripts\\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtualenv python not found at $venvPython. Falling back to system python."
    $venvPython = "python"
}

# Ensure Nuitka is installed in the active environment
& $venvPython -m pip install --upgrade nuitka setuptools wheel

# Output directory
$outDir = "$PSScriptRoot\\dist_main"

# Remove previous output (uncomment if you want automatic clean)
if (Test-Path $outDir) { Remove-Item -Recurse -Force $outDir }

# Build command:
# --standalone: produce a runnable folder (recommended for pygame)
# --include-data-dir=assets=assets : copy local assets folder into the packaged app under 'assets'
# --windows-disable-console : hide console window (omit while debugging)
# --remove-output : let Nuitka manage output cleanup

& $venvPython -m nuitka --standalone --remove-output --output-dir="$outDir" --include-data-dir=assets=assets --windows-disable-console main.py

Write-Host "Build finished. Check $outDir for the built application (look for main.dist)."