# Database Schema

## Tables

### `assets`
Contains all media assets managed by the library.
- `id` (INTEGER PK): Unique ID.
- `file_path` (TEXT UNIQUE): Absolute path to the file.
- `file_name` (TEXT): Name of the file.
- `file_type` (TEXT): Extension (e.g., .mp4, .drfx).
- `category_name` (TEXT): Virtual folder path (e.g., "SoundFX/Impacts").
- `preview_path` (TEXT): Path to cached preview image.
- `date_added` (TIMESTAMP): Import time.
- `is_favorite` (INTEGER): 0 or 1. (Note: Logic coerces NULL to 0).

### `categories`
Stores unique category names (mostly for autocomplete or structure).
- `id` (INTEGER PK)
- `name` (TEXT UNIQUE)

### `tags`
User-defined tags.
- `id` (INTEGER PK)
- `name` (TEXT UNIQUE)
- `color` (TEXT)

### `asset_tags`
Many-to-Many relationship between assets and tags.
- `asset_id` (FK)
- `tag_id` (FK)

### `clipboard_items`
History of clipboard images.
- `id` (INTEGER PK)
- `file_path` (TEXT): Path to saved PNG.
- `width` (INTEGER)
- `height` (INTEGER)
- `created_at` (TIMESTAMP)
- `is_deleted` (BOOLEAN): Soft delete flag (currently unused, items are hard deleted).
