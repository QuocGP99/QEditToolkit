import sqlite3
import os

class DBManager:
    def __init__(self, db_path="app_data.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_db()

    def connect(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def init_db(self):
        self.connect()
        # Create Assets Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT,
                category_name TEXT,
                preview_path TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_favorite INTEGER DEFAULT 0
            )
        ''')
        # Create Categories Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        # Create Tags Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT
            )
        ''')
        # Create AssetTags Association
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_tags (
                asset_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(asset_id) REFERENCES assets(id),
                FOREIGN KEY(tag_id) REFERENCES tags(id),
                PRIMARY KEY (asset_id, tag_id)
            )
        ''')
        # Create AssetCategories Association (or just a column in assets, keeping it simple)
        # For this version, let's add category_id to assets
        try:
            self.cursor.execute('ALTER TABLE assets ADD COLUMN category_id INTEGER REFERENCES categories(id)')
        except sqlite3.OperationalError:
            pass # Column likely exists
        
        # Migration: Add category_name if missing
        try:
            self.cursor.execute('ALTER TABLE assets ADD COLUMN category_name TEXT')
        except sqlite3.OperationalError:
            pass # Column likely exists
            
        # Migration: Add is_favorite if missing
        try:
            self.cursor.execute('ALTER TABLE assets ADD COLUMN is_favorite INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass # Column likely exists

        self.conn.commit()

    def get_favorite_assets(self):
        self.cursor.execute('SELECT * FROM assets WHERE is_favorite = 1 ORDER BY date_added DESC')
        return [dict(row) for row in self.cursor.fetchall()]

    def add_asset(self, file_path, file_name, file_type, category_id=None, preview_path=None, category_name=None):
        try:
            self.cursor.execute('''
                INSERT INTO assets (file_path, file_name, file_type, category_id, preview_path, category_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_path, file_name, file_type, category_id, preview_path, category_name))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None # Already exists

    def get_all_assets(self):
        self.cursor.execute('SELECT * FROM assets ORDER BY date_added DESC')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def search_assets(self, query):
        self.cursor.execute('SELECT * FROM assets WHERE file_name LIKE ?', (f'%{query}%',))
        return [dict(row) for row in self.cursor.fetchall()]

    def toggle_favorite(self, asset_id):
        self.cursor.execute('UPDATE assets SET is_favorite = NOT is_favorite WHERE id = ?', (asset_id,))
        self.conn.commit()

    def update_asset_preview(self, asset_id, preview_path):
        self.cursor.execute('UPDATE assets SET preview_path = ? WHERE id = ?', (preview_path, asset_id))
        self.conn.commit()

    def delete_asset(self, asset_id):
        self.cursor.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        self.conn.commit()

    def get_all_categories(self):
        """Returns distinct category names."""
        self.cursor.execute('SELECT DISTINCT category_name FROM assets WHERE category_name IS NOT NULL ORDER BY category_name')
        return [row['category_name'] for row in self.cursor.fetchall()]

    def get_assets_by_category(self, category_name):
        """Returns assets filtered by category."""
        self.cursor.execute('SELECT * FROM assets WHERE category_name = ? ORDER BY file_name', (category_name,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_category_counts(self):
        """Returns a dictionary of category_name: count."""
        self.cursor.execute('SELECT category_name, COUNT(*) as count FROM assets WHERE category_name IS NOT NULL GROUP BY category_name')
        return {row['category_name']: row['count'] for row in self.cursor.fetchall()}

    def get_asset_by_id(self, asset_id):
        """Returns single asset by ID."""
        self.cursor.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
