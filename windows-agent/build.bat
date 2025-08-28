@echo off
echo Building Windows Security Agent...

REM Set Go environment variables for Windows
set GOOS=windows
set GOARCH=amd64

REM Clean previous builds
if exist windows-agent.exe del windows-agent.exe

REM Download dependencies
echo Downloading dependencies...
go mod tidy

REM Build the agent
echo Building agent...
go build -ldflags="-s -w" -o windows-agent.exe .

if exist windows-agent.exe (
    echo Build successful!
    echo Executable: windows-agent.exe
    echo Size: 
    dir windows-agent.exe | find "windows-agent.exe"
) else (
    echo Build failed!
    exit /b 1
)

echo.
echo To run the agent:
echo   windows-agent.exe
echo.
echo To stop the agent:
echo   Press Ctrl+C
echo.
pause
