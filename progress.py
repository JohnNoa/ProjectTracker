# main_app.py (PyQt5 Version)

import sys
import os
import io
import functools # Keep this import

# --- PyQt5 Imports ---
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QRadioButton, QFrame, QScrollArea, QDialog,
    QFileDialog, QMessageBox, QSizePolicy, QSpacerItem, QMenu, QProgressBar,
    QListWidget, QListWidgetItem, QCheckBox, QDialogButtonBox, QGridLayout,
    QGroupBox, QAction
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings

# Import the managers
from database_manager import DatabaseManager
from theme_manager import ThemeManager, LIGHT_STYLE, DARK_STYLE

# --- Custom Widget for Task Row ---
class TaskItemWidget(QWidget):
    # Signal to request deletion, passing the item widget itself
    delete_requested = pyqtSignal(QListWidgetItem)

    def __init__(self, task_id, description, completed, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        print(f"    DEBUG [TaskItemWidget.__init__]: Initializing with task_id={self.task_id} (Type: {type(self.task_id)})")
        self.list_widget_item = None # Will be set when added to QListWidget

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2) # Minimal margins

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(completed)
        layout.addWidget(self.checkbox)

        self.lineedit = QLineEdit()
        self.lineedit.setText(description)
        self.lineedit.setPlaceholderText("Enter task description")
        layout.addWidget(self.lineedit, 1) # Stretch lineedit

        self.delete_button = QPushButton("X")
        self.delete_button.setFixedSize(25, 25)
        self.delete_button.setToolTip("Delete this task")
        # Connect directly to a method that emits the signal
        self.delete_button.clicked.connect(self.request_delete)
        layout.addWidget(self.delete_button)

    def request_delete(self):
        # Emit the signal carrying the associated QListWidgetItem
        if self.list_widget_item:
            self.delete_requested.emit(self.list_widget_item)

    def get_data(self):
        print(f"    DEBUG [TaskItemWidget.get_data]: Reading task_id={self.task_id} (Type: {type(self.task_id)})")
        return self.task_id, self.lineedit.text().strip(), self.checkbox.isChecked()

    def set_list_item(self, item):
        # Store the QListWidgetItem associated with this widget
        self.list_widget_item = item

    def get_task_id(self):
        return self.task_id

# --- Activity Creator Dialog (Remains the same) ---
# ... (Keep the existing ActivityCreatorDialog code) ...
class ActivityCreatorDialog(QDialog):
    # ... (no changes needed here) ...
     def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.image_path = None
        self.image_data = None # Store image data directly

        self.setWindowTitle("Create New Activity")
        self.setModal(True) # Make dialog modal
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Form Layout for better alignment
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Activity Name:"), 0, 0)
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Enter a unique activity name")
        form_layout.addWidget(self.name_entry, 0, 1)

        form_layout.addWidget(QLabel("Category:"), 1, 0)
        self.category_entry = QLineEdit()
        self.category_entry.setPlaceholderText("(Optional) e.g., Work, Hobby, Learning")
        form_layout.addWidget(self.category_entry, 1, 1)

        # Changed alignment enum for PyQt5
        form_layout.addWidget(QLabel("Initial Tasks:"), 2, 0, alignment=Qt.AlignTop)
        self.tasks_text = QTextEdit()
        self.tasks_text.setPlaceholderText("Enter one task per line")
        self.tasks_text.setFixedHeight(100) # Set fixed height initially
        form_layout.addWidget(self.tasks_text, 2, 1)

        layout.addLayout(form_layout)

        # Image Upload Section
        image_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        self.image_label = QLabel("No image selected")
        self.image_label.setStyleSheet("font-style: italic; color: gray;")
        image_layout.addWidget(self.upload_button)
        image_layout.addWidget(self.image_label, 1) # Stretch label

        layout.addLayout(image_layout)
        # Changed SizePolicy enum for PyQt5
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Changed StandardButton enum access for PyQt5
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

     def upload_image(self):
        # File dialog now parented to this dialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_path:
            self.image_path = file_path
            try:
                # Read image data immediately
                with open(self.image_path, 'rb') as f:
                    self.image_data = f.read()
                # Optional: Validate image size/type here if needed
                self.image_label.setText(f"Image: {os.path.basename(self.image_path)}")
                self.image_label.setStyleSheet("") # Reset style
            except Exception as e:
                QMessageBox.warning(self, "Image Error", f"Could not read image file: {e}")
                self.image_path = None
                self.image_data = None
                self.image_label.setText("No image selected")
                self.image_label.setStyleSheet("font-style: italic; color: gray;")

     def get_data(self):
        name = self.name_entry.text().strip()
        category = self.category_entry.text().strip()
        # Split tasks, filter out empty lines
        tasks = [line.strip() for line in self.tasks_text.toPlainText().strip().split('\n') if line.strip()]
        return name, category, tasks, self.image_data

     def accept(self):
        name, category, tasks, image_data = self.get_data()

        if not name:
            QMessageBox.warning(self, "Input Error", "Activity name is required.")
            return # Keep dialog open
        if not tasks:
            pass # Allow creating activities with no initial tasks

        # Attempt to create activity in DB
        activity_id, error = self.db_manager.create_activity(name, category, tasks, image_data)

        if error:
            QMessageBox.critical(self, "Database Error", f"Failed to create activity:\n{error}")
            if "already exists" in error:
                self.name_entry.selectAll()
                self.name_entry.setFocus()
                return
            else:
                super().reject()
        else:
            QMessageBox.information(self, "Success", f"Activity '{name}' created successfully!")
            super().accept() # Close dialog


