import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ui.main_window import MainWindow, QApplication
from src.core.config import ConfigManager
from PyQt6.QtWidgets import QFileDialog, QMessageBox


def main():
    app = QApplication(sys.argv)

    # Global Dark Theme Styling
    app.setStyleSheet(
        """
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', Roboto, sans-serif;
        }
        QLineEdit {
            background-color: #2b2b2b;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px;
            color: white;
            selection-background-color: #007acc;
        }
        QListWidget {
            background-color: #1e1e1e;
            border: none;
        }
        /* Scrollbar */
        QScrollBar:vertical {
            border: none;
            background: #2b2b2b;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """
    )

    # Storage Configuration Check
    config_manager = ConfigManager()
    storage_path = config_manager.get_storage_path()

    if not storage_path or not os.path.exists(storage_path):
        # Prompt user
        msg = QMessageBox()
        msg.setWindowTitle("Welcome to QEdit Toolkit")
        msg.setText("Please select a folder to store your assets (Storage Directory).")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

        storage_path = QFileDialog.getExistingDirectory(None, "Select Storage Folder")
        
        if not storage_path:
            # User canceled
            sys.exit(0)
            
        config_manager.set_storage_path(storage_path)

    window = MainWindow(storage_path=storage_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
