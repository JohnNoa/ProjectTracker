# database_manager.py

import sqlite3
from datetime import datetime
import os
import sys

class DatabaseManager:
    def __init__(self, db_name="activities.db"):
        # Get the absolute path of the directory containing this script (or the executable)
        if getattr(sys, 'frozen', False):
            # If running as a PyInstaller bundle
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # If running as a normal script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the Databases directory path
        self.db_folder = os.path.join(self.base_dir, "Databases")

        # Create the Databases directory if it doesn't exist
        os.makedirs(self.db_folder, exist_ok=True)

        # Construct the full path to the database file
        self.db_path = os.path.join(self.db_folder, db_name)

        print(f"Database Path: {self.db_path}") # For debugging

        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Access columns by name
            self.create_tables()
            print("Database connection successful.") # For debugging
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            # Optionally, raise the error or handle it to show a message to the user
            # For now, we'll let it potentially fail later if conn is None
            self.conn = None # Indicate connection failure

    def create_tables(self):
        if not self.conn: return # Don't proceed if connection failed
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE, -- Added UNIQUE constraint
                category TEXT,
                image BLOB,
                created_at TEXT, -- Storing as TEXT ISO format is often better
                modified_at TEXT
            )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_id INTEGER,
                    description TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0, -- 0 for False, 1 for True
                    FOREIGN KEY (activity_id) REFERENCES activities (id) ON DELETE CASCADE -- Ensure tasks deleted when activity is
                )
            ''')
            self.conn.commit()
            print("Tables checked/created.") # For debugging
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def create_activity(self, name, category, tasks, image_data=None):
        if not self.conn: return None, "Database connection error"
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute("INSERT INTO activities (name, category, image, created_at, modified_at) VALUES (?, ?, ?, ?, ?)",
                           (name, category, image_data, now, now))
            activity_id = cursor.lastrowid
            for task_desc in tasks:
                if task_desc.strip(): # Ignore empty tasks
                    cursor.execute("INSERT INTO tasks (activity_id, description, completed) VALUES (?, ?, ?)",
                                   (activity_id, task_desc.strip(), 0)) # Start as not completed
            self.conn.commit()
            print(f"Activity '{name}' created with ID: {activity_id}") # For debugging
            return activity_id, None # Success
        except sqlite3.IntegrityError:
             return None, f"Activity with name '{name}' already exists."
        except sqlite3.Error as e:
            self.conn.rollback() # Rollback on error
            print(f"Error creating activity: {e}")
            return None, f"Database error: {e}"

    def update_activity(self, activity_id, name, category, image_data):
        if not self.conn: return "Database connection error"
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        try:
            # Check if image_data needs update. If None is passed explicitly,
            # it means "don't change image". If an empty bytes object or similar
            # is passed, it might mean "remove image" - handle as needed.
            # Let's assume None means "keep current image".
            if image_data is not None: # If new image data is provided (even if it's empty bytes for removal)
                 cursor.execute("UPDATE activities SET name = ?, category = ?, image = ?, modified_at = ? WHERE id = ?",
                           (name, category, image_data, now, activity_id))
            else: # Keep the existing image
                cursor.execute("UPDATE activities SET name = ?, category = ?, modified_at = ? WHERE id = ?",
                           (name, category, now, activity_id))

            self.conn.commit()
            print(f"Activity ID {activity_id} updated.") # For debugging
            return None # Success
        except sqlite3.IntegrityError:
             return f"Activity with name '{name}' already exists."
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error updating activity {activity_id}: {e}")
            return f"Database error: {e}"

    def add_task(self, activity_id, description):
        print(f"DEBUG [db_manager.add_task]: ENTERED. activity_id={activity_id}, description='{description}'")
        if not self.conn: 
            print("DEBUG [db_manager.add_task]: EXITING early - no DB connection.") # Add print
            return None, "Database connection error"
        
        cursor = self.conn.cursor()
        try:
            print(f"  DB: Executing INSERT task for activity_id={activity_id}, description='{description.strip()}'")
            cursor.execute("INSERT INTO tasks (activity_id, description, completed) VALUES (?, ?, ?)",
                           (activity_id, description.strip(), 0))
            task_id = cursor.lastrowid
            print(f"  DB: INSERT executed. Last Row ID: {task_id}") # Add print immediately after execute

            print("  DB: Attempting commit...") # Add print before commit
            self.conn.commit()
            print(f"  DB: COMMIT successful. Task ID {task_id} should be saved.") # Confirm commit
            return task_id, None # Success
        except sqlite3.Error as e:
            # ---> Print the EXCEPTION <---
            print(f"!!!! DB ERROR [db_manager.add_task]: Exception occurred: {e} !!!!")
            self.conn.rollback() # Rollback on error
            print(f"  DB: Rolled back transaction due to error.")
            return None, f"Database error: {e}"
        finally:
             # ---> Print on exit, regardless of success/failure <---
             print(f"DEBUG [db_manager.add_task]: EXITING.")

    def update_task(self, task_id, description, completed):
        if not self.conn: return "Database connection error"
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE tasks SET description = ?, completed = ? WHERE id = ?",
                        (description.strip(), 1 if completed else 0, task_id))
            self.conn.commit()
            print(f"Task ID {task_id} updated.") # For debugging
            return None # Success
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error updating task {task_id}: {e}")
            return f"Database error: {e}"

    def delete_task(self, task_id):
        if not self.conn: return "Database connection error"
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            print(f"Task ID {task_id} deleted.") # For debugging
            return None # Success
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error deleting task {task_id}: {e}")
            return f"Database error: {e}"

    def get_activities(self, search_term="", sort_by="name"):
        if not self.conn: return []
        cursor = self.conn.cursor()
        # Using '%' for LIKE requires concatenation or specific param style in some DB APIs
        # Using f-strings here for simplicity, but parameter binding is safer
        search_query = f"%{search_term}%"

        base_query = "SELECT a.id, a.name, a.category, a.image, a.created_at, a.modified_at FROM activities a "
        where_clause = "WHERE a.name LIKE ? OR a.category LIKE ? "
        params = [search_query, search_query]

        # Subquery to calculate completion ratio safely handling division by zero
        completion_subquery = """
            (SELECT CAST(SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(t.id)
             FROM tasks t
             WHERE t.activity_id = a.id)
        """

        if sort_by == "name":
            order_by = "ORDER BY LOWER(a.name)"
        elif sort_by == "category":
            order_by = "ORDER BY LOWER(a.category), LOWER(a.name)"
        elif sort_by == 'completion':
             # Recalculate base query to include completion for sorting
             base_query = f"SELECT a.id, a.name, a.category, a.image, a.created_at, a.modified_at, COALESCE({completion_subquery}, 0) as completion_percent FROM activities a "
             order_by = "ORDER BY completion_percent DESC, LOWER(a.name)"
        else:
            order_by = "ORDER BY LOWER(a.name)" # Default sort

        full_query = base_query + where_clause + order_by

        try:
            cursor.execute(full_query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting activities: {e}")
            return []

    def get_activity(self, activity_id):
        if not self.conn: return None
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, name, category, image FROM activities WHERE id = ?", (activity_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting activity {activity_id}: {e}")
            return None

    def get_tasks(self, activity_id):
        if not self.conn: return []
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, description, completed FROM tasks WHERE activity_id = ? ORDER BY id", (activity_id,))
            # Return rows where completed is treated as boolean
            return [(row['id'], row['description'], bool(row['completed'])) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting tasks for activity {activity_id}: {e}")
            return []

    def delete_activity(self, activity_id):
        if not self.conn: return "Database connection error"
        cursor = self.conn.cursor()
        try:
            # Using CASCADE delete now, so only need to delete from activities
            cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
            self.conn.commit()
            print(f"Activity ID {activity_id} and its tasks deleted.") # For debugging
            return None # Success
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error deleting activity {activity_id}: {e}")
            return f"Database error: {e}"

    def get_activity_completion(self, activity_id):
        if not self.conn: return 0.0
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(CASE WHEN completed = 1 THEN 1 END) AS completed_count, COUNT(*) AS total_count
                FROM tasks
                WHERE activity_id = ?
            """, (activity_id,))
            result = cursor.fetchone()
            if result and result['total_count'] > 0:
                return (float(result['completed_count']) / result['total_count']) * 100.0
            else:
                return 0.0 # No tasks or failed query
        except sqlite3.Error as e:
            print(f"Error getting completion for activity {activity_id}: {e}")
            return 0.0

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.") # For debugging