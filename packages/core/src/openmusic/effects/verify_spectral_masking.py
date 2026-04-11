"""Verification script for Spectral Masking Avoidance.

This script directly imports the class and verifies basic functionality.
"""

import numpy as np
import sys

# Add src to path
sys.path.append("C:\\Users\\Tobias\\git\\openmusic\\packages\\core\\src")

print("=" * 60)
print("VERIFYING: Spectral Masking Avoidance imports...")

# Import class directly
print("=" * 60)
try:
    # Import SpectralMaskingAvoidance class
    from spectral_masking_avoidance import SpectralMaskingAvoidance

    # Check if import works
    print("✓ Import successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Verify class structure
print("=" * 60)
try:
    # Check class name
    print(f"Class name: {SpectralMaskingAvoidance.name}")
except Exception as e:
    print(f"✗ Class structure check failed: {e}")

# Verify method exists
print("=" * 60)
try:
    # Check if process method exists
    if hasattr(SpectralMaskingAvoidance, "process"):
        print("✓ process method exists")
    else:
        print(f"✗ process method missing")
        sys.exit(1)
except Exception as e:
    print(f"✗ process method check failed: {e}")
    sys.exit(1)

print("=" * 60)
print("VERIFICATION COMPLETE")

# Test basic functionality
print("=" * 60)
try:
    # Create dummy audio and params
    audio = np.sin(2 * np.pi * np.arange(48000))
    params = {
        "target_frequencies": [20.0, 400, 800, 2000],
        "filter_order": "peak",
        "depth": 50.0,
        "sample_rate": 48000,
    }

    # Call process
    result = spectral_masking_avoidance.process(audio, params)
    print(f"✓ Process call successful")
except Exception as e:
    print(f"✗ Process call failed: {e}")
    sys.exit(1)

print("Test PASSED")
