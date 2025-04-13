# main.py

import os
import tkinter as tk
from activity_tracker import ActivityTracker

if __name__ == "__main__":
    root = tk.Tk()
    app = ActivityTracker(root)
    root.mainloop()