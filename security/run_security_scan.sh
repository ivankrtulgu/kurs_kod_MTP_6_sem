#!/bin/bash
# Security Scan Script
# Комплексный анализ безопасности приложения

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Security Scan - Library Management System"
echo "=========================================="
echo ""

# Создание директории для отчетов
REPORTS_DIR="security/reports"
mkdir -p "$REPORTS_DIR"

# Проверка установки инструментов
echo "Checking security tools..."
if ! command -v bandit &> /dev/null; then
    echo -e "${YELLOW}Installing security tools...${NC}"
    pip install -q -r security/requirements-security.txt
fi

# 1. Bandit - поиск уязвимостей в коде
echo ""
echo "=========================================="
echo "1. Running Bandit (SAST Analysis)..."
echo "=========================================="
bandit -r . \
    -f json \
    -o "$REPORTS_DIR/bandit_report.json" \
    --exclude ./venv,./tests,./temp \
    --severity-level medium \
    || true

bandit -r . \
    -f txt \
    -o "$REPORTS_DIR/bandit_report.txt" \
    --exclude ./venv,./tests,./temp \
    --severity-level medium \
    || true

echo -e "${GREEN}✓ Bandit scan completed${NC}"

# 2. Safety - проверка уязвимостей в зависимостях
echo ""
echo "=========================================="
echo "2. Running Safety (Dependency Check)..."
echo "=========================================="
safety check \
    --json \
    --output "$REPORTS_DIR/safety_report.json" \
    || true

safety check \
    --full-report \
    --output "$REPORTS_DIR/safety_report.txt" \
    || true

echo -e "${GREEN}✓ Safety check completed${NC}"

# 3. pip-audit - аудит pip-пакетов
echo ""
echo "=========================================="
echo "3. Running pip-audit..."
echo "=========================================="
pip-audit \
    --format json \
    --output "$REPORTS_DIR/pip_audit_report.json" \
    || true

pip-audit \
    --format cyclonedx-json \
    --output "$REPORTS_DIR/sbom.json" \
    || true

echo -e "${GREEN}✓ pip-audit completed${NC}"

# 4. Detect-secrets - поиск секретов в коде
echo ""
echo "=========================================="
echo "4. Running detect-secrets..."
echo "=========================================="
detect-secrets scan \
    --exclude-files 'venv/.*|\.git/.*|\.pytest_cache/.*' \
    > "$REPORTS_DIR/secrets_baseline.json" \
    || true

echo -e "${GREEN}✓ Secrets detection completed${NC}"

# 5. Pylint - статический анализ
echo ""
echo "=========================================="
echo "5. Running Pylint (Code Quality)..."
echo "=========================================="
pylint \
    --rcfile=.pylintrc \
    --output-format=json \
    core/ infrastructure/ ui/ \
    > "$REPORTS_DIR/pylint_report.json" \
    2>/dev/null || true

pylint \
    --rcfile=.pylintrc \
    core/ infrastructure/ ui/ \
    > "$REPORTS_DIR/pylint_report.txt" \
    2>/dev/null || true

echo -e "${GREEN}✓ Pylint analysis completed${NC}"

# 6. Semgrep - продвинутый SAST
echo ""
echo "=========================================="
echo "6. Running Semgrep (Advanced SAST)..."
echo "=========================================="
semgrep \
    --config=auto \
    --json \
    --output="$REPORTS_DIR/semgrep_report.json" \
    . \
    || true

semgrep \
    --config=auto \
    --output="$REPORTS_DIR/semgrep_report.txt" \
    . \
    || true

echo -e "${GREEN}✓ Semgrep scan completed${NC}"

# 7. Генерация сводного отчета
echo ""
echo "=========================================="
echo "7. Generating Summary Report..."
echo "=========================================="
python security/generate_report.py

echo -e "${GREEN}✓ Summary report generated${NC}"

# Вывод результатов
echo ""
echo "=========================================="
echo "Security Scan Results"
echo "=========================================="
echo ""
echo "Reports saved to: $REPORTS_DIR/"
echo ""
echo "Key files:"
echo "  - bandit_report.txt       - SAST vulnerabilities"
echo "  - safety_report.txt       - Dependency vulnerabilities"
echo "  - pip_audit_report.json   - Package audit"
echo "  - secrets_baseline.json   - Detected secrets"
echo "  - pylint_report.txt       - Code quality issues"
echo "  - semgrep_report.txt      - Advanced SAST findings"
echo "  - security_summary.html   - HTML summary report"
echo ""

# Проверка критических уязвимостей
CRITICAL_COUNT=$(grep -c '"severity": "HIGH"' "$REPORTS_DIR/bandit_report.json" 2>/dev/null || echo "0")
if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo -e "${RED}⚠ WARNING: Found $CRITICAL_COUNT high-severity issues!${NC}"
    echo "Review $REPORTS_DIR/bandit_report.txt for details"
    exit 1
else
    echo -e "${GREEN}✓ No critical vulnerabilities found${NC}"
fi

echo ""
echo "=========================================="
echo "Scan completed successfully!"
echo "=========================================="
