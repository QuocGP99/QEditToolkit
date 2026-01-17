import os
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QFileDialog,
    QDialog,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal

# ============================================================================
# PROJECT TEMPLATES CONFIGURATION
# ============================================================================

PROJECT_TEMPLATES = {
    "Vlog": {
        "prefix": "VLOG",
        "icon": "🎬",
        "description": "For YouTube Videos",
        "structure": [
            "00_ProjectFiles",
            "01_Footage/Cam_A",
            "01_Footage/Cam_B",
            "02_Audio/Music",
            "05_Exports/Final",
        ],
    },
    "Shorts/Reels": {
        "prefix": "REEL",
        "icon": "📱",
        "description": "For TikTok & Instagram",
        "structure": [
            "00_ProjectFiles",
            "01_Raw_Footage",
            "02_Audio/SFX",
            "04_Exports/TikTok",
        ],
    },
    "Wedding": {
        "prefix": "WED",
        "icon": "💍",
        "description": "For Wedding Videos",
        "structure": [
            "00_ProjectFiles",
            "01_Footage/Ceremony",
            "01_Footage/Reception",
            "02_Audio/Vows",
            "05_Exports/Highlight",
        ],
    },
    "Event": {
        "prefix": "EVENT",
        "icon": "🎉",
        "description": "For Event Coverage",
        "structure": ["00_ProjectFiles", "01_Footage/MasterCam", "05_Exports/FullShow"],
    },
}


# ============================================================================
# PROJECT GENERATOR DIALOG
# ============================================================================


