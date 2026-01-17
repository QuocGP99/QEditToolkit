# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-17]
### Added
- **Audio Waveforms**: Visualization for audio files (.mp3, .wav) using FFmpeg.
- **View Modes**: Switch between "Icon View", "List View", and "Large Icons" in the Asset Manager.
- **Context-Aware Import**: Importing assets now respects the currently selected folder in the sidebar.
- **Smart Paste UI**: Improved dialog for pasting images directly to DaVinci Resolve bins.

### Changed
- **Asset Grid Layout**: Fixed grid size to prevent layout shifting with long filenames.
- **Sorting**: Assets are now sorted alphabetically (A-Z) by default.
- **Double-Click Action**: Double-clicking an asset now opens it in the default system viewer (or Space key).

### Fixed
- Fixed an issue where imported files were always saved to the root storage directory.
- Fixed layout alignment issues in the Asset Grid.
- **Favorites Sync**: Fixed an issue where the Favorites count and star indicators were not updating correctly (DB logic & UI sync).

### Added (Session 2)
- **Recursive Folder Import**: Import entire folder structures while preserving hierarchy vs flat import.
- **Import Progress**: Added progress bar for bulk file and folder imports.
- **Dynamic Favorites Count**: Sidebar now displays separate real-time count for Favorites.
- **Refactoring**: Improved code cleanliness in DBManager and MainWindow; prevented auto-creation of empty `clipboard_history` folder.

### Added (Session 3)
- **Configurable Storage**: User can now select any folder as the main storage location on first run.
- **Auto-Sync Cleanup**: App automatically scans and removes assets from the database if their physical files are missing on startup.
- **Folder Visibility Fix**: Fixed sidebar folder tree not updating immediately after creating new folders in non-default storage usage.
