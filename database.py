import sqlite3

def init_db():
    conn = sqlite3.connect('hotel.db')
    c = conn.cursor()

    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  table_number INTEGER,
                  items TEXT,
                  total REAL,
                  status TEXT DEFAULT 'pending',
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()