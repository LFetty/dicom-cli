#!/usr/bin/env python3
"""Test DICOM file sorting by Instance Number."""

import pydicom
from pathlib import Path

def test_instance_numbers():
    """Check Instance Numbers in the test DICOM files."""
    dicom_dir = Path("test-data/DICOM")
    
    if not dicom_dir.exists():
        print("Test DICOM directory not found")
        return
    
    files_with_instance = []
    
    for file_path in dicom_dir.iterdir():
        if file_path.is_file():
            try:
                dataset = pydicom.dcmread(str(file_path), stop_before_pixels=True)
                instance_num = getattr(dataset, 'InstanceNumber', None)
                slice_loc = getattr(dataset, 'SliceLocation', None)
                
                files_with_instance.append({
                    'file': file_path.name,
                    'instance': instance_num,
                    'slice_location': slice_loc
                })
            except Exception as e:
                print(f"Error reading {file_path.name}: {e}")
    
    # Sort by instance number
    files_with_instance.sort(key=lambda x: x['instance'] if x['instance'] is not None else 999999)
    
    print("DICOM files sorted by Instance Number:")
    print("-" * 60)
    for item in files_with_instance[:10]:  # Show first 10
        print(f"File: {item['file'][:35]:35} | Instance: {item['instance']:3} | Slice: {item['slice_location']}")

if __name__ == "__main__":
    test_instance_numbers()