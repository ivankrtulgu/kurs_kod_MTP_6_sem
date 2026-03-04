# build_ui.py
import subprocess
import sys
from pathlib import Path

UI_DIR = Path("ui/forms")
OUTPUT_DIR = Path("ui/generated")

OUTPUT_DIR.mkdir(exist_ok=True)

print("🔨 Компиляция UI файлов...")

errors = []
for ui_file in UI_DIR.glob("*.ui"):
    py_file = OUTPUT_DIR / f"ui_{ui_file.stem}.py"
    print(f"  {ui_file.name} → {py_file.name}", end=" ... ")
    
    try:
        result = subprocess.run(
            ["pyuic5", "-x", str(ui_file), "-o", str(py_file)],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅")
    except subprocess.CalledProcessError as e:
        print("❌")
        errors.append((ui_file.name, e.stderr))
        print(f"   Ошибка: {e.stderr[:200]}...")

if errors:
    print(f"\n⚠️ Не скомпилировано файлов: {len(errors)}")
    for name, err in errors:
        print(f"  • {name}")
    print("\n💡 Попробуй открыть проблемный .ui файл в Qt Designer и пересохранить")
    sys.exit(1)
else:
    print("\n✅ Все файлы скомпилированы успешно!")