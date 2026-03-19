@echo off
REM Batch build script for Nuitka (Windows)
REM Run from project root. Assumes a virtualenv at .venv with python & packages installed.

set VENV_PY=%~dp0.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
    echo Virtualenv python not found at %VENV_PY%. Falling back to system python.
    set VENV_PY=python
)

%VENV_PY% -m pip install --upgrade nuitka setuptools wheel

set OUTDIR=%~dp0dist_main
if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"

%VENV_PY% -m nuitka --standalone --remove-output --output-dir="%OUTDIR%" --include-data-dir=assets=assets --windows-disable-console main.py

echo Build finished. Check %OUTDIR% for the built application (look for main.dist).
pause