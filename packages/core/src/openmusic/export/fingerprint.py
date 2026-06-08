"""Audio fingerprinting using Chromaprint and AcoustID lookup.

Requires libchromaprint system library:
Ubuntu/Debian: apt install libchromaprint-dev
macOS: brew install chromaprint
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

import soundfile as sf

logger = logging.getLogger(__name__)


class FingerprintError(Exception):
    """Raised when fingerprinting fails."""


def generate_fingerprint(audio_path: str) -> str:
    """Generate a Chromaprint audio fingerprint from an audio file.

    Uses the fpcalc command-line tool (from chromaprint) to calculate
    the fingerprint.

    Args:
        audio_path: Path to an audio file.

    Returns:
        Compressed fingerprint string.

    Raises:
        FingerprintError: If the file doesn't exist or fpcalc fails.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FingerprintError(f"Audio file not found: {audio_path}")

    try:
        result = subprocess.run(
            ["fpcalc", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise FingerprintError(
            "fpcalc not found. Install chromaprint: "
            "apt install libchromaprint-dev / brew install chromaprint"
        )
    except subprocess.TimeoutExpired:
        raise FingerprintError("fpcalc timed out processing audio file")

    if result.returncode != 0:
        raise FingerprintError(
            f"fpcalc failed: {result.stderr.strip()}"
        )

    for line in result.stdout.splitlines():
        if line.startswith("FINGERPRINT="):
            return line.split("=", 1)[1].strip()

    raise FingerprintError("No fingerprint in fpcalc output")


def lookup_acoustid(
    audio_path: str,
    api_key: str,
    meta: str = "recordings",
) -> Optional[dict[str, Any]]:
    """Look up an audio file on AcoustID using its fingerprint.

    This is a placeholder that requires pyacoustid for actual API access.
    The AcoustID API is at https://api.acoustid.org/v2/lookup.

    Args:
        audio_path: Path to audio file.
        api_key: AcoustID API key.
        meta: Metadata type to request.

    Returns:
        API response dict, or None if lookup fails.
    """
    fingerprint = generate_fingerprint(audio_path)

    info = sf.info(audio_path)
    duration = info.duration

    try:
        import acoustid  # type: ignore[import-untyped]

        return acoustid.lookup(api_key, fingerprint, duration, meta=meta)
    except ImportError:
        logger.warning(
            "pyacoustid not installed. Install with: pip install pyacoustid>=1.3.0"
        )
        return None
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error("AcoustID lookup failed: %s", e)
        return {"error": str(e)}
