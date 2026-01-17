from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QHBoxLayout, QPushButton, QStyle
)
from PyQt6.QtGui import QPixmap, QIcon, QDrag
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QUrl
import os
import datetime

class ClipboardItemWidget(QWidget):
    """
    Custom widget for each clipboard history item.
    [ Thumbnail ] [ Info: Size, Time ] [ Delete Btn ]
    """
    delete_clicked = pyqtSignal(int) # Emits item_id

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.item_id = item_data['id']
        self.file_path = item_data['file_path']
        
        self.setFixedHeight(100)
        self.setStyleSheet("background-color: #2b2b2b; border-radius: 6px; margin: 2px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 80)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #1e1e1e; border: 1px solid #444;")
        
        if os.path.exists(self.file_path):
            pixmap = QPixmap(self.file_path)
            self.thumb_label.setPixmap(pixmap.scaled(
                120, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.thumb_label.setText("Missing")
        
        layout.addWidget(self.thumb_label)
        
        # 2. Info
        info_layout = QVBoxLayout()
        width = item_data.get('width', 0)
        height = item_data.get('height', 0)
        created_at = item_data.get('created_at', '')
        
        # Parse date nicely
        try:
             # Depending on SQLite format, might need parsing. 
             # SQLite default is YYYY-MM-DD HH:MM:SS
             dt = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
             created_str = dt.strftime("%H:%M %d/%m")
        except:
            created_str = created_at

        size_lbl = QLabel(f"📏 {width} x {height}")
        size_lbl.setStyleSheet("color: #ddd; font-weight: bold;")
        
        date_lbl = QLabel(f"🕒 {created_str}")
        date_lbl.setStyleSheet("color: #888; font-size: 11px;")
        
        info_layout.addWidget(size_lbl)
        info_layout.addWidget(date_lbl)
        info_layout.addStretch()
        
        layout.addLayout(info_layout, 1)
        
        # 3. Delete Button
        del_btn = QPushButton()
        del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        del_btn.setFixedSize(30, 30)
        del_btn.setToolTip("Delete this item")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #c42b1c;
                border-radius: 4px;
            }
        """)
        del_btn.clicked.connect(self._on_delete)
        layout.addWidget(del_btn)

    def _on_delete(self):
        self.delete_clicked.emit(self.item_id)


class ClipboardHistoryList(QListWidget):
    """
    Subclass to handle Drag and Drop from the list to Resolve.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                outline: none;
                border: none;
            }
            QListWidget::item {
                background-color: transparent;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: transparent; 
                border: 1px solid #007acc;
                border-radius: 8px;
            }
        """)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
            
        # Get stored file path
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(os.path.abspath(file_path))
        mime_data.setUrls([url])
        drag.setMimeData(mime_data)
        
        # Set drag pixmap
        widget = self.itemWidget(item)
        if widget:
            pixmap = widget.thumb_label.pixmap()
            if pixmap:
                drag.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        
        drag.exec(Qt.DropAction.CopyAction)


class ClipboardHistoryPanel(QWidget):
    def __init__(self, clipboard_manager, parent=None):
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("CLIPBOARD HISTORY")
        title.setStyleSheet("color: #ccc; font-weight: bold; margin: 10px;")
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("color: #ff6b6b; border: 1px solid #ff6b6b; padding: 4px 8px; border-radius: 4px;")
        clear_btn.clicked.connect(self.clear_all)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        header_layout.setContentsMargins(5,5,10,0)
        
        layout.addLayout(header_layout)
        
        # List
        self.list_widget = ClipboardHistoryList()
        layout.addWidget(self.list_widget)
        
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        if not self.clipboard_manager.db_manager:
            return

        items = self.clipboard_manager.db_manager.get_clipboard_history()
        for item_data in items:
            self.add_item_to_list(item_data)

    def add_item_to_list(self, item_data):
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(200, 110))
        item.setData(Qt.ItemDataRole.UserRole, item_data['file_path'])
        
        widget = ClipboardItemWidget(item_data)
        widget.delete_clicked.connect(self.delete_item)
        
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def delete_item(self, item_id):
        # Find item with this ID
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget.item_id == item_id:
                # Remove from DB/Disk
                self.clipboard_manager.delete_history_item(item_id, widget.file_path)
                # Remove from UI
                self.list_widget.takeItem(self.list_widget.row(item))
                break

    def clear_all(self):
        self.clipboard_manager.clear_history()
        self.list_widget.clear()
