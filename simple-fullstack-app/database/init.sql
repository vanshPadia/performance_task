-- Create database if it doesn't exist (fallback safety)
CREATE DATABASE IF NOT EXISTS testdb;
USE testdb;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);

-- 2. Books Catalog Table
CREATE TABLE IF NOT EXISTS books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  author VARCHAR(100) NOT NULL,
  available INT DEFAULT 1
);

-- 3. Borrow Track Join Table
CREATE TABLE IF NOT EXISTS borrowed_books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  book_id INT,
  returned INT DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 4. Seed books data only if the catalog is empty
INSERT INTO books (title, author, available) 
SELECT * FROM (
    SELECT 'The Hobbit', 'J.R.R. Tolkien', 3 UNION ALL
    SELECT '1984', 'George Orwell', 2 UNION ALL
    SELECT 'The Great Gatsby', 'F. Scott Fitzgerald', 1
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM books) LIMIT 3;