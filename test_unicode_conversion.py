#!/usr/bin/env python3
"""Test Unicode block conversion."""

import pydicom
import numpy as np
from PIL import Image
from pathlib import Path

def pixel_array_to_unicode(pixel_array, size=80):
    """Convert DICOM pixel array to Unicode block representation."""
    try:
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
        
        # Convert to PIL Image for easy resizing
        # Normalize to 0-255 range
        if pixel_array.dtype != np.uint8:
            pixel_min, pixel_max = pixel_array.min(), pixel_array.max()
            if pixel_max > pixel_min:
                pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
            else:
                pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)
        
        # Use square dimensions for better resolution and consistent display
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

def test_conversion():
    """Test the Unicode conversion."""
    test_file = Path("test-data/DICOM/CT.1.3.46.423632.338406202461915032530.27")
    
    try:
        dataset = pydicom.dcmread(str(test_file))
        pixel_array = dataset.pixel_array
        
        print("Converting to Unicode blocks...")
        unicode_image = pixel_array_to_unicode(pixel_array, size=60)
        
        print("\nUnicode block representation:")
        print(unicode_image)
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_conversion()