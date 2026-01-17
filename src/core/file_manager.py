import shutil
import uuid
import zipfile
import os
from pathlib import Path

from pathlib import Path
try:
    from src.core.preview_generator import PreviewGenerator
except ImportError:
     # Fallback for direct testing
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.core.preview_generator import PreviewGenerator

class FileManager:
    def __init__(self, db_manager, storage_dir):
        self.db_manager = db_manager
        self.storage_dir = storage_dir
        self.preview_generator = PreviewGenerator()
        if not os.path.exists(self.storage_dir):
            try:
                os.makedirs(self.storage_dir, exist_ok=True)
            except OSError as e:
                print(f"Error creating storage dir: {e}")

    def import_file(self, file_path, category_path=None):
        """
        Copies file to storage and adds to DB. Expands .drfx.
        category_path: Relative path (e.g. 'Textures/Wood') where the file should go.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        # Generate unique filename to avoid collisions
        ext = file_path.suffix.lower()
        
        # Handle DRFX specifically
        if ext == '.drfx':
            return self._process_drfx(file_path)

        # Standard file import
        new_filename = f"{file_path.stem}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Determine destination folder
        if category_path:
            dest_dir = os.path.join(self.storage_dir, category_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            dest_path = os.path.join(dest_dir, new_filename)
        else:
            dest_path = os.path.join(self.storage_dir, new_filename)

        try:
            shutil.copy2(file_path, dest_path)
            
            # Generate Preview
            file_type = self._get_file_type(ext)
            preview_path = self.preview_generator.generate_preview(dest_path, file_type)

            # Add to DB
            asset_id = self.db_manager.add_asset(
                dest_path, 
                file_path.name, 
                file_type, 
                preview_path=preview_path,
                category_name=category_path # Pass the category explicitly
            )
            return asset_id
        except Exception as e:
            print(f"Error importing {file_path}: {e}")
            return None

    def _process_drfx(self, file_path):
        """Unzips .drfx and registers internal .setting files."""
        try:
            # Create a dedicated extraction folder
            folder_name = f"{file_path.stem}_{uuid.uuid4().hex[:8]}"
            extract_path = os.path.join(self.storage_dir, folder_name)
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(file_path, 'r') as z:
                z.extractall(extract_path)
                
            # Scan extracted folder for content
            imported_count = 0
            for root, _, files in os.walk(extract_path):
                for file in files:
                    if file.lower().endswith('.setting'):
                        full_path = os.path.join(root, file)
                        
                        # Attempt to find sidecar preview (same name, .png/.jpg)
                        base_name = os.path.splitext(file)[0] # e.g. "Brush 01"
                        preview_path = None
                        
                        # Look for potential preview files
                        for img_ext in ['.png', '.jpg', '.jpeg']:
                            potential_img = os.path.join(root, base_name + img_ext)
                            if os.path.exists(potential_img):
                                preview_path = potential_img
                                break
                        
                        # Determine Category based on full relative folder path
                        # e.g. Templates/Edit/Transitions/Brush -> store as folder_path
                        rel_dir = os.path.dirname(os.path.relpath(full_path, extract_path)).replace('\\', '/')
                        category_name = rel_dir if rel_dir else 'Root'
                        
                        # Determine file_type based on path
                        file_type = 'macro' # default
                        
                        if 'Transitions' in rel_dir: file_type = 'transition'
                        elif 'Titles' in rel_dir: file_type = 'title'
                        elif 'Generators' in rel_dir: file_type = 'generator'
                        elif 'Effects' in rel_dir: file_type = 'effect'
                        
                        # Register asset
                        self.db_manager.add_asset(
                            full_path, 
                            file, # Filename (e.g. Brush 01.setting)
                            file_type, 
                            preview_path=preview_path,
                            category_name=category_name
                        )
                        imported_count += 1
            
            return imported_count
        except Exception as e:
            print(f"Error expanding drfx {file_path}: {e}")
            return None

    def scan_directory(self, dir_path, base_category=None, progress_callback=None):
        """
        Recursively scans directory and imports supported files.
        Preserves folder structure relative to dir_path.
        """
        supported_exts = {'.drfx', '.setting', '.cube', '.mp4', '.mov', '.png', '.jpg', '.wav', '.mp3'}
        
        # 1. Count total files for progress (optional but good for UX)
        total_files = 0
        for root, _, files in os.walk(dir_path):
             total_files += len([f for f in files if Path(f).suffix.lower() in supported_exts])
        
        imported_count = 0
        processed = 0
        
        dir_path = os.path.abspath(dir_path)
        
        for root, _, files in os.walk(dir_path):
            # Calculate relative folder structure
            rel_path = os.path.relpath(root, dir_path)
            if rel_path == ".":
                current_sub_cat = None
            else:
                # Normalize separators
                rel_path = rel_path.replace("\\", "/")
                current_sub_cat = rel_path

            # Combine with base_category if provided
            final_category = base_category
            if current_sub_cat:
                if base_category:
                    final_category = f"{base_category}/{current_sub_cat}"
                else:
                    final_category = current_sub_cat
            
            for file in files:
                if Path(file).suffix.lower() in supported_exts:
                    full_path = os.path.join(root, file)
                    if self.import_file(full_path, category_path=final_category):
                        imported_count += 1
                    
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total_files)
                        
        return imported_count

    def _get_file_type(self, ext):
        ext = ext.lower()
        if ext in ['.mp4', '.mov']: return 'video'
        if ext in ['.png', '.jpg']: return 'image'
        if ext in ['.wav', '.mp3']: return 'audio'
        if ext == '.drfx': return 'drfx'
        if ext == '.setting': return 'macro'
        if ext == '.cube': return 'lut'
        return 'other'
