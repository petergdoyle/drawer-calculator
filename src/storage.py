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
        
        # Create drawer_setups table
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
        
        # Check if slide_name column exists, if not add it (backward compatibility migration)
        cursor.execute("PRAGMA table_info(drawer_setups)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'slide_name' not in columns:
            cursor.execute("ALTER TABLE drawer_setups ADD COLUMN slide_name TEXT DEFAULT 'Blum Tandem (5/8\" Wood)'")

        # Create slides table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                width_tolerance REAL NOT NULL,
                height_tolerance REAL NOT NULL,
                min_depth_offset REAL NOT NULL,
                bottom_recess REAL NOT NULL,
                extension_below REAL NOT NULL,
                min_cab_width REAL NOT NULL,
                min_cab_height REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Prepopulate default slides if table is empty
        cursor.execute("SELECT COUNT(*) FROM slides")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO slides 
                (name, width_tolerance, height_tolerance, min_depth_offset, bottom_recess, extension_below, min_cab_width, min_cab_height)
                VALUES 
                ('Blum Tandem (5/8" Wood)', 0.375, 1.0, 0.125, 0.5, 0.21875, 6.0, 3.5),
                ('Blum Tandem (1/2" Wood)', 0.625, 1.0, 0.125, 0.5, 0.21875, 6.0, 3.5),
                ('Generic Undermount', 0.375, 1.0, 0.125, 0.5, 0.21875, 6.0, 3.5)
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
    slide_len: float,
    slide_name: str = 'Blum Tandem (5/8" Wood)'
) -> bool:
    """Save or overwrite a calculation setup in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO drawer_setups 
            (name, mode, cabinet_width, cabinet_height, drawer_width, drawer_height, slide_length, slide_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, 
            mode, 
            cabinet_w, 
            cabinet_h, 
            drawer_w, 
            drawer_h, 
            slide_len, 
            slide_name,
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

def list_slides() -> List[Dict[str, Any]]:
    """List all saved slide profiles, ordered by creation date descending."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM slides ORDER BY name ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Database list slides error: {e}")
        return []
    finally:
        conn.close()

def save_slide(
    name: str,
    width_tolerance: float,
    height_tolerance: float,
    min_depth_offset: float,
    bottom_recess: float,
    extension_below: float,
    min_cab_width: float,
    min_cab_height: float
) -> bool:
    """Save or update a slide profile in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO slides 
            (name, width_tolerance, height_tolerance, min_depth_offset, bottom_recess, extension_below, min_cab_width, min_cab_height)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            width_tolerance,
            height_tolerance,
            min_depth_offset,
            bottom_recess,
            extension_below,
            min_cab_width,
            min_cab_height
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database save slide error: {e}")
        return False
    finally:
        conn.close()

def delete_slide(slide_id: int) -> bool:
    """Delete a saved slide profile by its ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM slides WHERE id = ?", (slide_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database delete slide error: {e}")
        return False
    finally:
        conn.close()

def get_slide_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Retrieve slide profile details by name."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM slides WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database fetch slide by name error: {e}")
        return None
    finally:
        conn.close()
