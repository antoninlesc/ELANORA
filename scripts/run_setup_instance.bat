@echo off
REM Run the ELANORA instance setup wizard using Poetry from backend root
cd /d %~dp0\..\website\backend
poetry run python ../../installer/setup_instance.py || (
    echo.
    echo Python script failed! Press any key to see the error...
    pause > nul
)
echo.
echo Script finished. Press any key to exit.
pause > nul