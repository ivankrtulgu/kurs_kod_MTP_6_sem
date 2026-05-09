# Quick Start - Security Analysis

Быстрый старт для анализа безопасности приложения.

## Установка

```bash
# 1. Установить инструменты безопасности
pip install -r security/requirements-security.txt

# 2. Установить pre-commit hooks (опционально)
pre-commit install
```

## Запуск сканирования

### Windows

```cmd
security\run_security_scan.bat
```

### Linux/Mac

```bash
chmod +x security/run_security_scan.sh
./security/run_security_scan.sh
```

## Просмотр результатов

После завершения сканирования откройте HTML-отчет:

```bash
# Windows
start security\reports\security_summary.html

# Linux
xdg-open security/reports/security_summary.html

# Mac
open security/reports/security_summary.html
```

## Отчеты

Все отчеты сохраняются в `security/reports/`:

| Файл | Описание |
|------|----------|
| `security_summary.html` | Сводный HTML-отчет |
| `bandit_report.txt` | SAST-анализ кода |
| `safety_report.txt` | Уязвимости в зависимостях |
| `pip_audit_report.json` | Аудит pip-пакетов |
| `secrets_baseline.json` | Обнаруженные секреты |
| `pylint_report.txt` | Качество кода |
| `semgrep_report.txt` | Продвинутый SAST |

## Интерпретация результатов

### Уровни серьезности

- 🔴 **HIGH/CRITICAL** — требует немедленного исправления
- 🟡 **MEDIUM** — исправить в ближайшее время
- 🔵 **LOW** — исправить при возможности
- ⚪ **INFO** — информационное сообщение

### Что делать при обнаружении уязвимостей

1. Просмотрите отчет и определите приоритеты
2. Для критических уязвимостей — исправьте немедленно
3. Для зависимостей — обновите пакеты: `pip install --upgrade <package>`
4. Для кода — следуйте рекомендациям в `COMMON_VULNERABILITIES.md`
5. Повторите сканирование после исправлений

## Pre-commit hooks

Автоматические проверки перед каждым коммитом:

```bash
# Установка
pre-commit install

# Запуск вручную
pre-commit run --all-files

# Обновление hooks
pre-commit autoupdate
```

## CI/CD

GitHub Actions автоматически запускает security scan при каждом push/PR.

Просмотр результатов:
1. Перейдите в раздел "Actions" на GitHub
2. Выберите workflow "Security Scan"
3. Скачайте артефакты с отчетами

## Частые проблемы

### Инструменты не установлены

```bash
pip install -r security/requirements-security.txt
```

### Ошибка "command not found"

Убедитесь, что Python и pip добавлены в PATH.

### Слишком много ложных срабатываний

Настройте исключения в `.bandit`, `.pylintrc`, `.pre-commit-config.yaml`.

## Дополнительная информация

- [Полная документация](README.md)
- [Контрольный список безопасности](SECURITY_CHECKLIST.md)
- [Распространенные уязвимости](COMMON_VULNERABILITIES.md)
- [Политика безопасности](../SECURITY.md)
