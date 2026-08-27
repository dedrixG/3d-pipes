@echo off
setlocal
cd /d "%~dp0\.."

python -m pip install -r requirements.txt "pyinstaller>=6"
if errorlevel 1 exit /b 1

python -m PyInstaller --noconfirm --distpath dist --workpath build\pyinstaller-win packaging\windows\3d-pipes.spec
if errorlevel 1 exit /b 1

copy /y dist\3DPipes.exe dist\3DPipes.scr
echo Built dist\3DPipes.exe
echo Copy dist\3DPipes.scr to install as a screensaver (right-click - Install).
echo Unsigned: SmartScreen may warn. That is expected.
