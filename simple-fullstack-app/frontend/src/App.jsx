import { useState, useEffect } from 'react';

export default function App() {
    const [user, setUser] = useState(null);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [books, setBooks] = useState([]);
    const [borrowed, setBorrowed] = useState([]);
    const [error, setError] = useState('');

    const API_URL = 'http://0.0.0.0:5000/api';

    useEffect(() => {
        if (user) {
            fetchLibraryData();
        }
    }, [user]);

    const fetchLibraryData = async () => {
        try {
            const booksRes = await fetch(`${API_URL}/books`);
            const booksData = await booksRes.json();
            setBooks(booksData);

            const borrowRes = await fetch(`${API_URL}/borrowed/${user.id}`);
            const borrowData = await borrowRes.json();
            setBorrowed(borrowData);
        } catch (err) {
            console.error('Failed to reload data inventory');
        }
    };

    const handleAuth = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok) setUser(data);
            else setError(data.error || 'Authentication failed');
        } catch {
            setError('Cannot connect to backend server');
        }
    };

    const borrowBook = async (bookId) => {
        await fetch(`${API_URL}/books/borrow`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: user.id, bookId })
        });
        fetchLibraryData();
    };

    const returnBook = async (borrowId, bookId) => {
        await fetch(`${API_URL}/books/return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ borrowId, bookId })
        });
        fetchLibraryData();
    };

    const handleLogout = () => {
        setUser(null);
        setUsername('');
        setPassword('');
        setBorrowed([]);
    };

    if (!user) {
        return (
            <div style={{ maxWidth: '400px', margin: '100px auto', fontFamily: 'sans-serif', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
                <h2>📚 Library Login / Signup</h2>
                <p style={{ fontSize: '12px', color: '#666' }}>Tip: Enter any new name to automatically register an account!</p>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <form onSubmit={handleAuth}>
                    <input style={{ width: '90%', padding: '10px', margin: '10px 0' }} type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
                    <input style={{ width: '90%', padding: '10px', margin: '10px 0' }} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
                    <button style={{ width: '95%', padding: '10px', background: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }} type="submit">Enter Dashboard</button>
                </form>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: '900px', margin: '30px auto', fontFamily: 'sans-serif', padding: '20px' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #eee', paddingBottom: '10px' }}>
                <h2>📖 Welcome, {user.username}!</h2>
                <button onClick={handleLogout} style={{ padding: '8px 15px', background: '#dc3545', color: '#white', border: 'none', borderRadius: '4px', cursor: 'pointer', color: 'white' }}>Log Out</button>
            </header>

            <main style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginTop: '20px' }}>
                {/* Left Side: Available Catalog */}
                <div>
                    <h3>Available Books Catalog</h3>
                    {books.map(book => (
                        <div key={book.id} style={{ padding: '15px', border: '1px solid #eee', marginBottom: '10px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong>{book.title}</strong>
                                <div style={{ fontSize: '13px', color: '#555' }}>by {book.author}</div>
                                <small style={{ color: book.available > 0 ? 'green' : 'red' }}>Copies: {book.available}</small>
                            </div>
                            <button
                                onClick={() => borrowBook(book.id)}
                                disabled={book.available <= 0}
                                style={{ padding: '6px 12px', background: book.available > 0 ? '#007bff' : '#ccc', color: '#fff', border: 'none', borderRadius: '4px', cursor: book.available > 0 ? 'pointer' : 'not-allowed' }}>
                                Issue Book
                            </button>
                        </div>
                    ))}
                </div>

                {/* Right Side: User's Borrowed Items */}
                <div>
                    <h3>Your Issued Books</h3>
                    {borrowed.length === 0 ? (
                        <p style={{ color: '#888' }}>You haven't issued any books yet.</p>
                    ) : (
                        borrowed.map(item => (
                            <div key={item.borrow_id} style={{ padding: '15px', border: '1px solid #d4edda', background: '#f8fff9', marginBottom: '10px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <strong>{item.title}</strong>
                                    <div style={{ fontSize: '13px', color: '#555' }}>{item.author}</div>
                                </div>
                                <button
                                    onClick={() => returnBook(item.borrow_id, item.book_id)}
                                    style={{ padding: '6px 12px', background: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                    Return Book
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </main>
        </div>
    );
}