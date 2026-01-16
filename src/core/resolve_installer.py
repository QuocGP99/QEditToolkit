import os
import shutil
from pathlib import Path

class ResolveInstaller:
    """Handles installation of assets into DaVinci Resolve's Template directories."""
    
    def __init__(self):
        # Determine Resolve Templates Root
        # Typically: %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates
        appdata = os.getenv('APPDATA')
        if not appdata:
            # Fallback or error
            self.templates_root = None
            return

        self.templates_root = Path(appdata) / "Blackmagic Design" / "DaVinci Resolve" / "Support" / "Fusion" / "Templates"
        
        self.category_map = {
            'transition': 'Edit/Transitions',
            'title': 'Edit/Titles',
            'generator': 'Edit/Generators',
            'effect': 'Edit/Effects',
            'macro': 'Edit/Effects' # Fallback
        }

    def is_available(self):
        return self.templates_root is not None and self.templates_root.parent.exists()

    def install_asset(self, asset_data):
        """
        Copies the asset file to the appropriate Resolve directory.
        Returns (success, message)
        """
        if not self.is_available():
            return False, "Resolve Template directory not found."

        file_path = Path(asset_data['file_path'])
        file_type = asset_data.get('file_type', 'other')
        
        if not file_path.exists():
            return False, "Source file not found."
            
        # Determine target subfolder
        subfolder = self.category_map.get(file_type)
        if not subfolder:
            return False, f"Cannot install file type: {file_type}. Only .setting types supported."

        # Create target directory
        # We also might want to group them by "DVR_Drag_Import" or similar to avoid clutter?
        # For now, put them directly or in a "DVR_Manager" subfolder for organization
        target_dir = self.templates_root / subfolder / "DVR_Manager_Installs"
        
        # If the asset has a specific category name (e.g. "Brush"), maybe use that?
        category_name = asset_data.get('category_name')
        if category_name and category_name != 'Root':
             target_dir = target_dir / category_name

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = target_dir / file_path.name
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            
            # Also try to copy preview if it exists and follows Resolve naming convention?
            # Resolve uses .png sidecars sometimes.
            preview_path = asset_data.get('preview_path')
            if preview_path and os.path.exists(preview_path):
                 dest_preview = target_dir / (file_path.stem + Path(preview_path).suffix)
                 shutil.copy2(preview_path, dest_preview)
            
            return True, f"Installed to {target_dir}"
            
        except Exception as e:
            return False, str(e)
