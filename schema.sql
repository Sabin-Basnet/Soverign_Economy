CREATE TABLE IF NOT EXISTS users (
user_id TEXT PRIMARY KEY,
username TEXT NOT NULL,
balance REAL NOT NULL CHECK(balance >= 0)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(user_id),
    FOREIGN KEY(receiver_id) REFERENCES users(user_id)
);