# Security Reports Directory

Эта директория содержит отчеты по результатам сканирования безопасности.

## Генерируемые файлы

После запуска `run_security_scan.sh` или `run_security_scan.bat` здесь появятся:

- `security_summary.html` - сводный HTML-отчет
- `bandit_report.json` - результаты Bandit (JSON)
- `bandit_report.txt` - результаты Bandit (текст)
- `safety_report.json` - уязвимости в зависимостях (JSON)
- `safety_report.txt` - уязвимости в зависимостях (текст)
- `pip_audit_report.json` - аудит pip-пакетов
- `sbom.json` - Software Bill of Materials
- `secrets_baseline.json` - baseline для detect-secrets
- `pylint_report.json` - результаты Pylint (JSON)
- `pylint_report.txt` - результаты Pylint (текст)
- `semgrep_report.json` - результаты Semgrep (JSON)
- `semgrep_report.txt` - результаты Semgrep (текст)

## Примечание

Отчеты не коммитятся в Git (см. `.gitignore`), так как они:
- Содержат временные данные
- Могут раскрывать информацию о уязвимостях
- Генерируются автоматически при каждом запуске
