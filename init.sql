-- Инициализация базы данных PostgreSQL для системы управления библиотекой

-- Создание таблицы книг
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    author VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    publisher VARCHAR(255),
    year INTEGER,
    pages INTEGER,
    place VARCHAR(100),
    doi VARCHAR(100),
    cover_image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);

-- Создание таблицы инвентарных экземпляров
CREATE TABLE IF NOT EXISTS book_items (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    inventory_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    location VARCHAR(255),
    qr_code_path VARCHAR(500),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Индексы для инвентаря
CREATE INDEX IF NOT EXISTS idx_book_items_book_id ON book_items(book_id);
CREATE INDEX IF NOT EXISTS idx_book_items_inventory_number ON book_items(inventory_number);
CREATE INDEX IF NOT EXISTS idx_book_items_status ON book_items(status);

-- Создание таблицы читателей
CREATE TABLE IF NOT EXISTS readers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    card_number VARCHAR(50) UNIQUE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE
);

-- Индексы для читателей
CREATE INDEX IF NOT EXISTS idx_readers_card_number ON readers(card_number);
CREATE INDEX IF NOT EXISTS idx_readers_last_name ON readers(last_name);

-- Создание таблицы записей о выдаче
CREATE TABLE IF NOT EXISTS loan_records (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    reader_id INTEGER NOT NULL,
    loan_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    return_date TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES book_items(id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE CASCADE
);

-- Индексы для записей о выдаче
CREATE INDEX IF NOT EXISTS idx_loan_records_item_id ON loan_records(item_id);
CREATE INDEX IF NOT EXISTS idx_loan_records_reader_id ON loan_records(reader_id);
CREATE INDEX IF NOT EXISTS idx_loan_records_return_date ON loan_records(return_date);

-- Комментарии к таблицам
COMMENT ON TABLE books IS 'Каталог книг библиотеки';
COMMENT ON TABLE book_items IS 'Инвентарные экземпляры книг';
COMMENT ON TABLE readers IS 'Читатели библиотеки';
COMMENT ON TABLE loan_records IS 'Записи о выдаче и возврате книг';

-- Вставка тестовых данных (опционально)
-- INSERT INTO books (author, title, isbn, publisher, year, pages, place)
-- VALUES
--     ('Кнут Д.', 'Искусство программирования', '978-5-8459-0080-6', 'Вильямс', 2000, 720, 'М.'),
--     ('Страуструп Б.', 'Язык программирования C++', '978-5-8459-2089-7', 'Бином', 2011, 1136, 'М.');

-- Вывод информации
SELECT 'Database initialized successfully' AS status;
