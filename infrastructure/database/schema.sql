-- Library App Database Schema
-- SQLite schema for books table following GOST R 7.0.4-2020 standard
-- Created: 2026-03-02

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Books table
-- Stores bibliographic records according to GOST R 7.0.4-2020
CREATE TABLE IF NOT EXISTS books (
    -- System fields
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Required fields (per GOST R 7.0.4-2020)
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    responsibility TEXT NOT NULL,
    edition TEXT NOT NULL,
    place TEXT NOT NULL,
    publisher TEXT NOT NULL,
    year INTEGER NOT NULL,
    pages INTEGER NOT NULL,
    isbn TEXT NOT NULL,
    copyright TEXT NOT NULL,
    udc TEXT NOT NULL,
    bbk TEXT NOT NULL,
    author_mark TEXT NOT NULL,
    
    -- Additional fields
    reviewers TEXT DEFAULT '',
    annotation TEXT DEFAULT '',
    abstract TEXT DEFAULT '',
    doi TEXT DEFAULT '',
    content_type TEXT DEFAULT 'Текст',
    access_method TEXT DEFAULT 'непосредственный',
    
    -- File paths
    qr_code_path TEXT DEFAULT '',
    cover_image_path TEXT DEFAULT ''
);

-- Indexes for efficient querying
-- Index on author for author-based searches
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);

-- Index on title for title-based searches
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);

-- Index on ISBN for unique identification and lookups
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);

-- Composite index for common search patterns (author + year)
CREATE INDEX IF NOT EXISTS idx_books_author_year ON books(author, year);

-- Composite index for place + publisher searches
CREATE INDEX IF NOT EXISTS idx_books_place_publisher ON books(place, publisher);

-- Full-text search index for title and abstract
CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
    title,
    subtitle,
    abstract,
    content='books',
    content_rowid='id'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
    INSERT INTO books_fts(rowid, title, subtitle, abstract)
    VALUES (new.id, new.title, new.subtitle, new.abstract);
END;

CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
    INSERT INTO books_fts(books_fts, rowid, title, subtitle, abstract)
    VALUES('delete', old.id, old.title, old.subtitle, old.abstract);
END;

CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
    INSERT INTO books_fts(books_fts, rowid, title, subtitle, abstract)
    VALUES('delete', old.id, old.title, old.subtitle, old.abstract);
    INSERT INTO books_fts(rowid, title, subtitle, abstract)
    VALUES (new.id, new.title, new.subtitle, new.abstract);
END;

-- View for simplified book listing
CREATE VIEW IF NOT EXISTS v_books_summary AS
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
CREATE VIEW IF NOT EXISTS v_books_full AS
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
