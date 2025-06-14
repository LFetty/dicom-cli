#!/usr/bin/env python3
"""DICOM CLI - Interactive DICOM tag viewer with tree navigation."""

import sys
from pathlib import Path
import pydicom
from textual.app import App, ComposeResult
from textual.widgets import Tree, Header, Footer, Input, Static
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.theme import Theme
from typing import List, Optional
import os
import numpy as np
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import libsixel
except ImportError:
    libsixel = None

try:
    from textual_image.widget import Image as TextualImage
except ImportError:
    TextualImage = None


def detect_sixel_support() -> bool:
    """Detect if the current terminal supports sixel graphics."""
    if libsixel is None:
        return False
    
    # Check for common sixel-capable terminals
    term = os.environ.get('TERM', '')
    term_program = os.environ.get('TERM_PROGRAM', '')
    
    # Known sixel-capable terminals
    sixel_terms = {
        'xterm-256color',  # xterm with sixel support
        'mlterm',          # mlterm
        'foot',            # foot terminal
        'wezterm',         # wezterm
    }
    
    sixel_programs = {
        'WezTerm',
        'mlterm',
        'foot',
    }
    
    # Basic heuristic detection
    if term in sixel_terms or term_program in sixel_programs:
        return True
    
    # Try a simple sixel capability test
    try:
        # Send a minimal sixel query to test support
        print('\033[?4;3;4c', end='', flush=True)
        return True  # Assume support if no exception
    except:
        return False


# Custom themes with beautiful color palettes
CUSTOM_THEMES = {
    "medical_blue": Theme(
        name="medical_blue",
        primary="#2E86AB",        # Medical blue
        secondary="#A23B72",     # Deep pink accent
        accent="#F18F01",        # Warm orange
        warning="#C73E1D",       # Red warning
        error="#C73E1D",         # Red error
        success="#6BCF7F",       # Green success
        surface="#1A1D29",       # Dark blue-gray background
        panel="#252A3A",         # Lighter panel
        dark=True,
    ),
    
    "forest_green": Theme(
        name="forest_green", 
        primary="#2D5016",        # Forest green
        secondary="#C7B446",     # Golden yellow
        accent="#68B684",        # Mint green
        warning="#E67E22",       # Orange warning
        error="#E74C3C",         # Red error
        success="#68B684",       # Green success
        surface="#1C1C1C",       # Dark background
        panel="#2C2C2C",         # Lighter panel
        dark=True,
    ),
    
    "purple_haze": Theme(
        name="purple_haze",
        primary="#6A4C93",        # Deep purple
        secondary="#FFD23F",     # Bright yellow
        accent="#FF6B6B",        # Coral red
        warning="#F39C12",       # Orange warning
        error="#E74C3C",         # Red error
        success="#2ECC71",       # Green success
        surface="#2C1810",       # Dark warm background
        panel="#3D2817",         # Warm panel
        dark=True,
    ),
    
    "ocean_breeze": Theme(
        name="ocean_breeze",
        primary="#004E89",        # Deep ocean blue
        secondary="#00A896",     # Teal
        accent="#FFB700",        # Bright orange
        warning="#FF6B35",       # Orange warning
        error="#D62828",         # Red error
        success="#00A896",       # Teal success
        surface="#001219",       # Very dark blue
        panel="#0A1A24",         # Dark blue panel
        dark=True,
    ),
}


