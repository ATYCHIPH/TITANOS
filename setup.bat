@echo off
setlocal

cd /d "%~dp0"

echo.
echo TITANOS setup
echo =============
echo This will install dependencies, build the desktop app, and produce the Windows installer.
echo.

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js/npm is required before running TITANOS setup.
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python is required before running TITANOS setup.
  exit /b 1
)

echo Installing Python backend package...
cd /d "%~dp0TITANOS-core"
python -m pip install -e . || exit /b 1

echo Installing desktop packaging dependencies...
npm.cmd install || exit /b 1

echo Installing React UI dependencies...
cd /d "%~dp0titanos-ui"
npm.cmd install || exit /b 1

echo Building TITANOS desktop app and installer...
cd /d "%~dp0TITANOS-core"
npm.cmd run dist:dir || exit /b 1
npx.cmd electron-builder --win nsis || exit /b 1
npm.cmd run release:manifest || exit /b 1

echo.
echo TITANOS is ready.
echo Installer:
echo   %~dp0TITANOS-core\release\TITANOS Setup 1.0.0.exe
echo.
echo Launching unpacked desktop app for verification...
start "" "%~dp0TITANOS-core\release\win-unpacked\TITANOS.exe"

endlocal
