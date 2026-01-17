import sys
import os

class ResolveAPI:
    """
    Wrapper for DaVinci Resolve Scripting API.
    Handles connection to Resolve and basic bin operations.
    """
    def __init__(self):
        self.resolve = self._connect_to_resolve()
        self.project_manager = self.resolve.GetProjectManager() if self.resolve else None
        self.project = self.project_manager.GetCurrentProject() if self.project_manager else None
        self.media_pool = self.project.GetMediaPool() if self.project else None

    def _connect_to_resolve(self):
        """Attempts to connect to the running DaVinci Resolve instance."""
        try:
            # 1. Try direct import (works if PYTHONPATH is set)
            try:
                import DaVinciResolveScript as dvr_script
                return dvr_script.scriptapp("Resolve")
            except ImportError:
                pass

            # 2. Windows: Try to load module from standard installation paths
            if sys.platform.startswith("win"):
                expected_paths = [
                    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Developer\Scripting\Modules",
                    r"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
                ]
                
                for path in expected_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        sys.path.append(expanded_path)
                        try:
                            import DaVinciResolveScript as dvr_script
                            return dvr_script.scriptapp("Resolve")
                        except ImportError:
                            continue

            # 3. macOS/Linux fallback (generic env check)
            # (Already covered by direct import usually if env vars are set)
            
            return None
        except Exception as e:
            print(f"Failed to connect to Resolve: {e}")
            return None

    def is_connected(self):
        return self.resolve is not None

    def get_root_folder(self):
        """Returns the root folder of the media pool."""
        if not self.media_pool:
            return None
        return self.media_pool.GetRootFolder()

    def get_subfolders(self, folder):
        """Returns a list of subfolders in the given folder."""
        if not folder:
            return []
        return folder.GetSubFolderList()

    def get_all_bins(self):
        """
        Recursively retrieves all bins (folders) in the media pool.
        Returns a list of generic objects or dicts for the UI.
        """
        if not self.media_pool:
            return []
        
        root = self.get_root_folder()
        if not root:
            return []
        
        bins = []
        self._traverse_folders(root, bins)
        return bins

    def _traverse_folders(self, folder, bin_list, path=""):
        """Recursive helper to traverse folders."""
        current_path = f"{path}/{folder.GetName()}" if path else folder.GetName()
        bin_list.append({"name": folder.GetName(), "path": current_path, "obj": folder})
        
        for sub in folder.GetSubFolderList():
            self._traverse_folders(sub, bin_list, current_path)

    def set_current_bin(self, bin_obj):
        """Sets the current folder in Media Pool to the specified bin object."""
        if not self.media_pool or not bin_obj:
            return False
        return self.media_pool.SetCurrentFolder(bin_obj)

    def create_bin(self, name, parent_folder=None):
        """Creates a new bin."""
        if not self.media_pool:
            return None
        
        target_folder = parent_folder if parent_folder else self.get_root_folder()
        return self.media_pool.AddSubFolder(target_folder, name)
