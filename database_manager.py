# database_manager.py

import sqlite3
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_name="activities.db"):
        # Get the absolute path of the directory containing this script
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the database file in the project directory
        self.db_path = os.path.join(self.base_dir, db_name)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            image BLOB,
            created_at DATE,
            modified_at DATE
        )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                activity_id INTEGER,
                description TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (activity_id) REFERENCES activities (id)
            )
        ''')
        self.conn.commit()

    def create_activity(self, name, category, tasks, image_data=None):
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%d-%m-%Y")
        cursor.execute("INSERT INTO activities (name, category, image, created_at, modified_at) VALUES (?, ?, ?, ?, ?)",
                       (name, category, image_data, now, now))
        activity_id = cursor.lastrowid
        for task in tasks:
            if task.strip():  # Ignore empty tasks
                cursor.execute("INSERT INTO tasks (activity_id, description) VALUES (?, ?)",
                               (activity_id, task.strip()))
        self.conn.commit()
        return activity_id
    
    def update_activity(self, activity_id, name, category, image_data):
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%d-%m-%Y")
        if image_data is not None:
            cursor.execute("UPDATE activities SET name = ?, category = ?, image = ?, modified_at = ? WHERE id = ?",
                           (name, category, image_data, now, activity_id))
        else:
            cursor.execute("UPDATE activities SET name = ?, category = ?, modified_at = ? WHERE id = ?",
                           (name, category, now, activity_id))
        self.conn.commit()

    def get_activities(self, search_term="", sort_by="name"):
        cursor = self.conn.cursor()
        search_term = "%{}%".format(search_term)
        if sort_by == "name":
            query = """
            SELECT id, name, category, image, created_at, modified_at FROM activities
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY name
            """
        elif sort_by == "category":
            query = """
            SELECT id, name, category, image, created_at, modified_at FROM activities
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY category, name
            """
        else:  # completion
            query = """
            SELECT a.id, a.name, a.category, a.image, a.created_at, a.modified_at,
                CAST(SUM(CASE WHEN t.completed THEN 1 ELSE 0 END) AS FLOAT) / COUNT(t.id) AS completion_ratio
            FROM activities a
            LEFT JOIN tasks t ON a.id = t.activity_id
            WHERE a.name LIKE ? OR a.category LIKE ?
            GROUP BY a.id
            ORDER BY completion_ratio DESC, a.name
            """
        cursor.execute(query, (search_term, search_term))
        return cursor.fetchall()

    def get_activity(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, category, image FROM activities WHERE id = ?", (activity_id,))
        return cursor.fetchone()

    def get_tasks(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, description, completed FROM tasks WHERE activity_id = ?", (activity_id,))
        return cursor.fetchall()

    def update_task(self, task_id, description, completed):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET description = ?, completed = ? WHERE id = ?",
                    (description, completed, task_id))
        self.conn.commit()

    def add_task(self, activity_id, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (activity_id, description, completed) VALUES (?, ?, ?)",
                       (activity_id, description, False))
        self.conn.commit()
        return cursor.lastrowid

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def delete_activity(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE activity_id = ?", (activity_id,))
        cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        self.conn.commit()

    def get_activity_completion(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT CAST(SUM(CASE WHEN completed THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)
            FROM tasks
            WHERE activity_id = ?
        """, (activity_id,))
        return cursor.fetchone()[0] or 0

    def close(self):
        self.conn.close()