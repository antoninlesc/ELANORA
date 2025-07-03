@echo off
REM filepath: .githooks/setup-hooks.bat

echo Setting up Git hooks...

REM Get the repository root
for /f "tokens=*" %%i in ('git rev-parse --show-toplevel') do set REPO_ROOT=%%i

REM Copy pre-commit hook to .git\hooks\
copy "%REPO_ROOT%\.githooks\pre-commit" "%REPO_ROOT%\.git\hooks\pre-commit" >nul

echo Pre-commit hook installed successfully!
echo Your commits will now automatically run code quality checks.
pause
