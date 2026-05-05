#!/bin/bash
# Скрипт для запуска всех тестов библиотечной системы

echo "=========================================="
echo "  Запуск тестов библиотечной системы"
echo "=========================================="
echo ""

# Проверка установки pytest
if ! command -v pytest &> /dev/null
then
    echo "❌ pytest не установлен"
    echo "Установите: pip install -r tests/requirements-test.txt"
    exit 1
fi

echo "✅ pytest найден"
echo ""

# Запуск тестов
echo "🧪 Запуск всех тестов..."
echo ""

pytest -v \
    --cov=core \
    --cov=infrastructure \
    --cov=ui \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short

# Проверка результата
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ Все тесты прошли успешно!"
    echo "=========================================="
    echo ""
    echo "📊 Отчет о покрытии: htmlcov/index.html"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "  ❌ Некоторые тесты не прошли"
    echo "=========================================="
    echo ""
    exit 1
fi
