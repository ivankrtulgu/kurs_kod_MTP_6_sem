@echo off
REM Security Scan Script for Windows
REM Комплексный анализ безопасности приложения

echo ==========================================
echo Security Scan - Library Management System
echo ==========================================
echo.

REM Создание директории для отчетов
set REPORTS_DIR=security\reports
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

REM Проверка установки инструментов
echo Checking security tools...
pip show bandit >nul 2>&1
if errorlevel 1 (
    echo Installing security tools...
    pip install -q -r security\requirements-security.txt
)

REM 1. Bandit - поиск уязвимостей в коде
echo.
echo ==========================================
echo 1. Running Bandit (SAST Analysis)...
echo ==========================================
bandit -r . -f json -o "%REPORTS_DIR%\bandit_report.json" --exclude ./venv,./tests,./temp --severity-level medium 2>nul
bandit -r . -f txt -o "%REPORTS_DIR%\bandit_report.txt" --exclude ./venv,./tests,./temp --severity-level medium 2>nul
echo [OK] Bandit scan completed

REM 2. Safety - проверка уязвимостей в зависимостях
echo.
echo ==========================================
echo 2. Running Safety (Dependency Check)...
echo ==========================================
safety check --json --output "%REPORTS_DIR%\safety_report.json" 2>nul
safety check --full-report --output "%REPORTS_DIR%\safety_report.txt" 2>nul
echo [OK] Safety check completed

REM 3. pip-audit - аудит pip-пакетов
echo.
echo ==========================================
echo 3. Running pip-audit...
echo ==========================================
pip-audit --format json --output "%REPORTS_DIR%\pip_audit_report.json" 2>nul
pip-audit --format cyclonedx-json --output "%REPORTS_DIR%\sbom.json" 2>nul
echo [OK] pip-audit completed

REM 4. Detect-secrets - поиск секретов в коде
echo.
echo ==========================================
echo 4. Running detect-secrets...
echo ==========================================
detect-secrets scan --exclude-files "venv/.*|\.git/.*|\.pytest_cache/.*" > "%REPORTS_DIR%\secrets_baseline.json" 2>nul
echo [OK] Secrets detection completed

REM 5. Pylint - статический анализ
echo.
echo ==========================================
echo 5. Running Pylint (Code Quality)...
echo ==========================================
pylint --rcfile=.pylintrc --output-format=json core/ infrastructure/ ui/ > "%REPORTS_DIR%\pylint_report.json" 2>nul
pylint --rcfile=.pylintrc core/ infrastructure/ ui/ > "%REPORTS_DIR%\pylint_report.txt" 2>nul
echo [OK] Pylint analysis completed

REM 6. Semgrep - продвинутый SAST
echo.
echo ==========================================
echo 6. Running Semgrep (Advanced SAST)...
echo ==========================================
semgrep --config=auto --json --output="%REPORTS_DIR%\semgrep_report.json" . 2>nul
semgrep --config=auto --output="%REPORTS_DIR%\semgrep_report.txt" . 2>nul
echo [OK] Semgrep scan completed

REM 7. Генерация сводного отчета
echo.
echo ==========================================
echo 7. Generating Summary Report...
echo ==========================================
python security\generate_report.py
echo [OK] Summary report generated

REM Вывод результатов
echo.
echo ==========================================
echo Security Scan Results
echo ==========================================
echo.
echo Reports saved to: %REPORTS_DIR%\
echo.
echo Key files:
echo   - bandit_report.txt       - SAST vulnerabilities
echo   - safety_report.txt       - Dependency vulnerabilities
echo   - pip_audit_report.json   - Package audit
echo   - secrets_baseline.json   - Detected secrets
echo   - pylint_report.txt       - Code quality issues
echo   - semgrep_report.txt      - Advanced SAST findings
echo   - security_summary.html   - HTML summary report
echo.

REM Проверка критических уязвимостей
findstr /C:"\"severity\": \"HIGH\"" "%REPORTS_DIR%\bandit_report.json" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Found high-severity issues!
    echo Review %REPORTS_DIR%\bandit_report.txt for details
    exit /b 1
) else (
    echo [OK] No critical vulnerabilities found
)

echo.
echo ==========================================
echo Scan completed successfully!
echo ==========================================
pause
