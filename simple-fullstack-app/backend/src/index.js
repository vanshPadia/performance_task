const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

let db;

// Clean connection pool loop 
async function initDB() {
    try {
        db = await mysql.createConnection({
            host: process.env.DB_HOST || 'db',
            user: process.env.DB_USER || 'root',
            password: process.env.DB_PASSWORD || 'password',
            database: process.env.DB_NAME || 'testdb'
        });
        console.log('✅ Connected to MySQL Database smoothly.');
    } catch (err) {
        console.error('Database connection failed. Retrying in 3s...', err.message);
        setTimeout(initDB, 3000);
    }
}
initDB();

/* --- API ROUTES --- */

// 1. Auth: Login / Register Combo
app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        let [users] = await db.query('SELECT * FROM users WHERE username = ?', [username]);
        if (users.length === 0) {
            const [result] = await db.query('INSERT INTO users (username, password) VALUES (?, ?)', [username, password]);
            return res.json({ id: result.insertId, username });
        }
        if (users[0].password !== password) {
            return res.status(401).json({ error: 'Invalid password' });
        }
        res.json({ id: users[0].id, username: users[0].username });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 2. Get Book Catalog
app.get('/api/books', async (req, res) => {
    try {
        const [catalog] = await db.query('SELECT * FROM books');
        res.json(catalog);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 3. Get User Borrowed Books
app.get('/api/borrowed/:userId', async (req, res) => {
    try {
        const [borrowed] = await db.query(`
            SELECT bb.id as borrow_id, b.id as book_id, b.title, b.author 
            FROM borrowed_books bb 
            JOIN books b ON bb.book_id = b.id 
            WHERE bb.user_id = ? AND bb.returned = 0`, [req.params.userId]);
        res.json(borrowed);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 4. Issue Book
app.post('/api/books/borrow', async (req, res) => {
    const { userId, bookId } = req.body;
    try {
        const [book] = await db.query('SELECT available FROM books WHERE id = ?', [bookId]);
        if (book[0].available <= 0) return res.status(400).json({ error: 'No copies available' });

        await db.query('UPDATE books SET available = available - 1 WHERE id = ?', [bookId]);
        await db.query('INSERT INTO borrowed_books (user_id, book_id) VALUES (?, ?)', [userId, bookId]);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 5. Return Book
app.post('/api/books/return', async (req, res) => {
    const { borrowId, bookId } = req.body;
    try {
        await db.query('UPDATE books SET available = available + 1 WHERE id = ?', [bookId]);
        await db.query('UPDATE borrowed_books SET returned = 1 WHERE id = ?', [borrowId]);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => console.log(`🚀 API backend listening on port ${PORT}`));