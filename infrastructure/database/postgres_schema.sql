-- Library App Database Schema
-- PostgreSQL schema for library application
-- Converted from SQLite schema

-- Books table
-- Stores bibliographic records according to GOST R 7.0.4-2020
CREATE TABLE IF NOT EXISTS books (
    -- System fields
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Required fields (per GOST R 7.0.4-2020)
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT DEFAULT '',
    responsibility TEXT DEFAULT '',
    edition TEXT DEFAULT '',
    place TEXT NOT NULL,
    publisher TEXT NOT NULL,
    year INTEGER NOT NULL,
    pages INTEGER NOT NULL,
    isbn TEXT NOT NULL,
    copyright TEXT DEFAULT '',
    udc TEXT DEFAULT '',
    bbk TEXT DEFAULT '',
    author_mark TEXT DEFAULT '',

    -- Additional fields
    reviewers TEXT DEFAULT '',
    annotation TEXT DEFAULT '',
    abstract TEXT DEFAULT '',
    doi TEXT DEFAULT '',
    content_type TEXT DEFAULT 'Текст',
    access_method TEXT DEFAULT 'непосредственный',

    -- File paths
    qr_code_path TEXT DEFAULT '',
    cover_image_path TEXT DEFAULT '',

    -- Full-Text Search vector
    search_vector tsvector
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_author_year ON books(author, year);
CREATE INDEX IF NOT EXISTS idx_books_place_publisher ON books(place, publisher);
CREATE INDEX IF NOT EXISTS idx_books_search_vector ON books USING GIN(search_vector);

-- FTS Trigger Function
CREATE OR REPLACE FUNCTION books_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('russian', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('russian', coalesce(NEW.subtitle, '')), 'B') ||
        setweight(to_tsvector('russian', coalesce(NEW.abstract, '')), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- FTS Trigger
DROP TRIGGER IF EXISTS trg_books_search_vector_update ON books;
CREATE TRIGGER trg_books_search_vector_update
BEFORE INSERT OR UPDATE ON books
FOR EACH ROW EXECUTE FUNCTION books_search_vector_update();

-- Readers table
CREATE TABLE IF NOT EXISTS readers (
    id SERIAL PRIMARY KEY,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    birth_date TIMESTAMP,
    phone TEXT,
    email TEXT,
    home_address TEXT,
    registration_date TIMESTAMP,
    status TEXT CHECK(status IN ('active', 'blocked', 'expired')) DEFAULT 'active',
    notes TEXT,
    passport_series TEXT,
    passport_number TEXT
);

-- Book Items table
CREATE TABLE IF NOT EXISTS book_items (
    id SERIAL PRIMARY KEY,
    inventory_number TEXT UNIQUE NOT NULL,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    location TEXT,
    qr_code_path TEXT
);

-- Loan Records table
CREATE TABLE IF NOT EXISTS loan_records (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES book_items(id) ON DELETE CASCADE,
    reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE CASCADE,
    issue_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP NOT NULL,
    return_date TIMESTAMP,
    condition_on_issue TEXT,
    condition_on_return TEXT
);

-- View for simplified book listing
CREATE OR REPLACE VIEW v_books_summary AS
SELECT
    id,
    author,
    title,
    subtitle,
    place,
    publisher,
    year,
    pages,
    isbn,
    udc,
    bbk,
    created_at
FROM books
ORDER BY year DESC, title ASC;

-- View for books with full bibliographic info
CREATE OR REPLACE VIEW v_books_full AS
SELECT
    id,
    author,
    title,
    subtitle,
    responsibility,
    edition,
    place,
    publisher,
    year,
    pages,
    isbn,
    copyright,
    udc,
    bbk,
    author_mark,
    reviewers,
    annotation,
    abstract,
    doi,
    content_type,
    access_method,
    created_at,
    qr_code_path,
    cover_image_path
FROM books
ORDER BY created_at DESC;
