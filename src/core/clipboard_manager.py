from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QMimeData, QUrl
import os
import datetime

class ClipboardManager:
    """
    Handles clipboard interactions, specifically checking for images 
    and saving them to a temporary or project storage location.
    """
    def __init__(self, db_manager=None, storage_path="storage/clipboard_history"):
        self.db_manager = db_manager # Optional dependency
        self.storage_path = storage_path
        # self._ensure_storage_exists() # Removed auto-creation

    def _ensure_storage_exists(self):
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def has_image(self):
        """Checks if the clipboard currently contains an image."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        return mime_data.hasImage()

    def save_clipboard_image(self):
        """
        Saves the image from clipboard to disk.
        Returns the absolute path to the saved file, or None if failed.
        """
        if not self.has_image():
            return None

        clipboard = QApplication.clipboard()
        image = clipboard.image()
        
        if image.isNull():
            print("DEBUG: Clipboard image is Null. Formats available:", clipboard.mimeData().formats())
            return None

        # Generate unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paste_{timestamp}.png"
        
        # Ensure dir exists (again, just to be safe)
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
        filepath = os.path.join(self.storage_path, filename)
        abs_path = os.path.abspath(filepath)
        print(f"DEBUG: Saving image to {abs_path}")

        try:
            success = image.save(abs_path, "PNG")
            if not success:
                 print("DEBUG: image.save() returned False")
                 return None
            
            # Save to History DB if available
            if self.db_manager:
                self.db_manager.add_clipboard_item(abs_path, image.width(), image.height())
            
            return abs_path
        except Exception as e:
            print(f"DEBUG: Error saving image: {e}")
            return None

    def copy_file_to_clipboard(self, file_path):
        """
        Places the given file path onto the clipboard as a System File Object (List of URLs).
        This allows pasting into Finder/Explorer/Resolve.
        """
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        
        url = QUrl.fromLocalFile(os.path.abspath(file_path))
        mime_data.setUrls([url])
        
        clipboard.setMimeData(mime_data)

    def delete_history_item(self, item_id, file_path):
        """Removes the item from DB and deleting the file."""
        if self.db_manager:
            self.db_manager.delete_clipboard_item(item_id)
        
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting history file: {e}")

    def clear_history(self):
        """Clears all history from DB and deletes all files."""
        if not self.db_manager:
            return
            
        files_to_delete = self.db_manager.clear_clipboard_history()
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting history file: {e}")

