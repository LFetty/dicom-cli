#!/usr/bin/env python3
"""Test script to verify image viewing functionality."""

import pydicom
from pathlib import Path
import sys

def test_pixel_access():
    """Test if we can access pixel data from DICOM files."""
    test_file = Path("test-data/DICOM/CT.1.3.46.423632.338406202461915032530.27")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return False
    
    try:
        # Load DICOM file
        dataset = pydicom.dcmread(str(test_file))
        print(f"Loaded DICOM file: {test_file.name}")
        
        # Check if pixel data exists
        if hasattr(dataset, 'pixel_array'):
            pixel_array = dataset.pixel_array
            print(f"Pixel array shape: {pixel_array.shape}")
            print(f"Pixel array dtype: {pixel_array.dtype}")
            print(f"Pixel value range: {pixel_array.min()} to {pixel_array.max()}")
            return True
        else:
            print("No pixel_array attribute found")
            return False
            
    except Exception as e:
        print(f"Error loading DICOM: {e}")
        return False

if __name__ == "__main__":
    success = test_pixel_access()
    sys.exit(0 if success else 1)