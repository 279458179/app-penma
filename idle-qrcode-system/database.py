import sqlite3
import os

DB_PATH = "items.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            buy_date TEXT,
            owner TEXT,
            remark TEXT,
            photo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_item(item_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "name": row[1], "location": row[2],
            "buy_date": row[3], "owner": row[4], "remark": row[5], "photo": row[6]
        }
    else:
        return {"id": item_id, "name": "", "location": "", "buy_date": "", "owner": "", "remark": "", "photo": ""}

def save_item(data: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO items 
        (id, name, location, buy_date, owner, remark, photo) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data["id"], data["name"], data["location"], data["buy_date"],
          data["owner"], data["remark"], data.get("photo", "")))
    conn.commit()
    conn.close()