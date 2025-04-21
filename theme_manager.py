# theme_manager.py

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

# Basic Stylesheets (can be expanded significantly)
LIGHT_STYLE = """
    /* Default Light Theme - can be customized */
    QWidget {
        background-color: #f0f0f0;
        color: #000000;
    }
    QPushButton, QComboBox, QLineEdit, QTextEdit, QListView, QTableWidget, QListWidget, QCheckBox, QRadioButton, QGroupBox {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        padding: 5px;
    }
    QPushButton {
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
    }
    QMenuBar, QMenu {
        background-color: #e8e8e8;
        color: #000000;
    }
    QMenuBar::item:selected, QMenu::item:selected {
        background-color: #d0d0d0;
    }
    QScrollArea {
         background-color: #ffffff;
         border: 1px solid #cccccc;
    }
    QScrollBar:vertical {
        border: 1px solid #cccccc;
        background: #f0f0f0;
        width: 15px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #c0c0c0;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
    }
    QProgressBar {
        border: 1px solid #cccccc;
        text-align: center;
        color: black; /* Ensure text is visible */
        background-color: #ffffff;
    }
    QProgressBar::chunk {
        background-color: #4CAF50; /* Green progress */
    }

"""

DARK_STYLE = """
    QWidget {
        background-color: #2e2e2e;
        color: #ffffff;
    }
    QPushButton, QComboBox, QLineEdit, QTextEdit, QListView, QTableWidget, QListWidget, QCheckBox, QRadioButton, QGroupBox {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        color: #ffffff;
        padding: 5px;
    }
    QPushButton {
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:disabled {
        background-color: #303030;
        color: #777777;
        border: 1px solid #444444;
    }
    QLineEdit:disabled, QTextEdit:disabled {
         background-color: #303030;
         color: #777777;
    }
    QMenuBar, QMenu {
        background-color: #3c3c3c;
        color: #ffffff;
        border-bottom: 1px solid #555555;
    }
    QMenuBar::item:selected, QMenu::item:selected {
        background-color: #4a4a4a;
    }
    QScrollArea {
         background-color: #3c3c3c;
         border: 1px solid #555555;
    }
    QScrollBar:vertical {
        border: 1px solid #555555;
        background: #2e2e2e;
        width: 15px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #505050;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
    }
    QProgressBar {
        border: 1px solid #555555;
        text-align: center;
        color: white; /* Ensure text is visible */
        background-color: #3c3c3c;
    }
    QProgressBar::chunk {
        background-color: #5cb85c; /* Brighter Green progress */
    }
    QToolTip { /* Style tooltips */
        background-color: #4a4a4a;
        color: #ffffff;
        border: 1px solid #555555;
    }
    QDialog { /* Ensure dialogs also get themed */
        background-color: #2e2e2e;
    }
    QLabel#NoImageLabel { /* Style the specific "No Image" label */
        color: #aaaaaa;
        font-style: italic;
    }
"""

class ThemeManager:
    def __init__(self):
        self.settings = QSettings("YourOrgName", "ActivityTracker") # Use QSettings to save theme
        self.current_theme = self.settings.value("theme", "light", type=str)

    def apply_theme(self, app: QApplication):
        if self.current_theme == "dark":
            app.setStyleSheet(DARK_STYLE)
        else:
            app.setStyleSheet(LIGHT_STYLE)

    def toggle_theme(self, app: QApplication):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.settings.setValue("theme", self.current_theme)
        self.apply_theme(app)
        return self.current_theme

    def get_current_theme(self):
        return self.current_theme