# --- Activity Editor Dialog (Refactored for QListWidget) ---
class ActivityEditorDialog(QDialog):
    activity_saved = pyqtSignal()

    def __init__(self, activity_id, db_manager, parent=None):
        super().__init__(parent)
        self.activity_id = activity_id
        self.db_manager = db_manager
        self.current_image_data = None
        self.new_image_data = None
        # Store task IDs to delete from DB, not UI items
        self.db_tasks_to_delete = []

        self.setWindowTitle("Edit Activity")
        self.setModal(True)
        self.setMinimumSize(450, 550)

        layout = QVBoxLayout(self)

        # Top section (Image, Name, Category - mostly unchanged)
        top_frame = QFrame()
        top_layout = QGridLayout(top_frame)
        layout.addWidget(top_frame)

        self.image_label = QLabel("Loading Image...")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(100, 100)
        self.image_label.setStyleSheet("border: 1px dashed gray;")
        top_layout.addWidget(self.image_label, 0, 0, 2, 1)

        self.change_image_button = QPushButton("Change Image")
        self.change_image_button.clicked.connect(self.change_image)
        top_layout.addWidget(self.change_image_button, 0, 1)
        self.remove_image_button = QPushButton("Remove Image")
        self.remove_image_button.clicked.connect(self.remove_image)
        top_layout.addWidget(self.remove_image_button, 1, 1, alignment=Qt.AlignTop)

        details_layout = QGridLayout()
        top_layout.addLayout(details_layout, 0, 2, 2, 1)
        top_layout.setColumnStretch(2, 1)
        details_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_entry = QLineEdit()
        details_layout.addWidget(self.name_entry, 0, 1)
        details_layout.addWidget(QLabel("Category:"), 1, 0)
        self.category_entry = QLineEdit()
        details_layout.addWidget(self.category_entry, 1, 1)

        # --- Tasks Section Refactored ---
        tasks_group = QGroupBox("Tasks")
        tasks_layout = QVBoxLayout(tasks_group)
        layout.addWidget(tasks_group, 1) # Allow group to stretch

        # Use QListWidget
        self.tasks_list_widget = QListWidget()
        tasks_layout.addWidget(self.tasks_list_widget)

        self.add_task_button = QPushButton("Add New Task")
        self.add_task_button.clicked.connect(self.add_task_item) # Connect to new method
        tasks_layout.addWidget(self.add_task_button)
        # --- End Tasks Section Refactor ---

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_changes)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.load_activity_data()

    def load_activity_data(self):
        activity_data = self.db_manager.get_activity(self.activity_id)
        if not activity_data:
            QMessageBox.critical(self, "Error", "Could not load activity data.")
            self.reject()
            return

        self.name_entry.setText(activity_data['name'])
        self.category_entry.setText(activity_data['category'] or "")
        self.current_image_data = activity_data['image']
        self.update_image_display(self.current_image_data)
        self.db_tasks_to_delete = [] # Reset delete list on load

        # Load tasks into QListWidget
        self.tasks_list_widget.clear() # Clear previous items
        tasks = self.db_manager.get_tasks(self.activity_id)
        print(f"DEBUG [load_activity_data]: Loading {len(tasks)} tasks from DB.")
        for task_id, description, completed in tasks:
             print(f"  Loading from DB: ID={task_id} (Type: {type(task_id)}), Desc='{description}', Comp={completed}")
             self.add_task_item(task_id, description, completed) # Use the add method

    def add_task_item(self, task_id=None, description="", completed=False):
        """Adds a custom TaskItemWidget to the QListWidget."""
        if isinstance(task_id, bool):
            print("WARNING: Received boolean for task_id, forcing to None.")
            task_id = None
        print(f"DEBUG [add_task_item]: STARTING for task_id={task_id} (Type: {type(task_id)})")
        item_widget = TaskItemWidget(task_id, description, completed)
        print(f"  DEBUG [add_task_item]: item_widget created. Internal task_id={item_widget.get_task_id()} (Type: {type(item_widget.get_task_id())})")
        list_item = QListWidgetItem(self.tasks_list_widget) # Create QListWidgetItem

        # Store the QListWidgetItem within the custom widget for reference
        item_widget.set_list_item(list_item)

        # Set the size hint for the QListWidgetItem based on the custom widget's size
        list_item.setSizeHint(item_widget.sizeHint())

        print(f"  DEBUG [add_task_item]: BEFORE setItemWidget. Internal task_id={item_widget.get_task_id()} (Type: {type(item_widget.get_task_id())})")

        # Set the custom widget as the widget for this list item
        self.tasks_list_widget.addItem(list_item)
        self.tasks_list_widget.setItemWidget(list_item, item_widget)

        print(f"  DEBUG [add_task_item]: AFTER setItemWidget. Internal task_id={item_widget.get_task_id()} (Type: {type(item_widget.get_task_id())})")

        # Connect the custom widget's delete signal to our handler
        item_widget.delete_requested.connect(self.handle_task_delete_request)
        print(f"  DEBUG [add_task_item]: AFTER signal connect. Internal task_id={item_widget.get_task_id()} (Type: {type(item_widget.get_task_id())})")
        print(f"DEBUG [add_task_item]: Finished adding item for task_id={task_id}.")

    def handle_task_delete_request(self, list_item):
        """Handles the delete request signal from a TaskItemWidget."""
        # Get the custom widget associated with the list item
        item_widget = self.tasks_list_widget.itemWidget(list_item)
        if not item_widget: return

        task_id_to_delete = item_widget.get_task_id()
        print(f"DEBUG [handle_task_delete_request]: Request to delete Task ID: {task_id_to_delete}")

        # Find the row index of the item to remove it from the QListWidget
        row = self.tasks_list_widget.row(list_item)
        if row >= 0:
            # Remove the item from the QListWidget - this also deletes the item_widget
            self.tasks_list_widget.takeItem(row)
            print(f"  Removed item from QListWidget for Task ID {task_id_to_delete}.")

            # If it was an existing task (not None ID), add it to the DB delete list
            if task_id_to_delete is not None:
                if task_id_to_delete not in self.db_tasks_to_delete:
                    self.db_tasks_to_delete.append(task_id_to_delete)
                    print(f"  Added Task ID {task_id_to_delete} to DB delete list.")
                else:
                    print(f"  Task ID {task_id_to_delete} was already marked for deletion.")


    # update_image_display, change_image, remove_image remain the same
    def update_image_display(self, image_data):
         self.image_label.setStyleSheet("border: 1px dashed gray;") # Reset border
         if image_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Changed AspectRatioMode and TransformationMode enums for PyQt5
                scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Invalid Image")
         else:
             self.image_label.setText("No Image")
             self.image_label.setObjectName("NoImageLabel")
             style = QApplication.instance().styleSheet()
             self.image_label.setStyleSheet(style)

    def change_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    new_data = f.read()
                test_pixmap = QPixmap()
                if not test_pixmap.loadFromData(new_data):
                    raise ValueError("Invalid image format or corrupted file.")
                self.new_image_data = new_data
                self.update_image_display(self.new_image_data)
                print("New image selected and loaded.")
            except Exception as e:
                QMessageBox.warning(self, "Image Error", f"Could not load image: {e}")
                self.new_image_data = None
                self.update_image_display(self.current_image_data)

    def remove_image(self):
        if self.current_image_data or self.new_image_data:
            # Changed StandardButton enum access for PyQt5
            if QMessageBox.question(self, "Confirm Removal", "Remove image from this activity?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                self.new_image_data = b"" # Use empty bytes to signify removal
                self.update_image_display(None)
                print("Image marked for removal.")
        else:
             QMessageBox.information(self, "No Image", "There is no image to remove.")


    def save_changes(self):
        name = self.name_entry.text().strip()
        category = self.category_entry.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Activity name is required.")
            return

        final_image_data = self.new_image_data if self.new_image_data is not None else self.current_image_data

        error = self.db_manager.update_activity(self.activity_id, name, category, final_image_data)
        if error:
            QMessageBox.critical(self, "Database Error", f"Failed to update activity details:\n{error}")
            if "already exists" in error:
                 self.name_entry.selectAll()
                 self.name_entry.setFocus()
                 return
            return

        # Process tasks currently visible in the QListWidget
        save_errors = []
        print("-" * 20)
        print(f"Saving tasks for activity ID: {self.activity_id}")
        print(f"Tasks marked for deletion: {self.db_tasks_to_delete}")
        print(f"Number of items in QListWidget: {self.tasks_list_widget.count()}")

        for i in range(self.tasks_list_widget.count()):
            list_item = self.tasks_list_widget.item(i)
            item_widget = self.tasks_list_widget.itemWidget(list_item)
            if item_widget:
                task_id, description, completed = item_widget.get_data()
                print(f"  Processing UI Row {i}: ID={task_id}, Desc='{description}', Comp={completed}")

                if task_id is None: # New task added via button
                    if description:
                        print(f"    Attempting to ADD task: '{description}'")
                        new_task_id, task_error = self.db_manager.add_task(self.activity_id, description)
                        # ---> Print the RETURNED values <---
                        print(f"    Returned from db_manager.add_task: new_task_id={new_task_id}, task_error={task_error}")
                        if task_error:
                             print(f"      ADD FAILED: {task_error}")
                             save_errors.append(f"Add task '{description[:20]}...': {task_error}")
                        else:
                             print(f"      ADD SUCCEEDED! New ID: {new_task_id}")
                             # Update the widget's internal ID now that it's saved
                             item_widget.task_id = new_task_id
                    else:
                         print("    New task description is empty, skipping add.")
                elif description: # Existing task, update it
                    print(f"    Attempting to UPDATE task ID {task_id}")
                    task_error = self.db_manager.update_task(task_id, description, completed)
                    if task_error:
                         print(f"      UPDATE FAILED: {task_error}")
                         save_errors.append(f"Update task ID {task_id}: {task_error}")
                    else:
                         print(f"      UPDATE SUCCEEDED!")
                else: # Existing task with empty description - treat as delete
                    print(f"    Existing task ID {task_id} has empty description, adding to delete list.")
                    if task_id not in self.db_tasks_to_delete:
                        self.db_tasks_to_delete.append(task_id)
            else:
                 print(f"  Warning: Could not get item widget for row {i}")
        print("-" * 10)

        # Process actual DB deletions
        print(f"Processing final DB deletions list: {self.db_tasks_to_delete}")
        for task_id_to_delete in self.db_tasks_to_delete:
            print(f"  Attempting to DELETE task ID: {task_id_to_delete} from DB")
            task_error = self.db_manager.delete_task(task_id_to_delete)
            if task_error:
                 print(f"    DELETE FAILED: {task_error}")
                 save_errors.append(f"Delete task ID {task_id_to_delete}: {task_error}")
            else:
                 print(f"    DELETE SUCCEEDED!")
        print("=" * 20)

        if save_errors:
             error_message = "Activity details saved, but some task operations failed:\n\n" + "\n".join(save_errors)
             QMessageBox.warning(self, "Partial Success", error_message)
        else:
             QMessageBox.information(self, "Success", "Changes saved successfully!")

        self.activity_saved.emit()
        self.accept()

# --- Activity Display Widget (Remains mostly the same) ---
# ... (Keep the existing ActivityDisplayWidget code, it doesn't need QListWidget) ...
class ActivityDisplayWidget(QWidget):
    # ... (no changes needed here from the previous PyQt5 version) ...
    activity_selected = pyqtSignal(int)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._view_mode = "tiles"
        self._sort_by = "name"
        self._search_term = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        self.update_display()

    def set_view_mode(self, mode):
        if mode in ["list", "tiles", "icons"]:
            self._view_mode = mode
            self.update_display()

    def set_sort_by(self, sort_key):
         if sort_key in ["name", "category", "completion"]:
            self._sort_by = sort_key
            self.update_display()

    def set_search_term(self, term):
        self._search_term = term
        self.update_display()

    def update_display(self):
        activities = self.db_manager.get_activities(self._search_term, self._sort_by)
        # Create a new container widget each time
        new_content_widget = QWidget()
        layout = None

        if self._view_mode == "list":
            layout = QVBoxLayout(new_content_widget)
            layout.setAlignment(Qt.AlignTop)
            for activity in activities:
                item_widget = self._create_list_item(activity)
                layout.addWidget(item_widget)
            layout.addStretch(1) # Add stretch at the end for list view
        elif self._view_mode == "tiles" or self._view_mode == "icons":
            layout = QGridLayout(new_content_widget)
            layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            cols = max(1, self.parent().width() // 180 if self.parent() else 4) # Use parent width or default
            for idx, activity in enumerate(activities):
                item_widget = self._create_tile_item(activity, icon_only=(self._view_mode == "icons"))
                row = idx // cols
                col = idx % cols
                layout.addWidget(item_widget, row, col, alignment=Qt.AlignTop | Qt.AlignLeft)
            # Add stretch to prevent clumping
            layout.setRowStretch(layout.rowCount(), 1)
            layout.setColumnStretch(layout.columnCount(), 1)

        # Keep existing content widget until new one is ready
        old_widget = self.scroll_area.takeWidget()
        if old_widget:
            old_widget.deleteLater() # Delete the old one safely

        self.content_widget = new_content_widget # Assign new one
        self.scroll_area.setWidget(self.content_widget)

    # _create_base_frame, _add_double_click_to_children, _handle_double_click
    # _create_list_item, _create_tile_item, _show_context_menu, _delete_activity
    # should remain largely the same as in the previous PyQt5 version.
    # Make sure _show_context_menu uses self.sender().mapToGlobal(position)
    def _create_base_frame(self, activity_id):
        frame = QFrame()
        # Changed Shape and Shadow enums for PyQt5
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setLineWidth(1)
        # Changed ContextMenuPolicy enum for PyQt5
        frame.setContextMenuPolicy(Qt.CustomContextMenu)
        frame.customContextMenuRequested.connect(lambda pos, aid=activity_id: self._show_context_menu(pos, aid))
        frame.mouseDoubleClickEvent = lambda event, aid=activity_id: self._handle_double_click(aid)
        return frame

    def _add_double_click_to_children(self, parent_widget, activity_id):
         for child in parent_widget.findChildren(QWidget):
              child.mouseDoubleClickEvent = lambda event, aid=activity_id: self._handle_double_click(aid)

    def _handle_double_click(self, activity_id):
         print(f"Double-click detected for activity ID: {activity_id}")
         self.activity_selected.emit(activity_id)

    def _create_list_item(self, activity_row):
        activity_id = activity_row['id']
        frame = self._create_base_frame(activity_id)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        img_label = QLabel()
        img_label.setFixedSize(50, 50)
        # Changed alignment enum for PyQt5
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: 1px dashed lightgray;")
        if activity_row['image']:
            pixmap = QPixmap()
            if pixmap.loadFromData(activity_row['image']):
                 # Changed AspectRatioMode and TransformationMode enums for PyQt5
                 scaled_pixmap = pixmap.scaled(img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                 img_label.setPixmap(scaled_pixmap)
            else:
                 img_label.setText("?")
        else:
            img_label.setText("N/A")
        layout.addWidget(img_label)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(5,0,0,0)
        details_layout.addWidget(QLabel(f"<b>{activity_row['name']}</b>"))
        details_layout.addWidget(QLabel(f"<i>{activity_row['category'] or 'No Category'}</i>"))
        layout.addWidget(details_widget, 1)

        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        completion_percent = self.db_manager.get_activity_completion(activity_id)
        progress_bar.setValue(int(completion_percent))
        progress_bar.setFormat(f"{completion_percent:.0f}%")
        progress_bar.setToolTip(f"{completion_percent:.1f}% complete")
        progress_bar.setFixedWidth(100)
        layout.addWidget(progress_bar)

        self._add_double_click_to_children(frame, activity_id)
        return frame

    def _create_tile_item(self, activity_row, icon_only=False):
        activity_id = activity_row['id']
        frame = self._create_base_frame(activity_id)
        frame.setMinimumSize(150, 150)
        frame.setMaximumWidth(170)
        layout = QVBoxLayout(frame)
        # Changed alignment enum flags for PyQt5
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        img_label = QLabel()
        img_label.setFixedSize(100, 100)
        # Changed alignment enum for PyQt5
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: 1px dashed lightgray;")
        if activity_row['image']:
            pixmap = QPixmap()
            if pixmap.loadFromData(activity_row['image']):
                 # Changed AspectRatioMode and TransformationMode enums for PyQt5
                 scaled_pixmap = pixmap.scaled(img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                 img_label.setPixmap(scaled_pixmap)
            else:
                 img_label.setText("Invalid Image")
        else:
             img_label.setText("No Image")
        # Changed alignment enum for PyQt5
        layout.addWidget(img_label, 0, Qt.AlignHCenter)


        if not icon_only:
            name_label = QLabel(f"<b>{activity_row['name']}</b>")
            # Changed alignment enum for PyQt5
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            layout.addWidget(name_label)

            cat_label = QLabel(f"<i>{activity_row['category'] or 'No Category'}</i>")
            # Changed alignment enum for PyQt5
            cat_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(cat_label)

            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            completion_percent = self.db_manager.get_activity_completion(activity_id)
            progress_bar.setValue(int(completion_percent))
            progress_bar.setFormat(f"{completion_percent:.0f}%")
            progress_bar.setToolTip(f"{completion_percent:.1f}% complete")
            progress_bar.setFixedHeight(15)
            layout.addWidget(progress_bar)
            layout.addStretch(1)

        self._add_double_click_to_children(frame, activity_id)
        return frame

    def _show_context_menu(self, position, activity_id):
        menu = QMenu(self) # Parent the menu to self
        # Use QAction for menu items (better practice)
        open_action = QAction("Open / Edit", self)
        open_action.triggered.connect(lambda checked=False, aid=activity_id: self.activity_selected.emit(aid))
        menu.addAction(open_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda checked=False, aid=activity_id: self._delete_activity(aid))
        menu.addAction(delete_action)

        # Use widget's mapToGlobal for correct menu position
        widget = self.sender() # Get the widget that emitted the signal (the frame)
        global_pos = widget.mapToGlobal(position) if widget else self.mapToGlobal(position) # Fallback
        menu.exec_(global_pos) # Use exec_ for PyQt5

    def _delete_activity(self, activity_id):
        activity_data = self.db_manager.get_activity(activity_id)
        activity_name = activity_data['name'] if activity_data else f"ID {activity_id}"

        # Changed StandardButton enum access for PyQt5
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to delete the activity:\n'{activity_name}'?\n\nThis will also delete all associated tasks.",
                                     QMessageBox.Yes | QMessageBox.Cancel,
                                     QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            error = self.db_manager.delete_activity(activity_id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete activity:\n{error}")
            else:
                self.update_display()


# --- Main Application Window (Remains mostly the same) ---
# ... (Keep the existing ProjectTrackerApp code, __init__, setup_control_bar, etc.) ...
class ProjectTrackerApp(QMainWindow):
    # ... (Keep __init__, set_window_icon, setup_control_bar, open_activity_creator,
    #      open_activity_editor, handle_activity_saved, toggle_theme,
    #      update_theme_action_text, closeEvent, restore_geometry methods) ...
     def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Tracker")
        self.setGeometry(100, 100, 1000, 700)

        self.db_manager = DatabaseManager()
        if self.db_manager.conn is None:
            QMessageBox.critical(self, "Fatal Error", "Could not connect to the database.\nThe application will now close.")
            sys.exit(1)

        self.theme_manager = ThemeManager()
        self.set_window_icon()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create Display FIRST
        self.activity_display = ActivityDisplayWidget(self.db_manager)
        self.activity_display.activity_selected.connect(self.open_activity_editor)

        # Setup Control Bar SECOND
        control_frame = self.setup_control_bar()
        self.main_layout.addWidget(control_frame) # Add controls

        # Add Display AFTER controls
        self.main_layout.addWidget(self.activity_display, 1) # Add display area, allow stretch

        self.statusBar().showMessage("Ready")
        self.theme_manager.apply_theme(QApplication.instance())
        self.update_theme_action_text()

     def set_window_icon(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_path, 'res', 'img', 'ProgressTracker.ico')
        print(f"Attempting to load icon from: {icon_path}")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print("Icon loaded successfully.")
        else:
             print("Warning: Icon file not found.")

     def setup_control_bar(self): # Modify to return frame
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 5, 0, 5)

        # Use QIcon.fromTheme for potentially better cross-platform icons if available
        # Provide fallback path if theme icons aren't found
        add_icon_path = os.path.join(os.path.dirname(__file__), 'res', 'img', 'add_icon.png') # Example path
        add_icon = QIcon.fromTheme("list-add", QIcon(add_icon_path) if os.path.exists(add_icon_path) else QIcon())
        self.create_button = QPushButton(add_icon, " Create Activity")
        self.create_button.setToolTip("Add a new activity to track")
        self.create_button.clicked.connect(self.open_activity_creator)
        control_layout.addWidget(self.create_button)

        # Changed SizePolicy enum for PyQt5
        control_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        view_group = QGroupBox("View")
        view_layout = QHBoxLayout(view_group)
        self.view_list_rb = QRadioButton("List")
        self.view_tiles_rb = QRadioButton("Tiles")
        self.view_icons_rb = QRadioButton("Icons")
        view_layout.addWidget(self.view_list_rb)
        view_layout.addWidget(self.view_tiles_rb)
        view_layout.addWidget(self.view_icons_rb)
        self.view_tiles_rb.setChecked(True)
        # Use clicked for RadioButtons often works better than toggled with groups
        self.view_list_rb.clicked.connect(lambda: self.activity_display.set_view_mode("list"))
        self.view_tiles_rb.clicked.connect(lambda: self.activity_display.set_view_mode("tiles"))
        self.view_icons_rb.clicked.connect(lambda: self.activity_display.set_view_mode("icons"))
        control_layout.addWidget(view_group)

        sort_group = QGroupBox("Sort By")
        sort_layout = QHBoxLayout(sort_group)
        self.sort_name_rb = QRadioButton("Name")
        self.sort_category_rb = QRadioButton("Category")
        self.sort_completion_rb = QRadioButton("Completion")
        sort_layout.addWidget(self.sort_name_rb)
        sort_layout.addWidget(self.sort_category_rb)
        sort_layout.addWidget(self.sort_completion_rb)
        self.sort_name_rb.setChecked(True)
        self.sort_name_rb.clicked.connect(lambda: self.activity_display.set_sort_by("name"))
        self.sort_category_rb.clicked.connect(lambda: self.activity_display.set_sort_by("category"))
        self.sort_completion_rb.clicked.connect(lambda: self.activity_display.set_sort_by("completion"))
        control_layout.addWidget(sort_group)

        control_layout.addStretch(1)

        search_label = QLabel("Search:")
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Filter by name or category...")
        self.search_entry.setClearButtonEnabled(True)
        self.search_entry.textChanged.connect(self.activity_display.set_search_term)
        control_layout.addWidget(search_label)
        control_layout.addWidget(self.search_entry)

        self.theme_button = QPushButton()
        self.theme_button.setCheckable(False)
        self.theme_button.setToolTip("Toggle Light/Dark Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.theme_button)
        self.update_theme_action_text() # Call here to set initial state

        return control_frame # Return the frame

     def open_activity_creator(self):
        dialog = ActivityCreatorDialog(self.db_manager, self)
        # Use exec_() for PyQt5
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("New activity created.", 3000)
            self.activity_display.update_display()

     def open_activity_editor(self, activity_id):
        dialog = ActivityEditorDialog(activity_id, self.db_manager, self)
        dialog.activity_saved.connect(self.handle_activity_saved)
        # Use exec_() for PyQt5
        dialog.exec_()

     def handle_activity_saved(self):
        self.statusBar().showMessage("Activity updated.", 3000)
        self.activity_display.update_display()

     def toggle_theme(self):
        self.theme_manager.toggle_theme(QApplication.instance())
        self.update_theme_action_text()
        self.activity_display.update_display()

     def update_theme_action_text(self):
        theme = self.theme_manager.get_current_theme()
        # Example fallback paths (replace with actual paths or remove if not needed)
        moon_icon_path = os.path.join(os.path.dirname(__file__), 'res', 'img', 'moon.png')
        sun_icon_path = os.path.join(os.path.dirname(__file__), 'res', 'img', 'sun.png')

        if theme == "dark":
            # Use fallback icon path for PyQt5 if theme icon isn't reliable
            icon = QIcon(moon_icon_path) if os.path.exists(moon_icon_path) else QIcon.fromTheme("weather-clear-night")
            self.theme_button.setIcon(icon)
            self.theme_button.setText(" Light Mode")
            self.theme_button.setToolTip("Switch to Light Mode")
        else:
            icon = QIcon(sun_icon_path) if os.path.exists(sun_icon_path) else QIcon.fromTheme("weather-clear")
            self.theme_button.setIcon(icon)
            self.theme_button.setText(" Dark Mode")
            self.theme_button.setToolTip("Switch to Dark Mode")

     def closeEvent(self, event):
        print("Closing application...")
        self.db_manager.close()
        settings = QSettings("JohnNoah", "ProjectTracker")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

     def restore_geometry(self):
         settings = QSettings("JohnNoah", "ProjectTracker")
         geometry = settings.value("geometry")
         if geometry:
             self.restoreGeometry(geometry)
         state = settings.value("windowState")
         if state:
              self.restoreState(state)

# --- Entry Point (Remains the same) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("ProjectTracker")
    QApplication.setOrganizationName("JohnNoah")

    window = ProjectTrackerApp()
    window.restore_geometry()
    window.show()
    sys.exit(app.exec_()) # Use exec_() for PyQt5