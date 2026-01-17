from PyQt6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QMenu,
    QFileDialog,
    QMessageBox,
    QStyle,
)
from PyQt6.QtCore import Qt, QMimeData, QUrl, QSize, pyqtSignal
from PyQt6.QtGui import QDrag, QIcon, QPixmap
import os

try:
    from src.core.resolve_installer import ResolveInstaller
except ImportError:
    # Fallback or running directly
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from src.core.resolve_installer import ResolveInstaller


class AssetGrid(QListWidget):
    item_deleted = pyqtSignal() # Optional: create for deletes too
    favorite_changed = pyqtSignal(int) # Emits asset_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(180, 120))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSpacing(10)
        # Fix: Enforce strict grid size to prevent items from shifting due to long names
        self.setGridSize(QSize(200, 160)) 
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)  # Allow internal reordering if needed
        self.setDropIndicatorShown(True)

        self.installer = ResolveInstaller()

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Handle Double Click
        self.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Style for the grid
        self.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #2b2b2b;
                border-radius: 6px;
                padding: 10px;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #404040;
                border: 2px solid #007acc;
            }
            QListWidget::item:hover {
                background-color: #383838;
            }
        """
        )

    def set_view_mode(self, mode):
        """
        Switches the view mode of the list widget.
        mode: 'list' | 'icon' | 'large'
        """
        if mode == 'list':
            self.setViewMode(QListWidget.ViewMode.ListMode)
            self.setIconSize(QSize(40, 40))
            self.setGridSize(QSize()) # Reset grid size for list view (dynamic height)
            self.setSpacing(2)
        elif mode == 'icon':
            self.setViewMode(QListWidget.ViewMode.IconMode)
            self.setIconSize(QSize(180, 120))
            self.setGridSize(QSize(200, 160))
            self.setSpacing(10)
        elif mode == 'large':
            self.setViewMode(QListWidget.ViewMode.IconMode)
            self.setIconSize(QSize(280, 180))
            self.setGridSize(QSize(300, 220))
            self.setSpacing(15)

    def add_asset_item(self, asset_data):
        """
        Adds an item to the grid.
        asset_data: dict from DB (id, file_path, file_name, is_favorite, etc.)
        """
        display_name = asset_data["file_name"]
        is_favorite = asset_data.get("is_favorite", 0)

        if is_favorite:
            display_name = "⭐ " + display_name

        item = QListWidgetItem(display_name)

        # Load preview image
        preview_path = asset_data.get("preview_path")
        if preview_path and os.path.exists(preview_path):
            item.setIcon(QIcon(preview_path))
        else:
            # Placeholder or default icon based on type
            item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

        # Store data
        item.setData(Qt.ItemDataRole.UserRole, asset_data["file_path"])
        item.setData(Qt.ItemDataRole.UserRole + 1, asset_data["id"])
        item.setData(Qt.ItemDataRole.UserRole + 2, is_favorite)  # Store favorite status

        self.addItem(item)

    def startDrag(self, supportedActions):
        print("DEBUG: startDrag called")
        items = self.selectedItems()
        if not items:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        urls = []
        is_setting_file = False
        setting_content = ""

        for item in items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                # Ensure absolute path with forward slashes
                abs_path = os.path.abspath(file_path).replace("\\", "/")
                u = QUrl.fromLocalFile(abs_path)
                urls.append(u)

                # Check for .setting file content
                if abs_path.lower().endswith(".setting"):
                    is_setting_file = True
                    try:
                        with open(abs_path, "r", encoding="utf-8") as f:
                            setting_content += f.read() + "\n"
                    except:
                        pass

        if not urls:
            return

        mime_data.setUrls(urls)

        if is_setting_file and setting_content:
            mime_data.setText(setting_content)
        else:
            # Fallback: Plain text list of files
            mime_data.setText("\n".join([u.toLocalFile() for u in urls]))

        drag.setMimeData(mime_data)

        if len(items) >= 1:
            pixmap = items[0].icon().pixmap(100, 100)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

        drag.exec(Qt.DropAction.CopyAction)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu()

        # Favorites Option
        is_favorite = item.data(Qt.ItemDataRole.UserRole + 2)
        fav_text = "Remove from Favorites" if is_favorite else "Add to Favorites"
        fav_action = menu.addAction(fav_text)

        menu.addSeparator()

        # Install option
        install_action = menu.addAction("Install to DaVinci Resolve")

        menu.addSeparator()
        set_preview_action = menu.addAction("Set Preview Image...")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Asset")
        delete_selected_action = menu.addAction(
            f"Delete Selected ({len(self.selectedItems())})"
        )

        action = menu.exec(self.mapToGlobal(position))

        if action == fav_action:
            self.toggle_favorite(item)
        elif action == install_action:
            self.install_asset(item)
        elif action == set_preview_action:
            self.set_manual_preview(item)
        elif action == delete_action:
            self.delete_asset(item)
        elif action == delete_selected_action:
            self.delete_selected()

    def toggle_favorite(self, item):
        asset_id = item.data(Qt.ItemDataRole.UserRole + 1)
        is_favorite = item.data(Qt.ItemDataRole.UserRole + 2)

        # Access DB
        parent = self.parent()
        while parent and not hasattr(parent, "db"):
            parent = parent.parent()

        if parent and hasattr(parent, "db"):
            parent.db.toggle_favorite(asset_id)

            # Update Item UI immediately
            new_status = 0 if is_favorite else 1
            item.setData(Qt.ItemDataRole.UserRole + 2, new_status)

            text = item.text()
            if new_status:
                if not text.startswith("⭐ "):
                    item.setText("⭐ " + text)
            else:
                item.setText(text.replace("⭐ ", ""))
            
            # Notify MainWindow to update count
            self.favorite_changed.emit(asset_id)
        else:
            print("DB not found")

    def install_asset(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        asset_id = item.data(Qt.ItemDataRole.UserRole + 1)

        parent = self.parent()
        while parent and not hasattr(parent, "db"):
            parent = parent.parent()

        if parent and hasattr(parent, "db"):
            asset_data = parent.db.get_asset_by_id(asset_id)
            if asset_data:
                success, msg = self.installer.install_asset(asset_data)
                if success:
                    QMessageBox.information(
                        self,
                        "Install Success",
                        msg
                        + "\n\nPlease restart DaVinci Resolve or switch pages to see it.",
                    )
                else:
                    QMessageBox.warning(self, "Install Failed", msg)
            else:
                QMessageBox.warning(self, "Error", "Could not retrieve asset data.")
        else:
            QMessageBox.warning(self, "Error", "Database connection not found.")

    def set_manual_preview(self, item):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Preview Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            asset_id = item.data(Qt.ItemDataRole.UserRole + 1)

            parent = self.parent()
            while parent and not hasattr(parent, "db"):
                parent = parent.parent()

            if parent and hasattr(parent, "db"):
                parent.db.update_asset_preview(asset_id, file_path)
                item.setIcon(QIcon(file_path))
            else:
                print("Could not find DB connection")

    def delete_asset(self, item):
        confirm = QMessageBox.question(
            self,
            "Delete Asset",
            f"Are you sure you want to delete '{item.text()}'?\nThis will remove it from the library and delete the file from storage.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            asset_id = item.data(Qt.ItemDataRole.UserRole + 1)
            file_path = item.data(Qt.ItemDataRole.UserRole)

            parent = self.parent()
            while parent and not hasattr(parent, "db"):
                parent = parent.parent()

            if parent and hasattr(parent, "db"):
                parent.db.delete_asset(asset_id)
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file: {e}")

                self.takeItem(self.row(item))
            self.item_deleted.emit()

    def delete_selected(self):
        items = self.selectedItems()
        if not items:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Selected Assets",
            f"Are you sure you want to delete {len(items)} selected asset(s)?\\nThis will permanently remove them.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            parent = self.parent()
            while parent and not hasattr(parent, "db"):
                parent = parent.parent()

            if parent and hasattr(parent, "db"):
                for item in items:
                    asset_id = item.data(Qt.ItemDataRole.UserRole + 1)
                    file_path = item.data(Qt.ItemDataRole.UserRole)

                    parent.db.delete_asset(asset_id)
                    try:
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting file: {e}")

                    self.takeItem(self.row(item))
            self.item_deleted.emit()

    def _is_media_file(self, file_path):
        """Check if file is a supported media format"""
        if not file_path:
            return False

        media_extensions = {
            # Video
            ".mp4",
            ".mov",
            ".avi",
            ".mxf",
            ".m2ts",
            ".dv",
            ".m4v",
            # Audio
            ".wav",
            ".mp3",
            ".aac",
            ".m4a",
            ".flac",
            # Image
            ".png",
            ".jpg",
            ".jpeg",
            ".tiff",
            ".tif",
            ".bmp",
            ".dpx",
        }

        ext = os.path.splitext(file_path)[1].lower()
        return ext in media_extensions

    def on_item_double_clicked(self, item):
        """Handle double-click: Open file in default system viewer"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {e}")

    def keyPressEvent(self, event):
        """Handle Space key to open preview"""
        if event.key() == Qt.Key.Key_Space:
            items = self.selectedItems()
            if items:
                self.on_item_double_clicked(items[0])
        else:
            super().keyPressEvent(event)
