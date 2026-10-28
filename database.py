import sqlite3
import random

conn = sqlite3.connect('bank_ao.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    uid INTEGER PRIMARY KEY,
    full_name TEXT,
    stk_ao TEXT UNIQUE,
    balance INTEGER DEFAULT 0,
    INTEGER bank_acc TEXT,
    bank_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT,
_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS history (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    amount INTEGER,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

conn.commit()

def generate_stk_ao():
    while True:
        stk = '9704' + ''.join([str(random.randint(0, 9)) for _ in range(10)])
        c.execute("SELECT stk_ao FROM users WHERE stk_ao=?", (stk,))
        if not c.fetchone():
            return stk

if __name__ == "__main__":
    print("Database da tao xong: bank_ao.db")