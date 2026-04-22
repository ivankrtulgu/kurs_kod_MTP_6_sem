"""Скрипт просмотра содержимого базы данных."""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.parent.parent / "library.db"


def view_database(db_path: Path | None = None) -> None:
    """Просмотреть содержимое базы данных.
    
    Args:
        db_path: Путь к файлу БД.
    """
    if db_path is None:
        db_path = DB_PATH
    
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        print("  Сначала выполните: python init_db.py")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Список таблиц
    print("\n=== ТАБЛИЦЫ:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # Структура таблицы books
    print("\n=== СТРУКТУРА TABLE 'books':")
    cursor.execute("PRAGMA table_info(books);")
    columns = cursor.fetchall()
    print(f"  {'#':<3} {'Имя поля':<20} {'Тип':<10} {'NOT NULL':<10} {'PK':<5}")
    print("  " + "-" * 55)
    for col in columns:
        cid, name, dtype, notnull, default, pk = col
        print(f"  {cid:<3} {name:<20} {dtype:<10} {'YES' if notnull else 'NO':<10} {'YES' if pk else '':<5}")
    
    # Индексы
    print("\n=== ИНДЕКСЫ:")
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND tbl_name='books';")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"  - {idx[0]} on {idx[1]}")
    
    # Данные
    print("\n=== ДАННЫЕ В TABLE 'books':")
    cursor.execute("SELECT COUNT(*) FROM books;")
    count = cursor.fetchone()[0]
    print(f"  Всего записей: {count}")
    
    if count > 0:
        print("\n  Последние 5 записей:")
        cursor.execute("""
            SELECT id, author, title, year, isbn 
            FROM books 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        rows = cursor.fetchall()
        print(f"  {'ID':<5} {'Автор':<25} {'Название':<30} {'Год':<5} {'ISBN':<20}")
        print("  " + "-" * 90)
        for row in rows:
            id_, author, title, year, isbn = row
            author_short = (author[:22] + "...") if len(author) > 25 else author
            title_short = (title[:27] + "...") if len(title) > 30 else title
            print(f"  {id_:<5} {author_short:<25} {title_short:<30} {year:<5} {isbn:<20}")
    
    conn.close()
    print()


if __name__ == "__main__":
    view_database()
