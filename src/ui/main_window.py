import sys
import os
import subprocess
import shutil
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QSplitter,
    QSplitter,
    QMenu,
    QDialog,
    QComboBox,
)

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QAction

try:
    from src.ui.asset_grid import AssetGrid
    from src.database.db_manager import DBManager
    from src.core.file_manager import FileManager
    from src.ui.preview_panel import PreviewPanel
    from src.ui.project_generator import ProjectGeneratorDialog
    from src.core.resolve_api import ResolveAPI
    from src.core.clipboard_manager import ClipboardManager
    from src.ui.smart_paste_dialog import SmartPasteDialog
    from src.ui.clipboard_history_panel import ClipboardHistoryPanel

except ImportError:
    # Handle running directly for testing
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from src.ui.asset_grid import AssetGrid
    from src.database.db_manager import DBManager
    from src.core.file_manager import FileManager
    from src.ui.preview_panel import PreviewPanel
    from src.ui.project_generator import ProjectGeneratorDialog
    from src.core.resolve_api import ResolveAPI
    from src.core.clipboard_manager import ClipboardManager
    from src.ui.smart_paste_dialog import SmartPasteDialog



class MainWindow(QMainWindow):
    def __init__(self, storage_path=None):
        super().__init__()
        self.setWindowTitle("DVR Asset Manager")
        self.resize(1200, 800)
        
        # Storage Path
        self.storage_path = storage_path
        if not self.storage_path:
            # Fallback (should be handled by main.py but for safety)
            self.storage_path = os.path.abspath("storage")
        
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
        
        # Global Stylesheet
        self.setStyleSheet("""
            QWidget {
                font-family: "SF Pro Text", "Segoe UI", sans-serif;
                font-size: 10pt;
            }
            QToolTip {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                padding: 4px;
            }
        """)

        # Initialize Core Systems
        self.db = DBManager()
        self.file_manager = FileManager(self.db, storage_dir=self.storage_path)
        self.resolve_api = ResolveAPI()
        self.clipboard_manager = ClipboardManager(db_manager=self.db)
        
        # Track current folder for imports
        self.current_category = None

        # Setup UI
        self.setup_ui()
        self.setup_ui()
        self.sync_database_with_storage() # Auto-sync on startup
        self.load_assets()
        self._populate_categories()
        self.update_favorites_count()

    def setup_ui(self):
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar (Left)
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(250)
        self.sidebar_container.setStyleSheet(
            "background-color: #252525; border-right: 1px solid #333;"
        )
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)

        # Sidebar Items - Static
        # Header Area with Buttons
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 5, 0, 5)

        title_label = QLabel("LIBRARY")
        title_label.setStyleSheet("color: #888; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        reload_btn = QPushButton("↻")
        reload_btn.setToolTip("Reload Library")
        reload_btn.setFixedSize(24, 24)
        reload_btn.setStyleSheet(self._get_icon_btn_style())
        reload_btn.clicked.connect(self.reload_library)
        header_layout.addWidget(reload_btn)

        new_folder_btn = QPushButton("+")
        new_folder_btn.setToolTip("New Folder")
        new_folder_btn.setFixedSize(24, 24)
        new_folder_btn.setStyleSheet(self._get_icon_btn_style())
        new_folder_btn.clicked.connect(self.create_new_folder)
        header_layout.addWidget(new_folder_btn)

        self.sidebar_layout.addWidget(header_widget)

        # All Assets button
        all_btn = QPushButton("All Assets")
        all_btn.setProperty("filter_type", "all")
        all_btn.clicked.connect(lambda: self.filter_by_category(None))
        self._style_sidebar_button(all_btn)
        self.sidebar_layout.addWidget(all_btn)

        # Favorites button
        self.fav_btn = QPushButton("⭐ Favorites")
        self.fav_btn.setProperty("filter_type", "favorites")
        self.fav_btn.clicked.connect(lambda: self.filter_by_favorites())
        self._style_sidebar_button(self.fav_btn)
        self.sidebar_layout.addWidget(self.fav_btn)
        # Identify for easy lookup (e.g. finding by FindChild if needed elsewhere, though self.fav_btn is enough)
        self.fav_btn.setObjectName("Favorites")

        # Clipboard History Sidebar Button
        hist_btn = QPushButton("📋 Clipboard History")
        hist_btn.clicked.connect(self.toggle_clipboard_history)
        self._style_sidebar_button(hist_btn)
        self.sidebar_layout.addWidget(hist_btn)

        # Categories section header
        cat_label = QLabel("FOLDERS")
        cat_label.setStyleSheet(
            "color: #666; font-size: 11px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;"
        )
        self.sidebar_layout.addWidget(cat_label)

        # Folder Tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: transparent;
                border: none;
                color: #ccc;
            }
            QTreeWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #333;
            }
            QTreeWidget::item:selected {
                background-color: #404040;
                color: white;
            }
        """
        )
        self.folder_tree.itemClicked.connect(self._on_folder_clicked)
        # Context Menu for Delete
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(
            self.show_folder_context_menu
        )

        self.sidebar_layout.addWidget(self.folder_tree)

        # Storage Button (Bottom)
        storage_btn = QPushButton("Open Storage Folder")
        storage_btn.clicked.connect(self.open_storage_folder)
        storage_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #333;
                color: #aaa;
                border: none;
                padding: 8px;
                border-radius: 4px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #444;
                color: white;
            }
        """
        )
        self.sidebar_layout.addWidget(storage_btn)

        # Project Generator Button
        project_gen_btn = QPushButton("📁 New Project")
        project_gen_btn.clicked.connect(self.open_project_generator)
        project_gen_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                margin-top: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """
        )
        self.sidebar_layout.addWidget(project_gen_btn)

        # 2. Main Content Area (Right)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Bar (Search + Sidebar Toggle)
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet(
            "background-color: #1e1e1e; border-bottom: 1px solid #333;"
        )
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)

        # Sidebar Toggle Button
        toggle_btn = QPushButton("☰")
        toggle_btn.setFixedSize(32, 32)
        toggle_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #ccc;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                color: white;
                background-color: #333;
                border-radius: 4px;
            }
        """
        )
        toggle_btn.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(toggle_btn)

        # View Mode Selector
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Icon View", "List View", "Large Icons"])
        self.view_mode_combo.setFixedWidth(120)
        self.view_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px;
                color: #eee;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.view_mode_combo.currentIndexChanged.connect(self.change_view_mode)
        top_layout.addWidget(self.view_mode_combo)
        
        # Spacer
        top_layout.addSpacing(10)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search assets...")
        self.search_in.setStyleSheet(
            """
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px;
                color: #eee;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """
        )
        self.search_in.textChanged.connect(self.load_assets)
        top_layout.addWidget(self.search_in)

        import_btn = QPushButton("Import Asset ▼")
        import_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #007acc; 
                color: white; 
                border: none; 
                padding: 6px 12px; 
                border-radius: 4px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0062a3;
            }
            QPushButton::menu-indicator {
                image: none;
            }
            """
        )
        # Create Menu
        import_menu = QMenu(import_btn)
        import_menu.setStyleSheet("""
            QMenu {
                background-color: #252525;
                color: #ddd;
                border: 1px solid #444;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
        """)
        
        action_files = QAction("Import Files...", self)
        action_files.triggered.connect(self.import_assets)
        import_menu.addAction(action_files)
        
        action_folder = QAction("Import Folder...", self)
        action_folder.triggered.connect(self.import_folder_action)
        import_menu.addAction(action_folder)
        
        import_btn.setMenu(import_menu)
        top_layout.addWidget(import_btn)

        content_layout.addWidget(top_bar)

        # Status Bar / Message
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "background-color: #1e1e1e; color: #666; padding: 4px 10px; font-size: 11px;"
        )

        # Splitter for Grid and Preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")
        
        # Asset Grid
        self.grid = AssetGrid(self)
        self.splitter.addWidget(self.grid)

        # Preview Panel (Info Panel)
        self.preview_panel = PreviewPanel()
        self.preview_panel.favorite_toggled.connect(self.on_favorite_toggled)
        self.splitter.addWidget(self.preview_panel)
        self.preview_panel.hide() # Default hidden
        
        # Clipboard History Panel (Initially Hidden)
        self.clipboard_panel = ClipboardHistoryPanel(self.clipboard_manager)
        self.clipboard_panel.hide()
        self.splitter.addWidget(self.clipboard_panel)

        # Set splitter sizes (Grid gets more space)
        # Initial: [Grid, Preview Hidden, Clipboard Hidden]
        self.splitter.setSizes([1200, 0, 0])

        # Add stretch to splitter to ensure it fills available space
        content_layout.addWidget(self.splitter, 1)
        content_layout.addWidget(self.status_label)

        # Add sidebar and content to main layout
        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(content_widget, 1) # content_widget gets all extra space

        # Shortcuts
        self.select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.select_all_shortcut.activated.connect(self.grid.selectAll)

        # Connect grid selection to preview
        # Use itemSelectionChanged to handle both selection and deselection (clicking empty space)
        self.grid.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Listen for favorite changes from Grid (Context Menu)
        self.grid.favorite_changed.connect(lambda _: self.update_favorites_count())
        # Listen for deletions
        self.grid.item_deleted.connect(lambda: self.update_favorites_count())

    def on_selection_changed(self):
        items = self.grid.selectedItems()
        if not items:
            self.preview_panel.hide()
            # Collapse splitter section 1 (Preview) to 0
            sizes = self.splitter.sizes()
            if len(sizes) >= 2:
                # Keep clipboard part if exists, clean preview part
                # [Grid, Preview, Clipboard]
                new_sizes = list(sizes)
                new_sizes[1] = 0 
                # Give space back to Grid
                new_sizes[0] += sizes[1]
                self.splitter.setSizes(new_sizes)
            return

        # If has selection, update
        self.on_asset_clicked(items[0])

    def _get_icon_btn_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background-color: #333;
                border-radius: 4px;
            }
        """

    def _style_sidebar_button(self, btn):
        btn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 8px;
                background-color: transparent;
                color: #ccc;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """
        )

    def on_asset_clicked(self, item):
        # Update preview panel
        asset_id = item.data(Qt.ItemDataRole.UserRole + 1)
        asset_data = self.db.get_asset_by_id(asset_id)
        if asset_data:
            if not self.preview_panel.isVisible():
                self.preview_panel.show()
                # Adjust splitter size
                sizes = self.splitter.sizes()
                if len(sizes) == 3: 
                     clip_width = sizes[2]
                     avail = sizes[0] + sizes[1]
                     # Info panel needs less space (e.g. 250px)
                     self.splitter.setSizes([avail - 250, 250, clip_width])
                else:
                     self.splitter.setSizes([800, 250])

            self.preview_panel.update_preview(asset_data)
        
    def on_favorite_toggled(self, asset_id):
        new_state = self.db.toggle_favorite(asset_id)
        # Update UI in Grid
        # Find item in grid
        for index in range(self.grid.count()):
            item = self.grid.item(index)
            if item.data(Qt.ItemDataRole.UserRole + 1) == asset_id:
                # Update item display
                name = item.text()
                if new_state:
                    if not name.startswith("⭐ "):
                        item.setText("⭐ " + name)
                else:
                    if name.startswith("⭐ "):
                        item.setText(name.replace("⭐ ", ""))
                
                item.setData(Qt.ItemDataRole.UserRole + 2, new_state)
                break
        
        # If in Favorites view, refresh
        fav_btn = self.sidebar_container.findChild(QPushButton, "Favorites")
        if fav_btn and fav_btn.isChecked():
                self.filter_by_favorites()
        
        # Update Favorites count
        self.update_favorites_count()

    def update_favorites_count(self):
        """Update the Favorites button label with current count."""
        try:
             # Count manually or add a DB method. 
             favorites = [a for a in self.db.get_all_assets() if a.get("is_favorite")]
             count = len(favorites)
             self.fav_btn.setText(f"⭐ Favorites ({count})")
        except Exception as e:
             print(f"Error updating fav count: {e}")

    def toggle_sidebar(self):
        visible = self.sidebar_container.isVisible()
        self.sidebar_container.setVisible(not visible)

    def reload_library(self):
        self._populate_categories()
        self.load_assets(self.search_in.text())

    def change_view_mode(self, index):
        modes = ["icon", "list", "large"]
        if 0 <= index < len(modes):
            self.grid.set_view_mode(modes[index])

    def _populate_categories(self):
        # Clear existing
        self.folder_tree.clear()

        # Load all unique folder paths from DB
        db_categories = set(self.db.get_all_categories())

        # Also scan physical storage for empty folders
        storage_path = self.storage_path
        physical_categories = set()
        if os.path.exists(storage_path):
            for root, dirs, files in os.walk(storage_path):
                rel_path = os.path.relpath(root, storage_path)
                if rel_path == ".":
                    continue
                # Exclude clipboard_history from the main folder tree
                if "clipboard_history" in rel_path:
                    continue
                    
                rel_path = rel_path.replace("\\", "/")
                physical_categories.add(rel_path)

        # Merge both sources
        categories = sorted(list(db_categories.union(physical_categories)))
        # Filter out clipboard_history if it came from DB
        categories = [c for c in categories if "clipboard_history" not in c]

        # Get DB counts

        # Get DB counts
        counts = self.db.get_category_counts()

        # Build tree structure
        tree_dict = {}
        for path in categories:
            parts = path.split("/")
            current = tree_dict
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Helper to get recursive count if needed, or just specific category count
        # For now, simplistic approach: match path to DB category count

        # Recursively add to tree widget
        def add_items(parent, d, path_so_far=""):
            for name, children in sorted(d.items()):
                full_path = f"{path_so_far}/{name}" if path_so_far else name

                # Get count
                count = counts.get(full_path, 0)
                display_text = f"{name} ({count})" if count > 0 else name

                item = QTreeWidgetItem([display_text])
                item.setData(0, Qt.ItemDataRole.UserRole, full_path)

                if parent is None:
                    self.folder_tree.addTopLevelItem(item)
                else:
                    parent.addChild(item)

                if children:
                    add_items(item, children, full_path)

        add_items(None, tree_dict)
        self.folder_tree.expandAll()

    def _on_folder_clicked(self, item, column):
        # Get the full path stored in item data
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        self.filter_by_category(folder_path)

    def show_folder_context_menu(self, position):
        item = self.folder_tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        delete_action = menu.addAction("Delete Folder")
        action = menu.exec(self.folder_tree.mapToGlobal(position))

        if action == delete_action:
            self.delete_folder(item)

    def delete_folder(self, item):
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(
            self,
            "Delete Folder",
            f"Are you sure you want to delete folder '{folder_path}'?\nThis will remove ALL assets inside it.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            # 1. Delete all assets in this category from DB
            # Note: This is a prefix match if we follow category logic
            assets = [
                a
                for a in self.db.get_all_assets()
                if (a.get("category_name") or "").startswith(folder_path)
            ]

            for asset in assets:
                self.db.delete_asset(asset["id"])
                # Delete file? Yes
                if os.path.exists(asset["file_path"]):
                    try:
                        os.remove(asset["file_path"])
                    except:
                        pass

            # 2. Delete physical folder
            storage_path = self.storage_path
            full_dir_path = os.path.join(storage_path, folder_path)
            if os.path.exists(full_dir_path):
                try:
                    shutil.rmtree(full_dir_path)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", f"Could not delete directory: {e}"
                    )
                    return

            QMessageBox.information(self, "Success", "Folder deleted.")
            self.reload_library()

    def filter_by_category(self, category_name):
        self.current_category = category_name # Track selection
        self.grid.clear()
        if category_name:
            # Filter by prefix match (so clicking parent folder shows all children)
            assets = [
                a
                for a in self.db.get_all_assets()
                if (a.get("category_name") or "").startswith(category_name)
            ]
        else:
            assets = self.db.get_all_assets()
        
        # Sort assets by name
        assets.sort(key=lambda x: x.get("file_name", "").lower())

        for asset in assets:
            self.grid.add_asset_item(asset)
        self.status_label.setText(f"{len(assets)} assets loaded.")

    def filter_by_favorites(self):
        self.grid.clear()
        assets = [a for a in self.db.get_all_assets() if a.get("is_favorite")]
        for asset in assets:
            self.grid.add_asset_item(asset)
        self.status_label.setText(f"{len(assets)} favorites loaded.")

    def create_new_folder(self):
        from PyQt6.QtWidgets import QInputDialog

        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and folder_name:
            # Create in storage directory
            storage_path = self.storage_path
            new_path = os.path.join(storage_path, folder_name)

            try:
                os.makedirs(new_path, exist_ok=True)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Folder '{folder_name}' created.\n(Note: Empty folders might not appear until you add files)",
                )
                self._populate_categories()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")

    def load_assets(self, query=None):
        self.grid.clear()
        if query:
            assets = self.db.search_assets(query)
        else:
            assets = self.db.get_all_assets()
            
        # Sort assets by name
        assets.sort(key=lambda x: x.get("file_name", "").lower())

        for asset in assets:
            self.grid.add_asset_item(asset)
        self.status_label.setText(f"{len(assets)} assets loaded.")

    def import_assets(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Assets",
            "",
            "All Files (*.*);;Videos (*.mp4 *.mov *.avi);;Images (*.png *.jpg);;DaVinci Files (*.drfx *.setting *.cube)",
        )
        if files:
            # Show progress for bulk file import
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Importing files...", "Cancel", 0, len(files), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            count = 0
            for i, file_path in enumerate(files):
                if progress.wasCanceled():
                    break
                
                if self.file_manager.import_file(file_path, category_path=self.current_category):
                    count += 1
                progress.setValue(i + 1)

            self.load_assets()
            self._populate_categories()
            QMessageBox.information(
                self, "Import Complete", f"Successfully imported {count} assets."
            )

    def sync_database_with_storage(self):
        """
        Scans DB assets and removes them if the file no longer exists in storage.
        This fulfills the requirement: 'delete from storage -> delete from app'.
        """
        assets = self.db.get_all_assets()
        removed_count = 0
        for asset in assets:
            file_path = asset.get('file_path')
            if file_path and not os.path.exists(file_path):
                print(f"Sync: Removing missing asset {asset.get('file_name')} (ID: {asset.get('id')})")
                self.db.delete_asset(asset.get('id'))
                removed_count += 1
        
        if removed_count > 0:
            print(f"Sync: Removed {removed_count} missing assets from database.")
    
    def import_folder_action(self):
        """Import entire folder with structure."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Import")
        if not folder_path:
            return
            
        from PyQt6.QtWidgets import QProgressDialog
        
        # We need to know total first? scan_directory does it now.
        # But for UI responsiveness, we pass a callback.
        
        progress = QProgressDialog("Scanning and Importing...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0) # Show immediately
        progress.setValue(0)
        
        def update_progress(current, total):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f"Importing {current}/{total}...")
            QApplication.processEvents() # Keep UI alive
            if progress.wasCanceled():
                return
        
        # Determine target category (create a container folder for the import)
        folder_name = os.path.basename(folder_path)
        if self.current_category:
            target_category = f"{self.current_category}/{folder_name}"
        else:
            target_category = folder_name

        # Run import
        count = self.file_manager.scan_directory(
            folder_path, 
            base_category=target_category,
            progress_callback=update_progress
        )
        
        progress.setValue(progress.maximum())
        
        self.load_assets()
        self._populate_categories()
        
        QMessageBox.information(
            self, "Import Complete", f"Successfully imported {count} assets from folder."
        )

    def open_storage_folder(self):
        storage_path = os.path.abspath("storage")
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        if sys.platform == "win32":
            os.startfile(storage_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", storage_path])
        else:
            subprocess.Popen(["xdg-open", storage_path])

    def open_project_generator(self):
        """Open the Dynamic Project Generator dialog"""
        dialog = ProjectGeneratorDialog(self)
        dialog.project_created.connect(self.on_project_created)
        dialog.exec()

    def on_project_created(self, folder_path):
        """Handle project creation"""
        # Project folder created successfully
        pass

    def keyPressEvent(self, event):
        """Handle global shortcuts like Ctrl+V"""
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.handle_clipboard_paste()
        else:
            super().keyPressEvent(event)
    
    def toggle_clipboard_history(self):
        if self.clipboard_panel.isVisible():
            self.clipboard_panel.hide()
        else:
            self.clipboard_panel.show()
            self.clipboard_panel.refresh_list()
            # Force give space to panel: [Grid, Preview, Panel]
            # Try to take space from Grid/Preview
            sizes = self.splitter.sizes()
            if len(sizes) >= 3:
                # Assuming index 2 is clipboard panel
                # Give it 300px
                current_total = sum(sizes)
                new_size = [max(sizes[0] - 150, 100), max(sizes[1] - 150, 100), 300]
                self.splitter.setSizes(new_size)

    def handle_clipboard_paste(self):
        """
        Intercepts Paste, saves image to history, then shows dialog (optional) or just notifies.
        For now, let's keep the user workflow simple: Save to History -> Show History Panel.
        """
        if not self.clipboard_manager.has_image():
            return
        
        # 1. Save to History
        file_path = self.clipboard_manager.save_clipboard_image()
        if file_path:
            self.status_label.setText(f"📋 Saved to Clipboard History: {os.path.basename(file_path)}")
            
            # 2. Show Panel
            if not self.clipboard_panel.isVisible():
                self.clipboard_panel.show()
                sizes = self.splitter.sizes()
                if len(sizes) >= 3:
                    new_size = [max(sizes[0] - 150, 100), max(sizes[1] - 150, 100), 300]
                    self.splitter.setSizes(new_size)
                
            self.clipboard_panel.refresh_list()
        else:
            QMessageBox.warning(self, "Paste Error", "Failed to save image from clipboard.")
