@echo off
REM Скрипт для запуска всех тестов библиотечной системы (Windows)

echo ==========================================
echo   Запуск тестов библиотечной системы
echo ==========================================
echo.

REM Проверка установки pytest
where pytest >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ pytest не установлен
    echo Установите: pip install -r tests/requirements-test.txt
    exit /b 1
)

echo ✅ pytest найден
echo.

REM Запуск тестов
echo 🧪 Запуск всех тестов...
echo.

pytest -v ^
    --cov=core ^
    --cov=infrastructure ^
    --cov=ui ^
    --cov-report=html ^
    --cov-report=term-missing ^
    --tb=short

REM Проверка результата
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo   ✅ Все тесты прошли успешно!
    echo ==========================================
    echo.
    echo 📊 Отчет о покрытии: htmlcov\index.html
    echo.
) else (
    echo.
    echo ==========================================
    echo   ❌ Некоторые тесты не прошли
    echo ==========================================
    echo.
    exit /b 1
)
