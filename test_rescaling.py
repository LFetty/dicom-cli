#!/usr/bin/env python3
"""Test DICOM rescaling to Hounsfield Units."""

import pydicom
import numpy as np
from pathlib import Path

def test_dicom_rescaling():
    """Test DICOM rescaling parameters."""
    test_file = Path("test-data/DICOM/CT.1.3.46.423632.338406202461915032530.27")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    try:
        dataset = pydicom.dcmread(str(test_file))
        pixel_array = dataset.pixel_array
        
        # Check rescaling parameters
        rescale_slope = getattr(dataset, 'RescaleSlope', None)
        rescale_intercept = getattr(dataset, 'RescaleIntercept', None)
        
        print(f"Original pixel array:")
        print(f"  Shape: {pixel_array.shape}")
        print(f"  Data type: {pixel_array.dtype}")
        print(f"  Min value: {pixel_array.min()}")
        print(f"  Max value: {pixel_array.max()}")
        print(f"  Sample values: {pixel_array[250:255, 250:255].flatten()}")
        
        print(f"\nDICOM Rescaling Parameters:")
        print(f"  Rescale Slope: {rescale_slope}")
        print(f"  Rescale Intercept: {rescale_intercept}")
        
        if rescale_slope is not None and rescale_intercept is not None:
            # Apply rescaling
            hounsfield_array = pixel_array.astype(np.float32) * rescale_slope + rescale_intercept
            
            print(f"\nAfter rescaling to Hounsfield Units:")
            print(f"  Min HU: {hounsfield_array.min()}")
            print(f"  Max HU: {hounsfield_array.max()}")
            print(f"  Sample HU values: {hounsfield_array[250:255, 250:255].flatten()}")
            
            # Check if we have proper CT range
            if hounsfield_array.min() < -500:
                print("✓ Proper CT range detected (includes air ~-1000 HU)")
            else:
                print("⚠ Unusual CT range - may not be properly rescaled")
        else:
            print("⚠ No rescaling parameters found in DICOM")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dicom_rescaling()