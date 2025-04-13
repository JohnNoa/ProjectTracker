# activity_editor

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io


class ActivityEditor:
    def __init__(self, master, db_manager, update_callback):
        self.master = master
        self.db_manager = db_manager
        self.update_callback = update_callback
        self.new_image_data = None
        self.current_image_data = None

    def open_activity(self, activity_id):
        self.activity_id = activity_id
        self.dialog = tk.Toplevel(self.master)
        self.dialog.title("Edit Activity")
        self.dialog.geometry("400x500")
        self.dialog.transient(self.master)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        name, category, image_data = self.db_manager.get_activity(activity_id)
        self.current_image_data = image_data
        self.new_image_data = None

        # Image
        if image_data:
            img = Image.open(io.BytesIO(image_data))
            img = img.resize((100, 100), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            self.image_label = ttk.Label(main_frame, image=photo)
            self.image_label.image = photo
            self.image_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        else:
            self.image_label = ttk.Label(main_frame, text="No Image")
            self.image_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(main_frame, text="Change Image", command=self.change_image).grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Name and Category
        ttk.Label(main_frame, text="Activity Name:").grid(row=2, column=0, sticky="e", padx=(0, 5))
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.insert(0, name)
        self.name_entry.grid(row=2, column=1, sticky="w")

        ttk.Label(main_frame, text="Category:").grid(row=3, column=0, sticky="e", padx=(0, 5))
        self.category_entry = ttk.Entry(main_frame, width=30)
        self.category_entry.insert(0, category)
        self.category_entry.grid(row=3, column=1, sticky="w")

        # Tasks
        ttk.Label(main_frame, text="Tasks:").grid(row=4, column=0, columnspan=2, pady=(10, 5))
        
        self.tasks_frame = ttk.Frame(main_frame)
        self.tasks_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.canvas = tk.Canvas(self.tasks_frame)
        scrollbar = ttk.Scrollbar(self.tasks_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_tasks()

        ttk.Button(main_frame, text="Add Task", command=self.add_task).grid(row=6, column=0, pady=(10, 0))
        ttk.Button(main_frame, text="Save Changes", command=self.save_changes).grid(row=6, column=1, pady=(10, 0))

    def change_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            with open(file_path, 'rb') as file:
                self.new_image_data = file.read()
            img = Image.open(io.BytesIO(self.new_image_data))
            img = img.resize((100, 100), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.configure(image=photo)
            self.image_label.image = photo

    def save_changes(self):
        name = self.name_entry.get()
        category = self.category_entry.get()

        if not name:
            messagebox.showerror("Error", "Activity name is required.")
            return

        image_data = self.new_image_data if self.new_image_data is not None else self.current_image_data
        self.db_manager.update_activity(self.activity_id, name, category, image_data)

        for task_id, var, entry in self.task_widgets:
            description = entry.get().strip()
            if task_id is None and description:  # New task
                self.db_manager.add_task(self.activity_id, description)
            elif task_id is not None:
                if description:  # Update existing task
                    self.db_manager.update_task(task_id, description, var.get())
                else:  # Delete task if description is empty
                    self.db_manager.delete_task(task_id)

        messagebox.showinfo("Success", "Changes saved successfully!")
        self.dialog.destroy()
        self.update_callback()

    def load_tasks(self):
        tasks = self.db_manager.get_tasks(self.activity_id)
        self.task_widgets = []

        for task_id, description, completed in tasks:
            self.create_task_widgets(task_id, description, completed)

    def create_task_widgets(self, task_id, description, completed):
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill='x', padx=5, pady=2)

        var = tk.BooleanVar(value=completed)
        checkbutton = ttk.Checkbutton(frame, variable=var)
        checkbutton.pack(side=tk.LEFT)

        entry = ttk.Entry(frame, width=40)
        entry.insert(0, description)
        entry.pack(side=tk.LEFT, padx=5)

        delete_button = ttk.Button(frame, text="X", width=2, 
                                   command=lambda: self.delete_task(frame, task_id))
        delete_button.pack(side=tk.RIGHT)

        self.task_widgets.append((task_id, var, entry))

    def add_task(self):
        self.create_task_widgets(None, "", False)

    def delete_task(self, frame, task_id):
        frame.destroy()
        self.task_widgets = [w for w in self.task_widgets if w[0] != task_id]
        if task_id is not None:
            self.db_manager.delete_task(task_id)