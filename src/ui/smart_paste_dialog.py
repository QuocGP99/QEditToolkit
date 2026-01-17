from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                             QDialogButtonBox, QHBoxLayout, QMessageBox, QWidget, QApplication)
from PyQt6.QtGui import QPixmap, QIcon, QDrag
from PyQt6.QtCore import Qt, QSize, QMimeData, QUrl, pyqtSignal
import os

class DraggableLabel(QLabel):
    drag_started = pyqtSignal()
    drag_finished = pyqtSignal()

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        self.drag_started.emit()
        
        drag = QDrag(self)
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(os.path.abspath(self.file_path))
        mime_data.setUrls([url])
        drag.setMimeData(mime_data)
        
        # Determine drag action
        # In this specific case, we don't care much about the action result 
        # because the external app (Resolve) handles the drop.
        # But we emit 'drag_finished' so the dialog knows to close.
        drop_action = drag.exec(Qt.DropAction.CopyAction)
        
        self.drag_finished.emit()

class SmartPasteDialog(QDialog):
    """
    Dialog shown when user presses Ctrl+V.
    Allows user to select a target Bin in DaVinci Resolve.
    """
    def __init__(self, image_path, resolve_api, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.resolve_api = resolve_api
        self.selected_bin = None
        
        self.setWindowTitle("Smart Paste to Resolve 🎬")
        self.setMinimumWidth(400)
        
        self._init_ui()
        self._load_bins()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Image Preview
        # 1. Image Preview (Draggable)
        self.preview_label = DraggableLabel(self.image_path)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #2b2b2b; border-radius: 8px;")
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setToolTip("💡 Drag this image to DaVinci Resolve Timeline")
        
        # Connect drag signals
        self.preview_label.drag_finished.connect(self.accept) # Close dialog on drag finish
        
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            # Scale to fit while keeping aspect ratio
            scaled_pixmap = pixmap.scaled(380, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        else:
            self.preview_label.setText("Image not found")
        
        layout.addWidget(self.preview_label)

        # 2. Bin Selection
        bin_layout = QHBoxLayout()
        bin_label = QLabel("Sync Project Bin (Optional):")
        self.bin_combo = QComboBox()
        self.bin_combo.setEditable(True)  # Allow manual entry
        self.bin_combo.setPlaceholderText("Select Bin or Type New Name...")
        
        bin_layout.addWidget(bin_label)
        bin_layout.addWidget(self.bin_combo)
        layout.addLayout(bin_layout)

        # 3. Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Style OK button to look "Primary"
        ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("Cancel / Done")
        ok_btn.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 5px 15px;")
        
        layout.addWidget(button_box)

    def _load_bins(self):
        """Loads bins from Resolve API."""
        if not self.resolve_api or not self.resolve_api.is_connected():
            self.bin_combo.addItem("⚠️ Resolve not connected", None)
            self.bin_combo.setEnabled(False)
            return

        try:
            bins = self.resolve_api.get_all_bins()
            if not bins:
                self.bin_combo.addItem("Root (Master)", self.resolve_api.get_root_folder())
            else:
                for b in bins:
                    self.bin_combo.addItem(f"📁 {b['path']}", b['obj'])
        except Exception as e:
            self.bin_combo.addItem(f"Error: {str(e)}", None)

    def get_selected_bin(self):
        """Returns the selected bin object."""
        return self.bin_combo.currentData()