class EditTagScreen(ModalScreen):
    """Modal screen for editing DICOM tag values."""
    
    def __init__(self, tag_name: str, current_value: str, tag_info: str, is_bulk: bool = False, bulk_info: str = "", read_only: bool = False):
        super().__init__()
        self.tag_name = tag_name
        self.current_value = current_value
        self.tag_info = tag_info
        self.is_bulk = is_bulk
        self.bulk_info = bulk_info
        self.read_only = read_only
        self.new_value = None
    
    def compose(self) -> ComposeResult:
        # Escape markup in displayed text to prevent interpretation
        escaped_tag_info = self.tag_info.replace("[", r"\[").replace("]", r"\]")
        escaped_current_value = self.current_value.replace("[", r"\[").replace("]", r"\]")
        escaped_bulk_info = self.bulk_info.replace("[", r"\[").replace("]", r"\]") if self.bulk_info else ""
        
        widgets = [
            Static(f"Edit DICOM Tag: {escaped_tag_info}", id="edit_header"),
        ]
        
        if self.is_bulk:
            widgets.append(Static(f"Bulk edit mode: {escaped_bulk_info}", id="bulk_info"))
        
        widgets.extend([
            Static(f"Current value: {escaped_current_value}", id="current_value"),
            Input(value=self.current_value, placeholder="Enter new value" if not self.read_only else "Read-only", 
                  disabled=self.read_only, id="value_input"),
            Static("Press Enter to save, Escape to cancel" if not self.read_only else "Press Escape to close", id="edit_help"),
        ])
        
        yield Container(
            Vertical(*widgets, id="edit_dialog"),
            id="edit_container"
        )
    
    def on_mount(self) -> None:
        if not self.read_only:
            self.query_one("#value_input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.read_only:
            self.new_value = event.value
            self.dismiss(self.new_value)
    
    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class DicomTreeApp(App):
    """A Textual app to display DICOM tags in a tree view."""
    
    CSS = """
    /* Main app styling */
    Screen {
        background: $surface;
    }
    
    /* Header styling */
    Header {
        background: $primary;
        color: $text;
        height: 3;
    }
    
    /* Footer styling */
    Footer {
        background: $panel;
        color: $text;
        height: 3;
    }
    
    /* Tree widget styling */
    Tree {
        background: $surface;
        color: $text;
        border: solid $accent;
        border-title-color: $accent;
        border-title-style: bold;
        scrollbar-background: $panel;
        scrollbar-color: $accent;
    }
    
    /* Tree nodes */
    Tree > .tree--guides {
        color: $accent-darken-1;
    }
    
    Tree > .tree--guides-hover {
        color: $accent;
    }
    
    Tree > .tree--cursor {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    
    Tree > .tree--highlight {
        background: $accent-darken-2;
    }
    
    /* Container styling */
    Container {
        background: $surface;
    }
    
    /* Full container (default visible) */
    #full_container {
        background: $surface;
    }
    
    #full_container.hidden {
        display: none;
    }
    
    /* Split container styling (default hidden) */
    #split_container {
        background: $surface;
        height: 100%;
    }
    
    #split_container.hidden {
        display: none;
    }
    
    #tree_split_container {
        background: $surface;
        width: 50%;
        min-width: 40;
    }
    
    /* Image viewer styling */
    #image_container {
        background: $panel;
        border: thick $accent;
        border-title-color: $accent;
        border-title-style: bold;
        width: 50%;
        min-width: 40;
    }
    
    #image_header {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin: 1 0;
    }
    
    #window_info {
        color: $secondary;
        text-style: italic;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    #unicode_image {
        color: $text;
        text-align: center;
        margin: 1 0;
    }
    
    /* TextualImage widget styling for centering and sizing */
    Image {
        align: center middle;
        margin: 1 0;
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
    }
    
    #image_help {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        margin: 1 0;
    }
    
    /* Edit dialog styling */
    #edit_container {
        background: $panel;
        border: thick $accent;
        border-title-color: $accent;
        border-title-style: bold;
    }
    
    #edit_dialog {
        background: $panel;
        padding: 1;
    }
    
    #edit_header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    #bulk_info {
        color: $warning;
        text-style: italic;
        margin: 1 0;
    }
    
    #current_value {
        color: $text;
        margin: 1 0;
    }
    
    #value_input {
        border: solid $accent;
        background: $surface;
        color: $text;
        margin: 1 0;
    }
    
    #edit_help {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("space", "toggle_node", "Toggle", show=False),
        Binding("enter", "toggle_node", "Toggle", show=False),
        Binding("h,left", "prev_file", "Previous", show=True),
        Binding("l,right", "next_file", "Next", show=True),
        Binding("e", "edit_tag", "Edit", show=True),
        Binding("s", "save_file", "Save", show=True),
        Binding("i", "view_image", "Image", show=True),
        Binding("x", "toggle_sixel", "Sixel", show=True),
    ]
    
    def __init__(self, dicom_files: List[Path], current_index: int = 0):
        super().__init__()
        self.dicom_files = dicom_files
        self.current_index = current_index
        self.dataset = None
        self.has_changes = False
        self.tag_map = {}
        self.all_datasets = {}
        self.show_image = False  # Toggle between tag tree and image view
        self.current_preset = 0  # Current windowing preset
        self.sixel_supported = detect_sixel_support()  # Check sixel support
        self.use_sixel = False  # Toggle between Unicode blocks and sixel display
        self.has_textual_image_widget = False  # Track if TextualImage widget exists
        
        # DICOM windowing presets for different tissue types
        self.window_presets = [
            ("Auto", None, None),  # Auto windowing (current behavior)
            ("Soft Tissue", 350, 40),  # Window Width: 350, Window Center: 40
            ("Lung", 1500, -600),      # Window Width: 1500, Window Center: -600
            ("Bone", 2000, 300),       # Window Width: 2000, Window Center: 300
            ("Brain", 80, 40),         # Window Width: 80, Window Center: 40
            ("Liver", 150, 30),        # Window Width: 150, Window Center: 30
            ("Mediastinum", 350, 50),  # Window Width: 350, Window Center: 50
        ]
        
        # Register custom themes
        for theme_name, theme in CUSTOM_THEMES.items():
            self.register_theme(theme)
        
        # Set default custom theme - change this to try different ones:
        # Options: "medical_blue", "forest_green", "purple_haze", "ocean_breeze"
        self.theme = "forest_green"
    
    @property
    def current_file(self) -> Path:
        """Get the currently selected DICOM file."""
        return self.dicom_files[self.current_index]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        # Full tag view container
        full_tree = Tree("DICOM Tags", id="dicom_tree_full")
        full_tree.border_title = "DICOM Tag Browser"
        yield Container(full_tree, id="full_container")
        
        # Split view container (hidden by default)
        yield Horizontal(
            Container(
                Tree("DICOM Tags", id="dicom_tree_split"),
                id="tree_split_container"
            ),
            Container(
                Static("", id="image_header"),
                Static("", id="window_info"), 
                Static("", id="unicode_image", markup=False),
                Static("", id="image_help"),
                id="image_container"
            ),
            id="split_container"
        )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.update_title()
        self.load_dicom_file()
        
        # Set initial state: show full view, hide split view
        full_container = self.query_one("#full_container")
        split_container = self.query_one("#split_container")
        
        full_container.remove_class("hidden")
        split_container.add_class("hidden")
        
        self.populate_tree()
    
    def update_title(self) -> None:
        """Update the app title with current file info."""
        file_info = f"{self.current_file.name}"
        if len(self.dicom_files) > 1:
            file_info += f" ({self.current_index + 1}/{len(self.dicom_files)})"
        if self.has_changes:
            file_info += " *"
        self.title = f"DICOM Viewer - {file_info}"
    
    def load_dicom_file(self) -> None:
        """Load the current DICOM file."""
        try:
            self.dataset = pydicom.dcmread(str(self.current_file))
            # Also load all datasets if we have multiple files for bulk editing
            if len(self.dicom_files) > 1:
                self.load_all_datasets()
        except Exception as e:
            self.exit(message=f"Error loading DICOM file: {e}")
    
    def load_all_datasets(self) -> None:
        """Load all DICOM datasets for bulk editing."""
        for file_path in self.dicom_files:
            if file_path not in self.all_datasets:
                try:
                    self.all_datasets[file_path] = pydicom.dcmread(str(file_path))
                except Exception:
                    pass  # Skip files that can't be loaded
    
    def get_tag_values_across_files(self, tag) -> dict:
        """Get tag values across all loaded files."""
        values = {}
        for file_path, dataset in self.all_datasets.items():
            try:
                if tag in dataset:
                    values[file_path] = str(dataset[tag].value)
                else:
                    values[file_path] = None
            except:
                values[file_path] = None
        return values
    
    def is_tag_consistent_across_files(self, tag) -> tuple:
        """Check if a tag has the same value across all files."""
        if len(self.dicom_files) <= 1:
            return True, None
            
        values = self.get_tag_values_across_files(tag)
        unique_values = set(v for v in values.values() if v is not None)
        
        if len(unique_values) <= 1:
            return True, list(unique_values)[0] if unique_values else None
        else:
            return False, f"Mixed values: {', '.join(list(unique_values)[:3])}{'...' if len(unique_values) > 3 else ''}"
    
    def populate_tree(self) -> None:
        """Populate the full tree with DICOM tags."""
        tree = self.query_one("#dicom_tree_full", Tree)
        tree.show_root = False
        
        # Clear existing tree content and tag map
        tree.clear()
        self.tag_map.clear()
        
        if not self.dataset:
            return
        
        # Add main dataset node
        root = tree.root.add("Dataset", expand=True)
        
        # Add all data elements
        for elem in self.dataset:
            self.add_element_to_tree(root, elem, path=[])
    
    def populate_split_tree(self) -> None:
        """Populate the split view tree with DICOM tags."""
        tree = self.query_one("#dicom_tree_split", Tree)
        tree.show_root = False
        tree.border_title = "DICOM Tags"
        
        # Clear existing tree content and tag map
        tree.clear()
        self.tag_map.clear()
        
        if not self.dataset:
            return
        
        # Add main dataset node
        root = tree.root.add("Dataset", expand=True)
        
        # Add all data elements
        for elem in self.dataset:
            self.add_element_to_tree(root, elem, path=[])
    
    def add_element_to_tree(self, parent, element, path: List = None) -> None:
        """Add a data element to the tree."""
        if path is None:
            path = []
            
        # Format tag information
        tag_str = f"({element.tag.group:04X},{element.tag.element:04X})"
        
        # Get tag name if available
        try:
            tag_name = element.name
        except AttributeError:
            tag_name = "Unknown"
        
        # Format value
        if element.VR == 'SQ':  # Sequence
            label = f"{tag_str} {tag_name} [SQ] ({len(element.value)} items)"
            seq_node = parent.add(label, expand=False)
            
            # Add sequence items
            for i, item in enumerate(element.value):
                item_node = seq_node.add(f"Item {i+1}", expand=False)
                for sub_elem in item:
                    self.add_element_to_tree(item_node, sub_elem, path + [element.tag, i])
        else:
            # Regular data element - store in tag_map for editing
            try:
                value_str = str(element.value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                # Escape markup characters to prevent interpretation
                value_str = value_str.replace("[", r"\[").replace("]", r"\]")
            except:
                value_str = "<unable to display value>"
            
            label = f"{tag_str} {tag_name} [{element.VR}]: {value_str}"
            node = parent.add_leaf(label)
            
            # Store tag info for editing (only for non-sequence elements)
            # Don't allow slice-specific tags to be editable when multiple files are loaded
            if (element.VR not in ['SQ'] and 
                self.is_editable_tag(element) and
                not (len(self.dicom_files) > 1 and self.is_slice_specific_tag(element.tag))):
                self.tag_map[node] = {
                    'element': element,
                    'tag': element.tag,
                    'name': tag_name,
                    'vr': element.VR,
                    'path': path
                }
    
    def is_editable_tag(self, element) -> bool:
        """Check if a DICOM tag is safe to edit."""
        # Don't allow editing of critical DICOM structure tags
        critical_tags = {
            (0x0002, 0x0000),  # File Meta Information Group Length
            (0x0002, 0x0001),  # File Meta Information Version
            (0x0002, 0x0002),  # Media Storage SOP Class UID
            (0x0002, 0x0003),  # Media Storage SOP Instance UID
            (0x0002, 0x0010),  # Transfer Syntax UID
            (0x0008, 0x0016),  # SOP Class UID
            (0x0008, 0x0018),  # SOP Instance UID
        }
        return element.tag not in critical_tags and element.VR in ['CS', 'LO', 'LT', 'PN', 'SH', 'ST', 'UT', 'DS', 'IS', 'AS', 'DA', 'DT', 'TM']
    
    def is_slice_specific_tag(self, tag) -> bool:
        """Check if a tag contains slice-specific information that shouldn't be bulk edited."""
        # Convert tag to tuple format for comparison
        if hasattr(tag, 'group') and hasattr(tag, 'element'):
            tag_tuple = (tag.group, tag.element)
        else:
            tag_tuple = tag
            
        slice_specific_tags = {
            (0x0018, 0x5100),  # Patient Position
            (0x0020, 0x0032),  # Image Position (Patient)
            (0x0020, 0x0037),  # Image Orientation (Patient)
            (0x0020, 0x1041),  # Slice Location
            (0x0020, 0x0013),  # Instance Number
            (0x0020, 0x0012),  # Acquisition Number
            (0x0008, 0x0032),  # Acquisition Time
            (0x0008, 0x0033),  # Content Time
            (0x0018, 0x0050),  # Slice Thickness
            (0x0028, 0x1050),  # Window Center
            (0x0028, 0x1051),  # Window Width
            (0x0020, 0x1002),  # Images in Acquisition
        }
        return tag_tuple in slice_specific_tags
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        if self.show_image:
            tree = self.query_one("#dicom_tree_split", Tree)
        else:
            tree = self.query_one("#dicom_tree_full", Tree)
        tree.action_cursor_down()
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        if self.show_image:
            tree = self.query_one("#dicom_tree_split", Tree)
        else:
            tree = self.query_one("#dicom_tree_full", Tree)
        tree.action_cursor_up()
    
    def action_toggle_node(self) -> None:
        """Toggle the current node."""
        if self.show_image:
            tree = self.query_one("#dicom_tree_split", Tree)
        else:
            tree = self.query_one("#dicom_tree_full", Tree)
        tree.action_toggle_node()
    
    def action_prev_file(self) -> None:
        """Navigate to previous DICOM file."""
        if len(self.dicom_files) > 1:
            self.current_index = (self.current_index - 1) % len(self.dicom_files)
            self.switch_to_current_file()
            if self.show_image:
                self.populate_split_tree()
                # Delay image update to render after tree
                self.call_later(self.update_image_view)
            else:
                self.populate_tree()
            self.update_title()
    
    def action_next_file(self) -> None:
        """Navigate to next DICOM file."""
        if len(self.dicom_files) > 1:
            self.current_index = (self.current_index + 1) % len(self.dicom_files)
            self.switch_to_current_file()
            if self.show_image:
                self.populate_split_tree()
                # Delay image update to render after tree
                self.call_later(self.update_image_view)
            else:
                self.populate_tree()
            self.update_title()
    
    def switch_to_current_file(self) -> None:
        """Switch to the current file, using cached dataset if available."""
        if len(self.dicom_files) > 1 and self.current_file in self.all_datasets:
            # Use the already loaded (and potentially modified) dataset
            self.dataset = self.all_datasets[self.current_file]
        else:
            # Load fresh (for single file mode)
            self.load_dicom_file()
    
    def action_edit_tag(self) -> None:
        """Edit the currently selected DICOM tag."""
        if self.show_image:
            tree = self.query_one("#dicom_tree_split", Tree)
        else:
            tree = self.query_one("#dicom_tree_full", Tree)
        selected_node = tree.cursor_node
        
        if selected_node in self.tag_map:
            tag_info = self.tag_map[selected_node]
            current_value = str(tag_info['element'].value)
            tag_display = f"({tag_info['tag'].group:04X},{tag_info['tag'].element:04X}) {tag_info['name']}"
            
            # Check if this is bulk editing mode
            is_bulk = len(self.dicom_files) > 1
            bulk_info = ""
            
            if is_bulk:
                is_consistent, consistency_info = self.is_tag_consistent_across_files(tag_info['tag'])
                if is_consistent:
                    bulk_info = f"Will update {len(self.dicom_files)} files (same value)"
                else:
                    bulk_info = f"Will update {len(self.dicom_files)} files ({consistency_info})"
            
            # Show edit dialog
            edit_screen = EditTagScreen(tag_info['name'], current_value, tag_display, is_bulk, bulk_info)
            self.push_screen(edit_screen, self.handle_edit_result)
    
    def handle_edit_result(self, new_value: str) -> None:
        """Handle the result from the edit dialog."""
        if new_value is not None:
            if self.show_image:
                tree = self.query_one("#dicom_tree_split", Tree)
            else:
                tree = self.query_one("#dicom_tree_full", Tree)
            selected_node = tree.cursor_node
            
            if selected_node in self.tag_map:
                tag_info = self.tag_map[selected_node]
                current_value = str(tag_info['element'].value)
                
                if new_value != current_value:
                    try:
                        # Convert value based on VR
                        converted_value = self.convert_value_for_vr(new_value, tag_info['vr'])
                        
                        if len(self.dicom_files) > 1:
                            # Bulk update across all files
                            self.bulk_update_tag(tag_info['tag'], converted_value, tag_info['vr'])
                        else:
                            # Single file update
                            tag_info['element'].value = converted_value
                        
                        self.has_changes = True
                        
                        # Refresh the tree display
                        if self.show_image:
                            self.populate_split_tree()
                        else:
                            self.populate_tree()
                        self.update_title()
                        
                    except Exception as e:
                        # Could add error notification here
                        pass
    
    def action_toggle_sixel(self) -> None:
        """Toggle between Unicode blocks and sixel graphics display."""
        if not self.sixel_supported:
            self.notify("Sixel graphics not supported in this terminal")
            return
            
        if not self.show_image:
            self.notify("Switch to image view first (press 'i')")
            return
            
        # Toggle sixel mode
        self.use_sixel = not self.use_sixel
        
        # Update the image view with new display mode
        self.update_image_view()
        
        mode = "sixel graphics" if self.use_sixel else "Unicode blocks"
        self.notify(f"Switched to {mode} display")
    
    def action_view_image(self) -> None:
        """Toggle between full tag view and split view (tags + image)."""
        if not hasattr(self.dataset, 'pixel_array'):
            self.notify("No pixel data available in this DICOM file")
            return
            
        # Toggle the view
        self.show_image = not self.show_image
        
        # Get both containers
        full_container = self.query_one("#full_container")
        split_container = self.query_one("#split_container")
        
        if self.show_image:
            # Show split view, hide full view
            full_container.add_class("hidden")
            split_container.remove_class("hidden")
            # Populate both trees and update image
            self.populate_split_tree()
            # Delay image update to render after tree
            self.call_later(self.update_image_view)
        else:
            # Show full view, hide split view
            split_container.add_class("hidden")
            full_container.remove_class("hidden")
            # Populate full tree
            self.populate_tree()
    
    def update_image_view(self):
        """Update the image view with current dataset and windowing."""
        try:
            if hasattr(self.dataset, 'pixel_array'):
                if self.use_sixel and self.sixel_supported and TextualImage:
                    # Use TextualImage widget for sixel display
                    pil_image = self.get_pil_image_for_display()
                    if pil_image:
                        # Use DICOM SOP Instance UID as unique ID
                        try:
                            sop_instance_uid = str(self.dataset.SOPInstanceUID).replace('.', '_')
                            unique_id = f"textual_image_{sop_instance_uid}"
                        except:
                            # Fallback to filename if UID not available
                            unique_id = f"textual_image_{self.current_file.stem}"
                        
                        image_container = self.query_one("#image_container")
                        
                        # Check if widget with this ID already exists
                        try:
                            existing_widget = image_container.query_one(f"#{unique_id}")
                            # Widget exists, remove it and create new one with updated image
                            existing_widget.remove()
                        except:
                            # Widget doesn't exist, just clean up any other TextualImage widgets
                            existing_widgets = image_container.query("*")
                            for widget in existing_widgets:
                                if isinstance(widget, TextualImage):
                                    widget.remove()
                        
                        # Add a small delay to ensure widget removal is complete
                        # This helps with the timing issue where first windowing change doesn't work
                        unicode_widget = self.query_one("#unicode_image")
                        self.call_later(lambda: self._mount_textual_image(image_container, unicode_widget, pil_image, unique_id))
                    else:
                        content = "Error creating PIL image for display"
                        self.query_one("#unicode_image", Static).update(content)
                else:
                    # Use unicode blocks
                    content = self.pixel_array_to_unicode()
                    self.query_one("#unicode_image", Static).update(content)
                    # Remove any textual image widgets
                    if TextualImage:
                        image_container = self.query_one("#image_container")
                        existing_widgets = image_container.query("*")
                        for widget in existing_widgets:
                            if isinstance(widget, TextualImage):
                                widget.remove()
            else:
                content = "No pixel data available in this DICOM file"
                self.query_one("#unicode_image", Static).update(content)
        except Exception as e:
            content = f"Error loading pixel data: {str(e)}"
            self.query_one("#unicode_image", Static).update(content)
        
        # Create windowing info
        preset_name, window_width, window_center = self.window_presets[self.current_preset]
        if window_width is not None and window_center is not None:
            window_info = f"Window: {preset_name} (W:{window_width} / L:{window_center})"
        else:
            window_info = f"Window: {preset_name}"
        
        # Add display mode info
        if self.sixel_supported:
            display_mode = "sixel" if self.use_sixel else "blocks"
            window_info += f" | Display: {display_mode}"
        
        # Create help text
        help_text = "i to toggle view • w/s to change windowing"
        if self.sixel_supported:
            help_text += " • x to toggle sixel/blocks"
        if len(self.dicom_files) > 1:
            current_idx = self.current_index + 1
            total_files = len(self.dicom_files)
            help_text += f" • h/l or ←/→ to navigate ({current_idx}/{total_files})"
        
        # Update the widgets
        self.query_one("#image_header", Static).update(f"DICOM Image: {self.current_file.name}")
        self.query_one("#window_info", Static).update(window_info)
        self.query_one("#image_help", Static).update(help_text)
    
    def _mount_textual_image(self, image_container, unicode_widget, pil_image, unique_id):
        """Helper method to mount TextualImage widget with delay."""
        # Create new TextualImage widget with the PIL image
        new_image_widget = TextualImage(pil_image, id=unique_id)
        
        # Insert the new widget at the right position
        image_container.mount(new_image_widget, after=unicode_widget)
        
        # Hide unicode image when using sixel
        self.query_one("#unicode_image", Static).update("")
    
    def get_pil_image_for_display(self):
        """Get PIL image for display in TextualImage widget, sized for current terminal."""
        try:
            if Image is None:
                return None
            
            # Let the TextualImage widget handle sizing via CSS
            # Use generous max dimensions and let the widget scale appropriately
            max_width = 1200  # Large enough for good quality
            max_height = 900   # Large enough for good quality
            
            # Get pixel array
            pixel_array = self.dataset.pixel_array
            
            # Handle different array dimensions
            if len(pixel_array.shape) > 2:
                # For multi-slice or RGB images, take the first slice/channel
                if len(pixel_array.shape) == 3:
                    if pixel_array.shape[0] < pixel_array.shape[2]:  # Likely (slices, height, width)
                        pixel_array = pixel_array[0]
                    else:  # Likely (height, width, channels)
                        pixel_array = pixel_array[:, :, 0]
                elif len(pixel_array.shape) == 4:
                    pixel_array = pixel_array[0, 0]  # Take first slice and channel
            
            # Convert to Hounsfield Units if DICOM rescaling info is available
            pixel_array = self.apply_dicom_rescaling(pixel_array)
            
            # Apply windowing based on current preset
            pixel_array = self.apply_windowing(pixel_array)
            
            # Create PIL image
            img = Image.fromarray(pixel_array, mode='L')
            
            # Resize to fit display while maintaining aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            return None
    
    def pixel_array_to_unicode(self, size=50):
        """Convert DICOM pixel array to Unicode block representation."""
        try:
            if Image is None:
                return "PIL (Pillow) library not available. Install with: uv add pillow"
            
            # Get pixel array
            pixel_array = self.dataset.pixel_array
            
            # Handle different array dimensions
            if len(pixel_array.shape) > 2:
                # For multi-slice or RGB images, take the first slice/channel
                if len(pixel_array.shape) == 3:
                    if pixel_array.shape[0] < pixel_array.shape[2]:  # Likely (slices, height, width)
                        pixel_array = pixel_array[0]
                    else:  # Likely (height, width, channels)
                        pixel_array = pixel_array[:, :, 0]
                elif len(pixel_array.shape) == 4:
                    pixel_array = pixel_array[0, 0]  # Take first slice and channel
            
            # Convert to Hounsfield Units if DICOM rescaling info is available
            pixel_array = self.apply_dicom_rescaling(pixel_array)
            
            # Apply windowing based on current preset
            pixel_array = self.apply_windowing(pixel_array)
            
            # Use square dimensions for better resolution and consistent display
            # Size 50x50 fits well in most terminal windows while maintaining good detail
            new_width = new_height = size
            
            # Resize using PIL with high-quality resampling
            img = Image.fromarray(pixel_array, mode='L')
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_array = np.array(img)
            
            # Extended Unicode block characters for better detail
            # Using 8 levels for much finer gradation
            blocks = [' ', '░', '▒', '▓', '█', '▉', '▊', '▋']
            
            # Convert to block indices with finer granularity
            block_indices = (resized_array // 32).clip(0, 7)  # 255/8 ≈ 32
            
            # Build Unicode block image
            lines = []
            for row in block_indices:
                line = ''.join(blocks[idx] for idx in row)
                lines.append(line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"Error converting pixel data: {str(e)}"
    
    def pixel_array_to_sixel(self, max_width=400, max_height=300):
        """Convert DICOM pixel array to sixel graphics output."""
        try:
            if libsixel is None:
                return "libsixel library not available. Install with: uv add libsixel-python"
            
            if Image is None:
                return "PIL (Pillow) library not available. Install with: uv add pillow"
            
            # Get pixel array
            pixel_array = self.dataset.pixel_array
            
            # Handle different array dimensions
            if len(pixel_array.shape) > 2:
                # For multi-slice or RGB images, take the first slice/channel
                if len(pixel_array.shape) == 3:
                    if pixel_array.shape[0] < pixel_array.shape[2]:  # Likely (slices, height, width)
                        pixel_array = pixel_array[0]
                    else:  # Likely (height, width, channels)
                        pixel_array = pixel_array[:, :, 0]
                elif len(pixel_array.shape) == 4:
                    pixel_array = pixel_array[0, 0]  # Take first slice and channel
            
            # Convert to Hounsfield Units if DICOM rescaling info is available
            pixel_array = self.apply_dicom_rescaling(pixel_array)
            
            # Apply windowing based on current preset
            pixel_array = self.apply_windowing(pixel_array)
            
            # Create PIL image
            img = Image.fromarray(pixel_array, mode='L')
            
            # Resize to fit terminal while maintaining aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB for sixel output
            img_rgb = img.convert('RGB')
            
            # Convert PIL image to sixel
            from libsixel.encoder import Encoder
            
            encoder = Encoder()
            
            # Convert image to bytes
            img_bytes = img_rgb.tobytes()
            
            # Position cursor to right side for split view
            # Use raw string to avoid Textual markup interpretation
            move_cursor = r"\033[10;60H"  # Move cursor to row 10, column 60 (right side)
            
            # Encode to sixel using encode_bytes method
            result = encoder.encode_bytes(img_bytes, img_rgb.width, img_rgb.height, 
                                        libsixel.SIXEL_PIXELFORMAT_RGB888, None)
            
            return move_cursor + (result if result else "")
            
        except Exception as e:
            return f"Error converting pixel data to sixel: {str(e)}"
    
    def apply_dicom_rescaling(self, pixel_array):
        """Apply DICOM rescale slope and intercept to convert to Hounsfield Units."""
        try:
            # Get rescale slope and intercept from DICOM header
            rescale_slope = getattr(self.dataset, 'RescaleSlope', 1.0)
            rescale_intercept = getattr(self.dataset, 'RescaleIntercept', 0.0)
            
            # Convert to float for calculation
            pixel_array = pixel_array.astype(np.float32)
            
            # Apply DICOM rescaling formula: HU = pixel_value * slope + intercept
            hounsfield_array = pixel_array * rescale_slope + rescale_intercept
            
            return hounsfield_array
            
        except Exception:
            # If rescaling fails, return original array
            return pixel_array.astype(np.float32)
    
    def apply_windowing(self, pixel_array):
        """Apply DICOM windowing to pixel array (assumed to be in Hounsfield Units)."""
        preset_name, window_width, window_center = self.window_presets[self.current_preset]
        
        if preset_name == "Auto" or window_width is None:
            # Auto windowing - use full range of the actual data
            pixel_min, pixel_max = pixel_array.min(), pixel_array.max()
            if pixel_max > pixel_min:
                windowed = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
            else:
                windowed = np.zeros_like(pixel_array, dtype=np.uint8)
        else:
            # Apply standard DICOM windowing formula
            # pixel_array should now be in Hounsfield Units
            lower_bound = window_center - window_width / 2.0
            upper_bound = window_center + window_width / 2.0
            
            # Clip to window bounds
            windowed_float = np.clip(pixel_array, lower_bound, upper_bound)
            
            # Normalize to 0-255 range
            if upper_bound > lower_bound:
                windowed_float = (windowed_float - lower_bound) / (upper_bound - lower_bound) * 255.0
            else:
                windowed_float = np.zeros_like(windowed_float)
                
            windowed = windowed_float.astype(np.uint8)
        
        return windowed
    
    def on_key(self, event) -> None:
        """Handle key events, including windowing controls in image view."""
        if self.show_image and event.key in ("w", "s"):
            # Handle windowing changes in image view
            if event.key == "w":
                self.current_preset = (self.current_preset + 1) % len(self.window_presets)
            else:  # "s"
                self.current_preset = (self.current_preset - 1) % len(self.window_presets)
            # Refresh the image with new windowing
            self.update_image_view()
            event.prevent_default()
        # For other keys, let the normal key bindings handle them
    
    def bulk_update_tag(self, tag, new_value, vr: str) -> None:
        """Update a tag value across all loaded DICOM files."""
        for file_path, dataset in self.all_datasets.items():
            try:
                if tag in dataset and self.is_editable_tag(dataset[tag]):
                    dataset[tag].value = new_value
            except Exception:
                # Skip files where update fails
                pass
        
        # Also update the current displayed dataset if it's from the all_datasets cache
        if len(self.dicom_files) > 1 and self.current_file in self.all_datasets:
            self.dataset = self.all_datasets[self.current_file]
    
    def convert_value_for_vr(self, value: str, vr: str):
        """Convert string value to appropriate type based on VR."""
        if vr in ['DS']:  # Decimal String
            return float(value) if value else 0.0
        elif vr in ['IS']:  # Integer String
            return int(value) if value else 0
        elif vr in ['AS']:  # Age String
            return value.strip()
        elif vr in ['DA']:  # Date
            return value.strip()
        elif vr in ['DT']:  # DateTime
            return value.strip()
        elif vr in ['TM']:  # Time
            return value.strip()
        else:  # String types
            return value.strip()
    
    def action_save_file(self) -> None:
        """Save changes to the DICOM file(s)."""
        if self.has_changes:
            try:
                import shutil
                backup_files = []
                
                if len(self.dicom_files) > 1:
                    # Bulk save all modified files
                    for file_path, dataset in self.all_datasets.items():
                        # Create backup
                        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                        if not backup_path.exists():
                            shutil.copy2(file_path, backup_path)
                            backup_files.append(backup_path)
                        
                        # Save the DICOM file
                        dataset.save_as(str(file_path))
                else:
                    # Single file save
                    backup_path = self.current_file.with_suffix(self.current_file.suffix + '.bak')
                    if not backup_path.exists():
                        shutil.copy2(self.current_file, backup_path)
                        backup_files.append(backup_path)
                    
                    # Save the DICOM file
                    self.dataset.save_as(str(self.current_file))
                
                # Clean up backup files after successful save
                self.cleanup_backup_files(backup_files)
                
                self.has_changes = False
                self.update_title()
                
            except Exception as e:
                # Don't clean up backups if save failed
                pass
    
    def cleanup_backup_files(self, backup_files: List[Path]) -> None:
        """Remove backup files after successful save."""
        for backup_path in backup_files:
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except Exception:
                # If we can't delete backup, that's okay - leave it for safety
                pass


def is_dicom_file(file_path: Path) -> bool:
    """Check if a file is a DICOM file by trying to read it."""
    try:
        pydicom.dcmread(str(file_path), stop_before_pixels=True)
        return True
    except:
        return False


def get_instance_number(file_path: Path) -> int:
    """Get the Instance Number from a DICOM file for sorting."""
    try:
        dataset = pydicom.dcmread(str(file_path), stop_before_pixels=True)
        # Try Instance Number first
        if hasattr(dataset, 'InstanceNumber') and dataset.InstanceNumber is not None:
            return int(dataset.InstanceNumber)
        # Fallback to Slice Location if available
        elif hasattr(dataset, 'SliceLocation') and dataset.SliceLocation is not None:
            return int(float(dataset.SliceLocation) * 1000)  # Convert to int for sorting
        # Fallback to filename as last resort
        else:
            return 999999
    except:
        # If we can't read the DICOM or get instance number, use filename ordering
        return 999999


def find_dicom_files(path: Path) -> List[Path]:
    """Find all DICOM files in a directory or return single file if it's a DICOM."""
    if path.is_file():
        if is_dicom_file(path):
            return [path]
        else:
            print(f"Error: '{path}' is not a valid DICOM file.")
            sys.exit(1)
    elif path.is_dir():
        dicom_files = []
        for file_path in path.iterdir():
            if file_path.is_file() and is_dicom_file(file_path):
                dicom_files.append(file_path)
        
        if not dicom_files:
            print(f"Error: No DICOM files found in '{path}'.")
            sys.exit(1)
        
        # Sort by Instance Number for proper slice ordering
        return sorted(dicom_files, key=get_instance_number)
    else:
        print(f"Error: '{path}' does not exist.")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python dicom_cli.py <dicom_file_or_folder>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    dicom_files = find_dicom_files(path)
    
    if len(dicom_files) > 1:
        print(f"Found {len(dicom_files)} DICOM files. Use h/l or left/right arrows to navigate.")
    
    app = DicomTreeApp(dicom_files)
    app.run()


if __name__ == "__main__":
    main()