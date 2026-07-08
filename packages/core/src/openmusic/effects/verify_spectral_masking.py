"""Verification script for Spectral Masking Avoidance.

This script directly imports the class and verifies basic functionality.
"""

import sys
import numpy as np

# Add src to path
sys.path.insert(0, "src")

print("=" * 60)
print("VERIFYING: Spectral Masking Avoidance imports...")

try:
    from openmusic.effects.spectral_masking_avoidance import (
        SpectralMaskingAvoidance,
    )

    print("✓ Import successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Verify class structure
print("=" * 60)
effect = SpectralMaskingAvoidance()
print(f"  Effect name: {effect.name}")

# Verify process method exists
if hasattr(effect, "process"):
    print("✓ process method exists")
else:
    print("✗ process method missing")
    sys.exit(1)

print("=" * 60)
print("VERIFICATION COMPLETE")

# Test basic functionality
print("=" * 60)
try:
    audio = np.sin(2 * np.pi * np.arange(48000) / 48000 * 440)
    params = {
        "sensitivity": 50.0,
        "max_cut_db": 6.0,
        "sample_rate": 48000,
    }
    result = effect.process(audio, params)
    print(f"✓ Process call successful, output shape: {result.shape}")
    assert result.shape == audio.shape, "Output shape mismatch"
    assert np.all(np.isfinite(result)), "Non-finite values in output"
except Exception as e:
    print(f"✗ Process call failed: {e}")
    sys.exit(1)

print("=" * 60)
print("All tests PASSED")
