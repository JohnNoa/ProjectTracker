# activity_display.py

import tkinter as tk
from tkinter import ttk, Menu, messagebox
from PIL import Image, ImageTk
import io

class ActivityDisplay:
    def __init__(self, parent, db_manager, open_activity_callback):
        self.parent = parent
        self.db_manager = db_manager
        self.open_activity_callback = open_activity_callback

        self.view_var = tk.StringVar(value="list")
        self.sort_var = tk.StringVar(value="name")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_display())

        self.setup_display_area()

    def setup_display_area(self):
        self.activity_frame = ttk.Frame(self.parent)
        self.activity_frame.pack(fill=tk.BOTH, expand=True)

        self.activity_canvas = tk.Canvas(self.activity_frame)
        self.activity_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.activity_frame, orient=tk.VERTICAL, command=self.activity_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.activity_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.activity_canvas.bind('<Configure>', lambda e: self.activity_canvas.configure(scrollregion=self.activity_canvas.bbox("all")))

        self.inner_frame = ttk.Frame(self.activity_canvas)
        self.activity_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.update_display()

    def show_context_menu(self, event, activity_id):
        context_menu = Menu(self.parent, tearoff=0)
        context_menu.add_command(label="Edit", command=lambda: self.open_activity_callback(activity_id))
        context_menu.add_command(label="Delete", command=lambda: self.delete_activity(activity_id))
        context_menu.tk_popup(event.x_root, event.y_root)

    def delete_activity(self, activity_id):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this activity?"):
            self.db_manager.delete_activity(activity_id)
            self.update_display()

    def update_display(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        activities = self.db_manager.get_activities(self.search_var.get(), self.sort_var.get())
        for idx, (id, name, category, image_data, created_at, modified_at) in enumerate(activities):
            frame = ttk.Frame(self.inner_frame)
            frame.grid(row=idx // 3, column=idx % 3, padx=10, pady=10, sticky="nsew")
            
            if self.view_var.get() in ["tiles", "icons"] and image_data:
                img = Image.open(io.BytesIO(image_data))
                img = img.resize((100, 100), Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(frame, image=photo)
                label.image = photo  # Keep a reference to prevent garbage collection
                label.pack()
            elif self.view_var.get() in ["tiles", "icons"]:
                label = ttk.Label(frame, text="No Image")
                label.pack()
            
            if self.view_var.get() != "icons":
                ttk.Label(frame, text=name, font=("", 12, "bold")).pack()
                ttk.Label(frame, text="Category: {}".format(category)).pack()
                completion = self.db_manager.get_activity_completion(id)
                ttk.Label(frame, text="Completion: {:.0%}".format(completion)).pack()
                ttk.Label(frame, text="Created: {}".format(created_at)).pack()
                ttk.Label(frame, text="Modified: {}".format(modified_at)).pack()

            # Bind the double-click event and right-click event
            frame.bind("<Double-1>", lambda e, aid=id: self.open_activity_callback(aid))
            frame.bind("<Button-3>", lambda e, aid=id: self.show_context_menu(e, aid))
            for widget in frame.winfo_children():
                widget.bind("<Double-1>", lambda e, aid=id: self.open_activity_callback(aid))
                widget.bind("<Button-3>", lambda e, aid=id: self.show_context_menu(e, aid))

        # Update the canvas scroll region
        self.activity_canvas.update_idletasks()
        self.activity_canvas.configure(scrollregion=self.activity_canvas.bbox("all"))

    def show_context_menu(self, event, activity_id):
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.add_command(label="Open", command=lambda: self.open_activity_callback(activity_id))
        context_menu.add_command(label="Delete", command=lambda: self.delete_activity(activity_id))
        context_menu.tk_popup(event.x_root, event.y_root)

    def delete_activity(self, activity_id):
        if tk.messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this activity?"):
            self.db_manager.delete_activity(activity_id)
            self.update_display()

    def open_activity_callback(self, activity_id):
        print("ActivityDisplay: Callback triggered for activity {}".format(activity_id))
        self.open_activity_callback(activity_id)