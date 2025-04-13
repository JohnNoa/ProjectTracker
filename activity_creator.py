# activity_creator.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image

class ActivityCreator:
    def __init__(self, master, db_manager, update_callback):
        self.master = master
        self.db_manager = db_manager
        self.update_callback = update_callback
        self.image_path = None

    def open_dialog(self):
        self.dialog = tk.Toplevel(self.master)
        self.dialog.title("Create Activity")
        self.dialog.geometry("400x400")

        ttk.Label(self.dialog, text="Activity Name:").pack(pady=5)
        self.name_entry = ttk.Entry(self.dialog, width=40)
        self.name_entry.pack(pady=5)

        ttk.Label(self.dialog, text="Category:").pack(pady=5)
        self.category_entry = ttk.Entry(self.dialog, width=40)
        self.category_entry.pack(pady=5)

        ttk.Label(self.dialog, text="Tasks (one per line):").pack(pady=5)
        self.tasks_text = tk.Text(self.dialog, width=40, height=5)
        self.tasks_text.pack(pady=5)

        self.image_label = ttk.Label(self.dialog, text="No image selected")
        self.image_label.pack(pady=5)
        ttk.Button(self.dialog, text="Upload Image", command=self.upload_image).pack(pady=5)

        ttk.Button(self.dialog, text="Create", command=self.create_activity).pack(pady=10)

    def upload_image(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if self.image_path:
            self.image_label.config(text="Image: {}".format(os.path.basename(self.image_path)))

    def create_activity(self):
        name = self.name_entry.get()
        category = self.category_entry.get()
        tasks = self.tasks_text.get("1.0", tk.END).strip().split("\n")

        if not name or not tasks:
            messagebox.showerror("Error", "Activity name and at least one task are required.")
            return

        image_data = None
        if self.image_path:
            with open(self.image_path, 'rb') as file:
                image_data = file.read()

        try:
            self.db_manager.create_activity(name, category, tasks, image_data)
            messagebox.showinfo("Success", "Activity created successfully!")
            self.dialog.destroy()
            self.update_callback()
        except Exception as e:
            messagebox.showerror("Error", "Failed to create activity: {}".format(str(e)))
