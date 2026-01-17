import os
import zipfile
import ffmpeg
from pathlib import Path

class PreviewGenerator:
    def __init__(self, cache_dir="cache/previews"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def generate_preview(self, file_path, file_type):
        """Generates a preview image for the file and returns the path to the image."""
        filename = Path(file_path).name
        output_path = os.path.join(self.cache_dir, f"{filename}.jpg")
        
        if os.path.exists(output_path):
            return output_path

        try:
            if file_type == 'video':
                # Generate thumbnail at 1 second mark or 00:00:01
                (
                    ffmpeg
                    .input(file_path, ss='00:00:01')
                    .filter('scale', 320, -1)
                    .output(output_path, vframes=1)
                    .run(capture_stdout=True, capture_stderr=True)
                )
                return output_path
                return output_path
            
            elif file_type == 'audio':
                # Generate waveform using showwavespic
                # Colors: cyan on dark background (or transparent)
                # s=320x120 to match grid aspect ratio roughly
                (
                    ffmpeg
                    .input(file_path)
                    .filter('showwavespic', s='320x240', colors='#007acc')
                    .output(output_path, vframes=1)
                    .run(capture_stdout=True, capture_stderr=True)
                )
                return output_path
                try:
                    with zipfile.ZipFile(file_path, 'r') as z:
                        file_list = z.namelist()
                        print(f"Inspecting {filename}: found {len(file_list)} files.")
                        
                        # Strategy 1: Look for explicit thumbnail names
                        candidates = [f for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        
                        best_candidate = None
                        
                        # Priority 1: 'thumbnail.png' or similar
                        for c in candidates:
                            name = Path(c).name.lower()
                            if 'thumbnail' in name or 'preview' in name or 'icon' in name:
                                best_candidate = c
                                break
                        
                        # Priority 2: Largest image (likely to be the preview, not a small UI icon)
                        if not best_candidate and candidates:
                            # Sort by size descending
                            candidates.sort(key=lambda x: z.getinfo(x).file_size, reverse=True)
                            best_candidate = candidates[0]

                        if best_candidate:
                            print(f"Extracting preview for {filename}: {best_candidate}")
                            # Extract just this file
                            with open(output_path, 'wb') as f:
                                f.write(z.read(best_candidate))
                            return output_path
                        else:
                            print(f"No suitable preview image found in {filename}")
                            return None
                except zipfile.BadZipFile:
                    print(f"Bad zip file: {file_path}")
                    return None
            
            elif file_type == 'image':
                # Just return the original path or copy it (resizing would be better but keep it simple)
                return file_path
                
        except ffmpeg.Error as e:
            print(f"FFmpeg error for {file_path}: {e.stderr.decode('utf8')}")
            return None
        except Exception as e:
            print(f"Preview generation error for {file_path}: {e}")
            return None
        
        return None
