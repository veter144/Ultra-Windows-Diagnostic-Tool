@echo off
cd /d "%~dp0"
where dotnet >nul 2>&1 || (echo Dotnet runtime not found. Install .NET Desktop Runtime 8.0 and try again.& echo.& pause & exit /b 1)
dotnet "ConsoleApp2.dll"
if errorlevel 1 (echo.& echo App exited with error %%errorlevel%%.& pause)

