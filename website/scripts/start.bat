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
    cd lsfb-website\docker\MDL-Corpus-prod
    set ENV=prod && docker-compose up
    goto :eof
) else if /i "%ENV%"=="server" (
    cd lsfb-website\docker\MDL-Corpus-server
    set ENV=server && docker-compose up
    goto :eof
) else (
    echo Invalid environment. Please enter 'dev', 'prod', or 'server'.
    goto ask_env
)

:ask_docker
set /p USE_DOCKER="Do you want to use only Docker for development (yes/no/back)?: "
set "USE_DOCKER=%USE_DOCKER: =%"
if /i "%USE_DOCKER%"=="yes" (
    cd lsfb-website\docker\MDL-Corpus-dev
    set ENV=dev.docker && docker-compose up
    goto :eof
) else if /i "%USE_DOCKER%"=="no" (
    set "REPO_ROOT=%CD%\lsfb-website"
    wt.exe ^
        new-tab --title "Database" cmd /k "cd /d !REPO_ROOT!\docker\MDL-Corpus-dev && set ENV=dev && docker-compose up db" ^
        ; new-tab --title "Frontend" cmd /k "cd /d !REPO_ROOT!\frontend && set ENV=dev && npm install && npm run dev" ^
        ; new-tab --title "Backend" cmd /k "cd /d !REPO_ROOT!\backend && set ENV=dev && poetry install && poetry run fastapi dev app/main.py --port 8008"
    goto :eof
) else if /i "%USE_DOCKER%"=="back" (
    goto ask_env
) else (
    echo Invalid choice. Please enter 'yes', 'no', or 'back'.
    goto ask_docker
)