import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ui.main_window import MainWindow, QApplication


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

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