class ProjectGeneratorDialog(QDialog):
    # Signal to notify when project is created
    project_created = pyqtSignal(str)  # Emit folder path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dynamic Project Generator")
        self.setGeometry(100, 100, 1000, 700)
        self.selected_template = None
        self.parent_directory = None
        self.selected_buttons = {}
        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===== SECTION 1: TEMPLATE SELECTION (Radio Buttons) =====
        template_label = QLabel("Select Project Template")
        template_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        template_label.setStyleSheet("color: #ffffff;")
        main_layout.addWidget(template_label)

        # Group box for radio buttons
        template_group = QGroupBox()
        template_group.setStyleSheet(
            """
            QGroupBox {
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """
        )
        template_layout = QVBoxLayout(template_group)
        template_layout.setSpacing(10)
        template_layout.setContentsMargins(0, 0, 0, 0)

        self.radio_group = QButtonGroup()
        self.radio_buttons = {}

        for idx, template_name in enumerate(PROJECT_TEMPLATES.keys()):
            radio_btn = QRadioButton()
            template = PROJECT_TEMPLATES[template_name]

            # Create description text
            description = (
                f"{template['icon']} {template_name} - {template['description']}"
            )
            radio_btn.setText(description)
            radio_btn.setStyleSheet(
                """
                QRadioButton {
                    color: #ffffff;
                    font-size: 11pt;
                    spacing: 8px;
                    padding: 8px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:unchecked {
                    background-color: #2d2d2d;
                    border: 2px solid #404040;
                    border-radius: 9px;
                }
                QRadioButton::indicator:checked {
                    background-color: #3b82f6;
                    border: 2px solid #3b82f6;
                    border-radius: 9px;
                }
                QRadioButton:hover {
                    background-color: #2a2a2a;
                    border-radius: 4px;
                }
            """
            )

            radio_btn.toggled.connect(
                lambda checked, name=template_name: (
                    self.select_template(name) if checked else None
                )
            )
            self.radio_group.addButton(radio_btn, idx)
            self.radio_buttons[template_name] = radio_btn
            template_layout.addWidget(radio_btn)

        main_layout.addWidget(template_group)

        # ===== SECTION 2: PROJECT NAME INPUT =====
        input_section = QVBoxLayout()
        input_section.setSpacing(10)

        name_label = QLabel("Project Name")
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        input_section.addWidget(name_label)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText(
            "Enter project name (e.g., Da Lat Trip)"
        )
        self.project_name_input.setStyleSheet(self.get_lineedit_style())
        self.project_name_input.setMinimumHeight(40)
        self.project_name_input.textChanged.connect(self.update_preview)
        input_section.addWidget(self.project_name_input)

        main_layout.addLayout(input_section)

        # ===== SECTION 3: DIRECTORY SELECTION =====
        dir_section = QHBoxLayout()
        dir_section.setSpacing(10)

        dir_label = QLabel("Parent Directory")
        dir_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        dir_label.setStyleSheet("color: #ffffff;")
        dir_section.addWidget(dir_label)

        self.directory_display = QLineEdit()
        self.directory_display.setReadOnly(True)
        self.directory_display.setPlaceholderText("No directory selected")
        self.directory_display.setStyleSheet(self.get_lineedit_style())
        self.directory_display.setMinimumHeight(40)
        dir_section.addWidget(self.directory_display)

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet(self.get_button_style())
        browse_btn.setMinimumHeight(40)
        browse_btn.setMinimumWidth(120)
        browse_btn.clicked.connect(self.browse_directory)
        dir_section.addWidget(browse_btn)

        main_layout.addLayout(dir_section)

        # ===== SECTION 4: LIVE PREVIEW =====
        preview_label = QLabel("Preview")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_label.setStyleSheet("color: #ffffff;")
        main_layout.addWidget(preview_label)

        self.preview_display = QLabel()
        self.preview_display.setStyleSheet(
            """
            QLabel {
                background-color: #2d2d2d;
                color: #3b82f6;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New';
                font-size: 12pt;
                font-weight: bold;
                border: 2px solid #3b82f6;
            }
        """
        )
        self.preview_display.setMinimumHeight(50)
        self.preview_display.setText("Select a template and enter project name")
        main_layout.addWidget(self.preview_display)

        # ===== SECTION 5: ACTION BUTTONS =====
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        create_btn = QPushButton("Create Project")
        create_btn.setStyleSheet(self.get_button_style())
        create_btn.setMinimumHeight(45)
        create_btn.setMinimumWidth(200)
        create_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        create_btn.clicked.connect(self.create_project)
        action_layout.addWidget(create_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet(self.get_button_style("#666666", "#555555"))
        reset_btn.setMinimumHeight(45)
        reset_btn.setMinimumWidth(100)
        reset_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        reset_btn.clicked.connect(self.reset_form)
        action_layout.addWidget(reset_btn)

        main_layout.addLayout(action_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

    def select_template(self, template_name):
        """Handle template selection"""
        self.selected_template = template_name
        self.update_preview()

    def browse_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Parent Directory", str(Path.home())
        )
        if directory:
            self.parent_directory = directory
            self.directory_display.setText(directory)
            self.update_preview()

    def update_preview(self):
        """Update the live preview of the project folder name"""
        if not self.selected_template:
            self.preview_display.setText("⚠️ Select a template first")
            return

        project_name = self.project_name_input.text().strip()
        if not project_name:
            self.preview_display.setText("⚠️ Enter a project name")
            return

        # Format: YYYYMMDD_PREFIX_ProjectName
        today = datetime.now().strftime("%Y%m%d")
        prefix = PROJECT_TEMPLATES[self.selected_template]["prefix"]

        # Replace spaces with underscores
        formatted_name = project_name.replace(" ", "_")

        final_folder_name = f"{today}_{prefix}_{formatted_name}"

        if self.parent_directory:
            full_path = os.path.join(self.parent_directory, final_folder_name)
            self.preview_display.setText(f"📁 {full_path}")
        else:
            self.preview_display.setText(f"📁 [Select Directory]/{final_folder_name}")

    def create_project(self):
        """Create the project folder structure"""
        # Validate inputs
        if not self.selected_template:
            QMessageBox.warning(self, "Error", "Please select a template first!")
            return

        project_name = self.project_name_input.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Error", "Please enter a project name!")
            return

        if not self.parent_directory:
            QMessageBox.warning(self, "Error", "Please select a parent directory!")
            return

        # Generate folder name
        today = datetime.now().strftime("%Y%m%d")
        prefix = PROJECT_TEMPLATES[self.selected_template]["prefix"]
        formatted_name = project_name.replace(" ", "_")
        final_folder_name = f"{today}_{prefix}_{formatted_name}"

        # Full path
        root_folder = os.path.join(self.parent_directory, final_folder_name)

        # Check if folder already exists
        if os.path.exists(root_folder):
            QMessageBox.warning(
                self, "Error", f"Project folder already exists:\n{root_folder}"
            )
            return

        try:
            # Create root folder
            os.makedirs(root_folder, exist_ok=True)

            # Create subfolders
            structure = PROJECT_TEMPLATES[self.selected_template]["structure"]
            for subfolder in structure:
                subfolder_path = os.path.join(root_folder, subfolder)
                os.makedirs(subfolder_path, exist_ok=True)

            # Create README.txt with timestamp
            readme_path = os.path.join(root_folder, "README.txt")
            with open(readme_path, "w") as f:
                f.write(f"Project: {final_folder_name}\n")
                f.write(f"Template: {self.selected_template}\n")
                f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write("Folder Structure:\n")
                for subfolder in structure:
                    f.write(f"  - {subfolder}\n")

            # Success message
            QMessageBox.information(
                self, "Success", f"Project created successfully!\n\n📁 {root_folder}"
            )

            # Emit signal for project creation handling
            self.project_created.emit(root_folder)

            # Reset form
            self.reset_form()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project:\n{str(e)}")

    def reset_form(self):
        """Reset all form inputs"""
        self.project_name_input.clear()
        self.directory_display.clear()
        self.selected_template = None
        self.parent_directory = None
        self.preview_display.setText("Select a template and enter project name")

        # Reset radio button selection
        if self.radio_group.checkedButton():
            self.radio_group.checkedButton().setChecked(False)

    # ===== STYLESHEET METHODS =====

    def apply_stylesheet(self):
        """Apply dark theme stylesheet"""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
            }
        """
        )

    def get_lineedit_style(self):
        """Get stylesheet for QLineEdit"""
        return """
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 8px;
                font-size: 11pt;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """

    def get_button_style(self, bg_color="#3b82f6", hover_color="#2563eb"):
        """Get stylesheet for QPushButton"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """
