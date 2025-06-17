@echo off
setlocal enabledelayedexpansion

:: Get the directory where the script is located
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Container name
set "CONTAINER_NAME=python-dev-container"

echo Building dev container...
docker build -t %CONTAINER_NAME% .

echo Starting dev container...
docker run -it --rm ^
    --name %CONTAINER_NAME% ^
    -v "%PROJECT_DIR%:/app" ^
    -p 8000:8000 ^
    -w /app ^
    %CONTAINER_NAME%
