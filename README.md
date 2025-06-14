# DICOM CLI

A Python CLI application for interactive DICOM (medical imaging) file viewing and editing using the Textual TUI framework.

## Features

- **Interactive DICOM tag navigation**: Tree-based display of all DICOM tags with expandable sequences
- **Single and bulk file editing**: Edit DICOM tag values across single files or entire directories
- **Advanced image visualization**: 
  - Unicode block-based pixel array visualization in terminal
  - High-quality sixel graphics support for compatible terminals
  - Multiple windowing presets for different tissue types (Auto, Soft Tissue, Lung, Bone, Brain, Liver, Mediastinum)
- **Split-screen view**: View DICOM tags and images side-by-side
- **Safety features**: Automatic backup creation, critical tag protection, slice-specific tag filtering
- **Multiple themes**: Beautiful medical/scientific color schemes
- **File navigation**: Navigate through multiple DICOM files with proper slice ordering

## Requirements

### Python Dependencies

- Python 3.12 or higher
- Dependencies are automatically installed via `uv` (see Installation section)

### System Dependencies

For sixel graphics support (optional but recommended):

**Ubuntu/Debian:**
```bash
sudo apt-get install libsixel-dev libsixel-bin
```

**macOS (with Homebrew):**
```bash
brew install libsixel
```

**Arch Linux:**
```bash
sudo pacman -S libsixel
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dicom-cli
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

   If you don't have `uv` installed:
   ```bash
   pip install uv
   uv sync
   ```

## Usage

### Basic Usage

**View a single DICOM file:**
```bash
uv run python dicom_cli.py path/to/file.dcm
```

**View all DICOM files in a directory:**
```bash
uv run python dicom_cli.py path/to/dicom/directory/
```

### Navigation and Controls

#### File Navigation
- `h` or `ê`: Previous file
- `l` or `í`: Next file

#### Tag Tree Navigation
- `j` or `ì`: Move down in tree
- `k` or `ë`: Move up in tree
- `Space` or `Enter`: Expand/collapse tree nodes

#### Image Viewing
- `i`: Toggle between full tag view and split view (tags + image)
- `x`: Toggle between Unicode blocks and sixel graphics (in image view)
- `w`: Cycle forward through windowing presets
- `s`: Cycle backward through windowing presets

#### Editing
- `e`: Edit selected tag value
- `s`: Save changes to file(s)

#### General
- `q`: Quit application

### Image Display Modes

#### Unicode Blocks
- Works in all terminals
- Displays DICOM pixel data as Unicode block characters
- Good for basic image preview

#### Sixel Graphics
- Requires libsixel installation and compatible terminal
- High-quality image rendering with proper scaling
- Automatically adapts to terminal size
- Maintains correct aspect ratio

### Compatible Terminals for Sixel

- **xterm** (with sixel support compiled in)
- **mlterm**
- **foot**
- **WezTerm**
- **Windows Terminal** (recent versions with sixel enabled)

### Windowing Presets

The application includes medical imaging windowing presets:

- **Auto**: Automatic windowing based on image data range
- **Soft Tissue**: W:350 / L:40 - General soft tissue visualization
- **Lung**: W:1500 / L:-600 - Lung parenchyma and airways
- **Bone**: W:2000 / L:300 - Bone structures
- **Brain**: W:80 / L:40 - Brain tissue differentiation
- **Liver**: W:150 / L:30 - Liver tissue contrast
- **Mediastinum**: W:350 / L:50 - Mediastinal structures

## File Editing

### Single File Mode
When viewing a single DICOM file, you can edit individual tag values. Changes are applied to that file only.

### Bulk Editing Mode
When viewing a directory of DICOM files, the application enables bulk editing:
- Edit values across multiple files simultaneously
- Slice-specific tags are protected from bulk editing
- Consistent values across files are highlighted

### Safety Features
- **Automatic backups**: `.bak` files are created before saving changes
- **Critical tag protection**: System-critical DICOM tags cannot be modified
- **VR validation**: Only safe Value Representation types can be edited
- **Slice-specific protection**: Tags like Instance Number and Slice Location are protected in bulk mode

## Themes

The application includes four custom themes:
- **medical_blue**: Professional medical interface with blue accents
- **forest_green**: Nature-inspired green color scheme
- **purple_haze**: Modern purple and yellow contrast
- **ocean_breeze**: Deep ocean blues with teal accents

The default theme is `forest_green`. To change themes, modify the `self.theme` setting in the `__init__` method of `DicomTreeApp`.

## Troubleshooting

### Sixel Graphics Not Working
1. Verify libsixel is installed on your system
2. Check that your terminal supports sixel graphics
3. In Windows Terminal, enable sixel support in settings:
   ```json
   "experimental.rendering.sixel": true
   ```

### Import Errors
If you encounter import errors for optional dependencies:
- **PIL/Pillow**: Required for image processing - install with `uv add pillow`
- **libsixel-python**: Required for sixel graphics - automatically installed
- **textual-image**: Required for advanced image display - automatically installed

### Performance Issues
- Large DICOM files may take time to load
- Sixel rendering can be slower than Unicode blocks
- Consider using Unicode block mode for faster navigation

## Development

### Project Structure
- `dicom_cli.py`: Main application file
- `main.py`: Entry point (minimal)
- `pyproject.toml`: Project configuration and dependencies

### Dependencies Overview
- **pydicom**: DICOM file parsing and manipulation
- **textual**: Terminal user interface framework
- **textual-image**: Enhanced image display widgets
- **pillow**: Image processing and manipulation
- **numpy**: Numerical operations on pixel arrays
- **libsixel-python**: Sixel graphics encoding

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]