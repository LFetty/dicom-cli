# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI application for interactive DICOM (medical imaging) file viewing and editing using the Textual TUI framework. The main functionality includes:

- Interactive tree-based navigation of DICOM tags
- Single and bulk file editing capabilities
- Unicode block-based pixel array visualization in terminal
- Multiple custom themes with medical/scientific color schemes
- Safe editing with backup creation and critical tag protection

## Architecture

### Core Components

**`dicom_cli.py`** - Main application file containing:
- `DicomTreeApp` - Main Textual app class handling file navigation, tree display, and tag editing
- `ImageViewScreen` - Modal dialog for displaying DICOM pixel arrays as Unicode blocks
- `EditTagScreen` - Modal dialog for tag value editing
- Custom theme definitions with medical/scientific color schemes
- DICOM file discovery and validation logic

**`main.py`** - Simple entry point (currently minimal)

### Key Technical Details

- Uses `pydicom` library for DICOM file parsing and manipulation
- Uses `textual` framework for the terminal user interface
- Supports both single file and bulk (multiple file) editing modes
- Implements safety measures: critical tag protection, backup creation, slice-specific tag filtering
- Theme system with 4 custom themes: medical_blue, forest_green, purple_haze, ocean_breeze
- DICOM files are automatically sorted by Instance Number for proper slice ordering
- Proper DICOM rescaling applied (slope/intercept) to convert pixel values to Hounsfield Units for accurate windowing

### DICOM Tag Editing Logic

- Only allows editing of safe VR (Value Representation) types: CS, LO, LT, PN, SH, ST, UT, DS, IS, AS, DA, DT, TM
- Protects critical DICOM structure tags from modification
- Prevents bulk editing of slice-specific tags across multiple files
- Creates `.bak` backup files before saving changes

## Development Commands

**Run the application:**
```bash
uv run python dicom_cli.py <path_to_dicom_file_or_directory>
# or
python dicom_cli.py <path_to_dicom_file_or_directory>
```

**Install dependencies:**
```bash
uv sync
```

**Add new dependencies:**
```bash
uv add <package_name>
```

## Test Data

The `test-data/DICOM/` directory contains CT scan files for testing the application. These are real DICOM files that can be used to test single file and bulk editing functionality.

## Usage Patterns

- Single file mode: Pass a DICOM file path
- Bulk mode: Pass a directory containing multiple DICOM files
- Navigation: h/l or arrow keys to switch between files, j/k to navigate tree
- Editing: Press 'e' to edit selected tag, 's' to save changes
- Image viewing: Press 'i' to toggle between full tag view and split view (tags + image)
  - Split view shows DICOM tags on left, pixel array as Unicode blocks on right
  - Full windowing controls available in split view
  - Navigation: h/l or arrow keys to navigate between files (if multiple loaded)
  - Windowing: w/s to cycle through windowing presets (Auto, Soft Tissue, Lung, Bone, Brain, Liver, Mediastinum)
- The app automatically detects if multiple files are loaded and enables bulk editing features