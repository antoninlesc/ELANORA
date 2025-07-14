@echo off
setlocal enabledelayedexpansion
REM Move to repo root (two levels up from scripts)
cd /d %~dp0\..\..

:ask_env
set /p ENV="Enter environment (dev/prod/server): "
set "ENV=%ENV: =%"
if /i "%ENV%"=="dev" (
    goto ask_docker
) else if /i "%ENV%"=="prod" (
    call :check_docker_with_retry
    cd website\docker\website-prod
    set ENVIRONMENT=prod
    echo Running: docker-compose up
    docker-compose up
    if errorlevel 1 (
        echo.
        echo ERROR: Docker compose failed!
        pause
    )
    goto :eof
) else if /i "%ENV%"=="server" (
    call :check_docker_with_retry
    cd website\docker\website-server
    set ENVIRONMENT=server
    echo Running: docker-compose up
    docker-compose up
    if errorlevel 1 (
        echo.
        echo ERROR: Docker compose failed!
        pause
    )
    goto :eof
) else (
    echo Invalid environment. Please enter 'dev', 'prod', or 'server'.
    goto ask_env
)

:ask_docker
set /p USE_DOCKER="Do you want to use only Docker for development (yes/no/back)?: "
set "USE_DOCKER=%USE_DOCKER: =%"
if /i "%USE_DOCKER%"=="yes" (
    call :check_docker_with_retry
    cd website\docker\website-dev
    set ENVIRONMENT=dev
    echo Running: docker-compose up
    docker-compose up
    if errorlevel 1 (
        echo.
        echo ERROR: Docker compose failed!
        pause
    )
    goto :eof
) else if /i "%USE_DOCKER%"=="no" (
    call :check_docker_for_db_with_retry
    
    set "REPO_ROOT=%CD%\website"
    wt.exe ^
        new-tab --title "Database" cmd /k "cd /d !REPO_ROOT!\docker\website-dev && set ENVIRONMENT=dev && docker-compose up db" ^
        ; new-tab --title "Frontend" cmd /k "cd /d !REPO_ROOT!\frontend && set ENVIRONMENT=dev && npm install && npm run dev" ^
        ; new-tab --title "Backend" cmd /k "cd /d !REPO_ROOT!\backend && set ENVIRONMENT=dev && poetry install && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8018"
    goto :eof
) else if /i "%USE_DOCKER%"=="back" (
    goto ask_env
) else (
    echo Invalid choice. Please enter 'yes', 'no', or 'back'.
    goto ask_docker
)

:check_docker_with_retry
:docker_retry_loop
echo Checking Docker availability...
docker version >nul 2>&1
if %errorlevel% equ 0 (
    echo Docker is available.
    goto :eof
) else (
    echo.
    echo Docker is not running or not installed.
    echo Please start Docker Desktop and wait for it to fully load.
    echo.
    pause
    echo.
    goto docker_retry_loop
)

:check_docker_for_db_with_retry
:docker_db_retry_loop
echo Checking Docker availability for database...
docker version >nul 2>&1
if %errorlevel% equ 0 (
    echo Docker is available for database container.
    goto :eof
) else (
    echo.
    echo Docker is not running - needed for database container.
    echo Please start Docker Desktop and wait for it to fully load.
    echo.
    pause
    echo.
    goto docker_db_retry_loop
)