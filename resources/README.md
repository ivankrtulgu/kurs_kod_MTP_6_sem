# Resources Directory

Эта папка содержит статические ресурсы приложения.

## Структура

- `icons/` - иконки приложения
  - `icon-open-book.png` - основная иконка окна приложения

## Использование

Ресурсы загружаются через `Path` для обеспечения кроссплатформенности:

```python
from pathlib import Path

icon_path = Path(__file__).parent.parent / "resources" / "icons" / "icon-open-book.png"
```
