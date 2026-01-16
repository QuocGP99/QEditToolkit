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
    QMenu,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QAction

try:
    from src.ui.asset_grid import AssetGrid
    from src.database.db_manager import DBManager
    from src.core.file_manager import FileManager
    from src.ui.preview_panel import PreviewPanel
    from src.ui.project_generator import ProjectGeneratorDialog
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DVR Asset Manager")
        self.resize(1200, 800)

        # Initialize Core Systems
        self.db = DBManager()
        self.file_manager = FileManager(self.db)

        # Setup UI
        self.setup_ui()
        self.load_assets()
        self._populate_categories()

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
        fav_btn = QPushButton("⭐ Favorites")
        fav_btn.setProperty("filter_type", "favorites")
        fav_btn.clicked.connect(lambda: self.filter_by_favorites())
        self._style_sidebar_button(fav_btn)
        self.sidebar_layout.addWidget(fav_btn)

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

        import_btn = QPushButton("Import Asset")
        import_btn.setStyleSheet(
            "background-color: #007acc; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;"
        )
        import_btn.clicked.connect(self.import_assets)
        top_layout.addWidget(import_btn)

        content_layout.addWidget(top_bar)

        # Status Bar / Message
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "background-color: #1e1e1e; color: #666; padding: 4px 10px; font-size: 11px;"
        )

        # Splitter for Grid and Preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")

        # Asset Grid
        self.grid = AssetGrid(self)
        splitter.addWidget(self.grid)

        # Preview Panel
        self.preview_panel = PreviewPanel()
        splitter.addWidget(self.preview_panel)

        # Set splitter sizes (Grid gets more space)
        splitter.setSizes([800, 400])

        content_layout.addWidget(splitter)
        content_layout.addWidget(self.status_label)

        # Add sidebar and content to main layout
        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(content_widget)

        # Shortcuts
        self.select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.select_all_shortcut.activated.connect(self.grid.selectAll)

        # Connect grid selection to preview
        self.grid.itemClicked.connect(self.on_asset_clicked)

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
            self.preview_panel.update_preview(asset_data)

    def toggle_sidebar(self):
        visible = self.sidebar_container.isVisible()
        self.sidebar_container.setVisible(not visible)

    def reload_library(self):
        self._populate_categories()
        self.load_assets(self.search_in.text())

    def _populate_categories(self):
        # Clear existing
        self.folder_tree.clear()

        # Load all unique folder paths from DB
        db_categories = set(self.db.get_all_categories())

        # Also scan physical storage for empty folders
        storage_path = os.path.abspath("storage")
        physical_categories = set()
        if os.path.exists(storage_path):
            for root, dirs, files in os.walk(storage_path):
                rel_path = os.path.relpath(root, storage_path)
                if rel_path == ".":
                    continue
                rel_path = rel_path.replace("\\", "/")
                physical_categories.add(rel_path)

        # Merge both sources
        categories = sorted(list(db_categories.union(physical_categories)))

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
            storage_path = os.path.abspath("storage")
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
            storage_path = os.path.abspath("storage")
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
            count = 0
            for file_path in files:
                if self.file_manager.import_file(file_path):
                    count += 1

            self.load_assets()
            self._populate_categories()
            QMessageBox.information(
                self, "Import Complete", f"Successfully imported {count} assets."
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
        dialog.exec()
