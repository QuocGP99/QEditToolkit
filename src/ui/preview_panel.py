from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QStyle, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont
import os
import subprocess
import json

class PreviewPanel(QWidget):
    favorite_toggled = pyqtSignal(int) # Emits asset_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QWidget {
                background-color: #252525; 
                border-left: 1px solid #333;
                color: #ddd;
            }
            QLabel {
                border: none;
            }
        """)
        
        self.setup_ui()
        self.current_asset = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)
        
        # 1. Header: Filename + Favorite Star
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Star Button
        self.star_btn = QPushButton()
        self.star_btn.setFixedSize(32, 32)
        self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.star_btn.clicked.connect(self._on_star_clicked)
        self.star_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 24px;
                color: #444; 
            }
            QPushButton:hover {
                color: #FFD700;
            }
        """)
        
        # Filename Label
        self.name_label = QLabel("No Selection")
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        
        header_layout.addWidget(self.star_btn)
        header_layout.addWidget(self.name_label, 1) # Expand
        header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)

        # 2. Info Grid (Table-like look)
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(8)
        
        self.type_label = self._create_info_row("Type", "-")
        self.size_label = self._create_info_row("Size", "-")
        self.len_label = self._create_info_row("Duration", "-")
        self.date_label = self._create_info_row("Added", "-")
        
        layout.addLayout(self.info_layout)
        layout.addStretch()

    def _create_info_row(self, label, value):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #888; font-weight: bold; min-width: 60px;")
        
        val = QLabel(value)
        val.setStyleSheet("color: #ccc;")
        val.setWordWrap(True)
        
        row_layout.addWidget(lbl)
        row_layout.addWidget(val)
        
        self.info_layout.addWidget(row_widget)
        return val

    def update_preview(self, asset_data):
        self.current_asset = asset_data
        
        if not asset_data:
            self.name_label.setText("No Selection")
            self.type_label.setText("-")
            self.size_label.setText("-")
            self.date_label.setText("-")
            self._set_star_state(False)
            return

        file_path = asset_data.get('file_path')
        
        # 1. Name
        self.name_label.setText(asset_data.get('file_name', 'Unknown'))
        
        # 2. Favorite
        is_fav = bool(asset_data.get('is_favorite', 0))
        self._set_star_state(is_fav)

        # 3. Type
        self.type_label.setText(asset_data.get('file_type', 'Unknown').upper())

        # 4. Size & Details
        if file_path and os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            self.size_label.setText(f"{size_mb:.2f} MB")
        else:
            self.size_label.setText("File Missing")

        # 5. Length (Duration)
        if asset_data.get('file_type') in ['video', 'audio'] and file_path and os.path.exists(file_path):
            duration = self._get_duration(file_path)
            self.len_label.setText(duration)
        else:
            self.len_label.setText("-")

        # 6. Date
        date_str = asset_data.get('date_added', '')
        # SQLite often stores as string, simplistic display
        self.date_label.setText(str(date_str).split('.')[0]) 
    
    def _get_duration(self, file_path):
        """Get media duration using ffprobe."""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                file_path
            ]
            # On Windows, prevent cmd window from popping up
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode == 0:
                seconds = float(result.stdout.strip())
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                if h > 0:
                     return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                return f"{int(m):02d}:{int(s):02d}"
        except Exception:
            pass
        return "-" 

    def _set_star_state(self, is_favorite):
        if is_favorite:
            self.star_btn.setText("⭐") # Gold Star
            self.star_btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 24px; color: #FFD700; }
                QPushButton:hover { color: #ffe44d; }
            """)
        else:
            self.star_btn.setText("☆") # Empty Star
            self.star_btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 24px; color: #666; }
                QPushButton:hover { color: #FFD700; }
            """)

    def _on_star_clicked(self):
        if self.current_asset:
            asset_id = self.current_asset.get('id')
            if asset_id:
                self.favorite_toggled.emit(asset_id)
                # Toggle locally immediately for UI response, assuming DB success
                curr_state = (self.star_btn.text() == "⭐")
                self._set_star_state(not curr_state)
