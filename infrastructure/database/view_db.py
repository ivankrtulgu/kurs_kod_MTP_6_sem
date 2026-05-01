"""Скрипт просмотра содержимого базы данных."""
from pathlib import Path

from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager


def view_database() -> None:
    """Просмотреть содержимое базы данных."""
    with PostgresDatabaseManager(settings.DATABASE_URL).get_connection() as conn:
        cursor = conn.cursor()
        
        # Список таблиц
        print("\n=== ТАБЛИЦЫ:")
        cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table['tablename']}")
        
        # Структура таблицы books
        print("\n=== СТРУКТУРА TABLE 'books':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'books' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"  {'#':<3} {'Имя поля':<20} {'Тип':<15} {'NOT NULL':<10}")
        print("  " + "-" * 50)
        for i, col in enumerate(columns, 1):
            name = col['column_name']
            dtype = col['data_type']
            notnull = 'YES' if col['is_nullable'] == 'NO' else 'NO'
            print(f"  {i:<3} {name:<20} {dtype:<15} {notnull:<10}")
        
        # Индексы
        print("\n=== ИНДЕКСЫ:")
        cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'books';")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  - {idx['indexname']}")
        
        # Данные
        print("\n=== ДАННЫЕ В TABLE 'books':")
        cursor.execute("SELECT COUNT(*) as count FROM books;")
        count = cursor.fetchone()['count']
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
                id_ = row['id']
                author = row['author']
                title = row['title']
                year = row['year']
                isbn = row['isbn']
                author_short = (author[:22] + "...") if len(author) > 25 else author
                title_short = (title[:27] + "...") if len(title) > 30 else title
                print(f"  {id_:<5} {author_short:<25} {title_short:<30} {year:<5} {isbn:<20}")
    print()


if __name__ == "__main__":
    view_database()
