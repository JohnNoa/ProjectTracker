# activity_tracker.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from PIL import Image, ImageTk
import io
import os
from database_manager import DatabaseManager
from activity_creator import ActivityCreator
from activity_display import ActivityDisplay
from activity_editor import ActivityEditor

class ActivityTracker:
    def __init__(self, master):
        self.master = master
        self.master.title("Project Tracker")
        self.master.geometry("1000x700")

        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set the icon for the main window
        icon_path = os.path.join(current_dir, 'res', 'img', 'ProgressTracker.ico')
        
        if os.path.exists(icon_path):
            icon = Image.open(icon_path)
            icon = ImageTk.PhotoImage(icon)
            self.master.iconphoto(True, icon)
        else:
            messagebox.showwarning("Warning", "Icon file not found at: {}".format(icon_path))
        
        # Set up database
        self.db_manager = DatabaseManager('activities.db')
        
        # Main frame
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Activity display area
        self.activity_display = ActivityDisplay(self.main_frame, self.db_manager, self.open_activity)
        
        # Initialize activity_creator and activity_editor
        self.activity_creator = ActivityCreator(self.master, self.db_manager, self.activity_display.update_display)
        self.activity_editor = ActivityEditor(self.master, self.db_manager, self.activity_display.update_display)
        
        # Top frame for buttons and options
        self.setup_top_frame()

    def setup_top_frame(self):
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=10)

        # Create activity button
        self.create_activity_button = ttk.Button(top_frame, text="Create Activity", command=self.activity_creator.open_dialog)
        self.create_activity_button.pack(side=tk.LEFT, padx=5)

        # View options
        self.setup_view_options(top_frame)

        # Sort options
        self.setup_sort_options(top_frame)

        # Search entry
        self.setup_search_entry(top_frame)

    def setup_view_options(self, parent):
        view_frame = ttk.Frame(parent)
        view_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(view_frame, text="View:").pack(side=tk.LEFT)
        for value in ["list", "tiles", "icons"]:
            ttk.Radiobutton(view_frame, text=value.capitalize(), variable=self.activity_display.view_var, 
                            value=value, command=self.activity_display.update_display).pack(side=tk.LEFT)

    def setup_sort_options(self, parent):
        sort_frame = ttk.Frame(parent)
        sort_frame.pack(side=tk.LEFT)
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT)
        for value in ["name", "category", "completion"]:
            ttk.Radiobutton(sort_frame, text=value.capitalize(), variable=self.activity_display.sort_var, 
                            value=value, command=self.activity_display.update_display).pack(side=tk.LEFT)

    def setup_search_entry(self, parent):
        search_frame = ttk.Frame(parent)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        ttk.Entry(search_frame, textvariable=self.activity_display.search_var, width=20).pack(side=tk.LEFT)

    def open_activity(self, activity_id):
        self.activity_editor.open_activity(activity_id)
        