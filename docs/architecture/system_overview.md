# System Architecture Overview

## Core Components

### 1. User Interface (UI)
- **MainWindow (`src/ui/main_window.py`)**: The central hub. Manages the sidebar (folders), toolbar (search, view modes), and the split view (Grid + Preview).
- **AssetGrid (`src/ui/asset_grid.py`)**: A customized `QListWidget` that displays assets. Supports multiple view modes (Icon, List, Large) and handles drag-and-drop operations.
- **PreviewPanel (`src/ui/preview_panel.py`)**: Displays details and previews for the selected asset. Handles video playback and image display.

### 2. Logic & Data Management
- **FileManager (`src/core/file_manager.py`)**: Handles physical file operations.
    - Imports files to `storage/` (supports subdirectories).
    - Expands `.drfx` bundles.
    - Triggers preview generation.
- **DBManager (`src/database/db_manager.py`)**: Manages SQLite database interactions (adding assets, querying, favorites, categories).
- **PreviewGenerator (`src/core/preview_generator.py`)**:
    - **Video**: Uses `ffmpeg` to extract a thumbnail at 1s.
    - **Audio**: Uses `ffmpeg` (`showwavespic`) to generate a blue waveform image.
    - **Images**: Uses the original file.
- **ConfigManager (`src/core/config.py`)**: Manages persistent application settings using `config.json` (e.g., storage path).
- **ResolveAPI (`src/core/resolve_api.py`)**: Handles communication with DaVinci Resolve's Scripting API.

## Data Flow

### Import Process
1.  User clicks **Import Asset**.
2.  `MainWindow` captures the selected folder (`current_category`).
3.  `FileManager.import_file` is called with the source path and category.
4.  File is copied to `storage/{category}/`.
5.  `PreviewGenerator` creates a thumbnail/waveform in `cache/previews/`.
6.  Asset metadata is saved to `app_data.db`.
7.  `AssetGrid` refreshes to show the new item.

### Smart Paste Flow
1.  User presses `Ctrl+V`.
2.  `SmartPasteDialog` appears with the clipboard image.
3.  On confirmation, image is saved temporarily.
4.  User drags the image from the dialog directly into DaVinci Resolve.
