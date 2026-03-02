@echo off
setlocal
cd /d "%~dp0"
call "%~dp0.venv\Scripts\activate.bat"
python -m pip install -r "%~dp0requirements.txt"
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0dist" rmdir /s /q "%~dp0dist"
python -m PyInstaller --clean "%~dp0ContadorMTR03.spec"
endlocal
