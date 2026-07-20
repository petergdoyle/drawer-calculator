import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

# Homelab compliance: check for Docker volume directory first, fallback to local
DB_DIR = "/app/data" if os.path.exists("/app/data") else "./data"
DB_PATH = os.path.join(DB_DIR, "drawers.db")

def init_db() -> None:
    """Ensure data directory exists and initialize SQLite schema."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drawer_setups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                mode TEXT NOT NULL,
                cabinet_width REAL NOT NULL,
                cabinet_height REAL NOT NULL,
                drawer_width REAL NOT NULL,
                drawer_height REAL NOT NULL,
                slide_length REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

def save_setup(
    name: str, 
    mode: str, 
    cabinet_w: float, 
    cabinet_h: float, 
    drawer_w: float, 
    drawer_h: float, 
    slide_len: float
) -> bool:
    """Save or overwrite a calculation setup in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO drawer_setups 
            (name, mode, cabinet_width, cabinet_height, drawer_width, drawer_height, slide_length, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, 
            mode, 
            cabinet_w, 
            cabinet_h, 
            drawer_w, 
            drawer_h, 
            slide_len, 
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database save error: {e}")
        return False
    finally:
        conn.close()

def list_setups() -> List[Dict[str, Any]]:
    """List all saved setups, ordered by creation date descending."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drawer_setups ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Database list error: {e}")
        return []
    finally:
        conn.close()

def get_setup_by_id(setup_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve setup configuration by its primary key ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drawer_setups WHERE id = ?", (setup_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database fetch error: {e}")
        return None
    finally:
        conn.close()

def delete_setup(setup_id: int) -> bool:
    """Delete a saved setup by its ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM drawer_setups WHERE id = ?", (setup_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database delete error: {e}")
        return False
    finally:
        conn.close()
