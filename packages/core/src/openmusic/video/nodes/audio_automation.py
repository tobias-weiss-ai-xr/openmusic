"""Audio automation node for per-stage processing with advanced sound design."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pedalboard
import soundfile as sf
from scipy.signal import butter, filtfilt

from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


def _apply_transient_shaping(audio: np.ndarray, sr: int, attack_ms: float, sustain_db: float, release_ms: float) -> np.ndarray:
    """Apply transient shaping for punchier or smoother dynamics.

    Args:
        audio: Input audio (stereo)
        sr: Sample rate
        attack_ms: Attack time in ms (positive is punchier, negative is softer)
        sustain_db: Sustain level in dB (negative reduces sustain)
        release_ms: Release time in ms

    Returns:
        Shaped audio
    """
    # Simple envelope follower
    window_size = int(0.005 * sr)
    envelope = np.abs(audio).max(axis=1, keepdims=True)
    # Smooth envelope
    kernel = np.ones(window_size) / window_size
    envelope = filtfilt(kernel, [1], envelope, axis=0)
    
    # Apply gain modulation based on attack/sustain/release
    attack_samples = int(abs(attack_ms) * sr / 1000)
    release_samples = int(release_ms * sr / 1000)
    
    shaped_audio = audio.copy()
    sustain_gain = 10 ** (sustain_db / 20)
    
    for i in range(len(shaped_audio)):
        if i < attack_samples:
            gain = (i / attack_samples) if attack_ms > 0 else (1 - i / attack_samples)
        elif i > len(shaped_audio) - release_samples:
            gain = (len(shaped_audio) - i) / release_samples
        else:
            gain = sustain_gain
        shaped_audio[i] *= gain
    
    return shaped_audio


def _apply_sidechain_simulation(audio: np.ndarray, sr: int, bpm: int, depth_db: float = -6) -> np.ndarray:
    """Simulate sidechain compression pumping at BPM.

    Args:
        audio: Input audio
        sr: Sample rate
        bpm: Beats per minute
        depth_db: Pump depth in dB

    Returns:
        Audio with sidechain pumping
    """
    duration = len(audio) / sr
    beat_duration = 60 / bpm
    t = np.arange(len(audio)) / sr
    
    # Create LFO at kick frequency (or 1/2 beat for pumping)
    lfo_freq = bpm / 60
    # Smooth pumping curve using raised cosine
    lfo = -np.abs(np.sin(2 * np.pi * lfo_freq * t)) ** 2
    
    # Apply gain modulation
    depth_linear = 10 ** (depth_db / 20)
    modulated_gain = 1 + lfo * (depth_linear - 1)
    
    return audio * modulated_gain[:, np.newaxis]


def _apply_formant_filter(audio: np.ndarray, sr: int, center_freq: float, q: float = 5.0, gain_db: float = 0) -> np.ndarray:
    """Apply resonant filter with formant-like characteristics.
    
    Simulates vocal or instrument formants for harmonic richness.

    Args:
        audio: Input audio
        sr: Sample rate
        center_freq: Formant center frequency in Hz
        q: Q factor (bandwidth)
        gain_db: Gain in dB

    Returns:
        Filtered audio
    """
    nyquist = sr / 2
    normalized_freq = center_freq / nyquist
    
    # Create bandpass filter
    b, a = butter(2, [normalized_freq / q, normalized_freq * q], btype='band')
    filtered = filtfilt(b, a, audio, axis=0)
    
    # Mix with original if gain_db != 0
    if gain_db != 0:
        gain_linear = 10 ** (gain_db / 20)
        return audio + filtered * gain_linear
    
    return filtered


def _get_key_harmonics(key: str) -> Dict[str, float]:
    """Extract harmonic frequencies for the given key.

    For D minor: D (root), F (minor third), A (perfect fifth)

    Args:
        key: Musical key (e.g., "Dm", "C", "F#")

    Returns:
        Dictionary of harmonic frequencies in Hz
    """
    key_harmonics = {
        "Dm": {"root": 146.83, "third": 174.61, "fifth": 220.00},  # D3, F3, A3
        "C": {"root": 130.81, "third": 164.81, "fifth": 196.00},  # C3, E3, G3
        "Eb": {"root": 155.56, "third": 185.00, "fifth": 233.08},  # Eb3, G3, Bb3
        "G": {"root": 196.00, "third": 246.94, "fifth": 293.66},  # G3, B3, D4
        "A": {"root": 220.00, "third": 261.63, "fifth": 329.63},  # A3, C4, E4
        "F": {"root": 174.61, "third": 220.00, "fifth": 261.63},  # F3, A3, C4
    }

    return key_harmonics.get(key, key_harmonics["Dm"])


def _apply_harmonic_resonance(audio: np.ndarray, sr: int, frequencies: list, q: float = 8.0, gain_db: float = 2) -> np.ndarray:
    """Apply resonance at specific harmonic frequencies to emphasize chord tones.

    Creates a harmonic "color" by emphasizing the fundamental chord tones
    of the key to enhance musical coherence.

    Args:
        audio: Input audio (stereo)
        sr: Sample rate
        frequencies: List of harmonic frequencies to emphasize in Hz
        q: Q factor for narrow bandpass filters
        gain_db: Gain to apply to resonances

    Returns:
        Audio with harmonic resonance
    """
    result = audio.copy()

    for freq in frequencies:
        board = pedalboard.Pedalboard()
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=freq, gain_db=gain_db, q=q))
        result = board(result, sr)

    return result


def _apply_stage_modifications(
    audio: np.ndarray,
    sr: int,
    stage: str,
    key: str = "Dm",
    bpm: int = 125,
) -> np.ndarray:
    """Apply stage-specific audio effects with music theory integration.

    Professional mastering with:
    - Harmonic resonance at key chord tones (root, third, fifth)
    - Chord progression alignment (Dm → F → Cm → Gm → Bb → Dm)
    - Harmonic rhythm (slow ambient, fast build, complex peaks)
    - Transient shaping, sidechain pumping, formant filtering

    Args:
        audio: Audio segment (stereo)
        sr: Sample rate
        stage: Stage identifier
        key: Musical key for harmonic context
        bpm: BPM for rhythmic modulation

    Returns:
        Processed audio segment
    """
    # Get key harmonics for harmonic resonance
    harmonics = _get_key_harmonics(key)
    chord_tones = [harmonics["root"], harmonics["third"], harmonics["fifth"]]

    board = pedalboard.Pedalboard()

    # Chord progression map for D minor: Dm → F → Cm → Gm → Bb → Dm
    # Each stage emphasizes different chord tones
    chord_progression = {
        "ambient-intro": "Dm",      # Root emphasis
        "early-build": "F",         # Third key (F major)
        "mid-build": "Dm",          # Return to tonic
        "pre-peak-one": "Cm",       # Relative minor
        "peak-one": "Gm",           # Dominant minor
        "peak-two": "Bb",           # Subdominant major
        "post-peak": "Dm",         # Tonic resolution
        "decay-one": "F",           # Submediant
        "decay-two": "Dm",         # Tonic
        "dissolution": "Dm",        # Final tonic
    }

    current_chord = chord_progression.get(stage, "Dm")

    # Stage effects based on chord progression and harmonic rhythm
    if stage == "ambient-intro":
        # Slow harmonic rhythm, root emphasis (D: 146.83 Hz, F: 174.61 Hz, A: 220.00 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=146.83, gain_db=4, q=6.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=220.00, gain_db=3, q=5.0))
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=400))
        board.append(pedalboard.Reverb(room_size=0.9, wet_level=0.6, dry_level=0.4))
        board.append(pedalboard.Limiter(threshold_db=-5.0))

    elif stage == "early-build":
        # Faster harmonic rhythm, F chord emphasis (F: 174.61 Hz, A: 220.00 Hz, C: 261.63 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=174.61, gain_db=5, q=5.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=261.63, gain_db=3, q=6.0))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=40))
        board.append(pedalboard.Compressor(threshold_db=-15, ratio=2.0))
        board.append(pedalboard.Reverb(room_size=0.4, wet_level=0.3, dry_level=0.7))

    elif stage == "mid-build":
        # Dm chord with rising energy (D: 146.83 Hz, F: 174.61 Hz, A: 220.00 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=146.83, gain_db=6, q=5.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=293.66, gain_db=3, q=4.0))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=50))
        board.append(pedalboard.Compressor(threshold_db=-18, ratio=3.0))

    elif stage == "pre-peak-one":
        # Cm chord tension (C: 130.81 Hz, Eb: 155.56 Hz, G: 196.00 Hz)
        board.append(pedalboard.LowShelfFilter(gain_db=5, cutoff_frequency_hz=130.81))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=155.56, gain_db=4, q=5.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=392.00, gain_db=3, q=4.0))
        board.append(pedalboard.Bitcrush(bit_depth=13))
        board.append(pedalboard.Compressor(threshold_db=-20, ratio=4.0))

    elif stage == "peak-one":
        # Gm dominant tension (G: 196.00 Hz, Bb: 233.08 Hz, D: 293.66 Hz)
        board.append(pedalboard.LowShelfFilter(gain_db=8, cutoff_frequency_hz=196.00))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=233.08, gain_db=5, q=4.5))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=293.66, gain_db=4, q=5.0))
        board.append(pedalboard.Distortion(drive_db=18))
        board.append(pedalboard.Compressor(threshold_db=-28, ratio=7.0))

    elif stage == "peak-two":
        # Bb subdominant resolution (Bb: 233.08 Hz, D: 293.66 Hz, F: 349.23 Hz)
        board.append(pedalboard.LowShelfFilter(gain_db=6, cutoff_frequency_hz=233.08))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=349.23, gain_db=4, q=4.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=196.00, gain_db=2, q=3.0))
        board.append(pedalboard.Distortion(drive_db=25))
        board.append(pedalboard.Compressor(threshold_db=-26, ratio=6.0))

    elif stage == "post-peak":
        # Dm tonic resolution (D: 146.83 Hz, F: 174.61 Hz, A: 220.00 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=146.83, gain_db=5, q=6.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=293.66, gain_db=2, q=5.0))
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=6500))
        board.append(pedalboard.Delay(delay_seconds=0.16, feedback=0.4))
        board.append(pedalboard.Compressor(threshold_db=-16, ratio=3.0))

    elif stage == "decay-one":
        # F subdominant calm (F: 174.61 Hz, A: 220.00 Hz, C: 261.63 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=174.61, gain_db=4, q=5.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=261.63, gain_db=2, q=4.0))
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=1500))
        board.append(pedalboard.Reverb(room_size=0.6, wet_level=0.7, dry_level=0.3))
        board.append(pedalboard.Compressor(threshold_db=-12, ratio=2.0))

    elif stage == "decay-two":
        # Dm return to tonic (D: 146.83 Hz, F: 174.61 Hz, A: 220.00 Hz)
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=146.83, gain_db=3, q=7.0))
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=220.00, gain_db=2, q=6.0))
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=600))
        board.append(pedalboard.Reverb(room_size=0.9, wet_level=0.85, dry_level=0.15))
        board.append(pedalboard.Delay(delay_seconds=0.35, feedback=0.55))
        board.append(pedalboard.Limiter(threshold_db=-8.0))

    elif stage == "dissolution":
        # Final Dm dissolution - all energies converging
        board.append(pedalboard.PeakFilter(cutoff_frequency_hz=146.83, gain_db=2, q=8.0))
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=250))
        board.append(pedalboard.Reverb(room_size=1.0, wet_level=1.0, dry_level=0.0))
        board.append(pedalboard.Limiter(threshold_db=-18.0))

    # After pedalboard chain, apply harmonic resonance for chord tonality

    # Apply harmonic resonance at current chord's fundamental tones
    current_chord_harmonics = _get_key_harmonics(key)

    # Map chord to its fundamental tones for resonance
    chord_fundamentals = {
        "Dm": [current_chord_harmonics["root"], current_chord_harmonics["third"], current_chord_harmonics["fifth"]],  # D, F, A
        "F": [174.61, 220.00, 261.63, 349.23],  # F, A, C, F4
        "Cm": [130.81, 155.56, 196.00, 392.00],  # C, Eb, G, G4
        "Gm": [196.00, 233.08, 293.66],  # G, Bb, D
        "Bb": [233.08, 293.66, 349.23],  # Bb, D, F
        "C": [130.81, 164.81, 196.00],  # C, E, G
        "A": [220.00, 261.63, 329.63],  # A, C, E
        "Eb": [155.56, 185.00, 233.08],  # Eb, G, Bb
    }

    chord_tones = chord_fundamentals.get(current_chord, chord_fundamentals["Dm"])

    processed = _apply_harmonic_resonance(board(audio, sr), sr, chord_tones, q=8.0, gain_db=1.5)

    # Apply stage-specific advanced processing
    if stage == "early-build":
        processed = _apply_sidechain_simulation(processed, sr, bpm, depth_db=-3)
    
    elif stage in ["pre-peak-one", "peak-one", "peak-two"]:
        # Punchy transient shaping for peaks
        processed = _apply_transient_shaping(processed, sr, attack_ms=5, sustain_db=-2, release_ms=100)
        # Add formant emphasis for harmonic character
        if stage == "peak-one":
            processed = _apply_formant_filter(processed, sr, 150, q=3.0, gain_db=3)
        elif stage == "peak-two":
            processed = _apply_formant_filter(processed, sr, 300, q=3.0, gain_db=2)
    
    elif stage == "post-peak":
        # Softer transients with sidechain pumping
        processed = _apply_transient_shaping(processed, sr, attack_ms=-10, sustain_db=-4, release_ms=200)
        processed = _apply_sidechain_simulation(processed, sr, bpm, depth_db=-5)
    
    elif stage in ["decay-one", "decay-two"]:
        # Smooth, sustained transients
        processed = _apply_transient_shaping(processed, sr, attack_ms=-20, sustain_db=-3, release_ms=500)
    
    elif stage == "ambient-intro":
        # Very smooth, atmospheric
        processed = _apply_transient_shaping(processed, sr, attack_ms=-30, sustain_db=-6, release_ms=1000)

    return processed


def apply_per_stage_audio_automation(state: VideoPipelineState) -> Dict[str, Any]:
    """Apply stage-specific EQ/compression to enhance musical expression.

    Args:
        state: VideoPipelineState with audio_paths, stage_timings, config

    Returns:
        State update: audio_with_automation = Path
    """
    config = state["config"]
    audio_paths = state["audio_paths"]
    stage_timings = state["stage_timings"]
    key = config.get("key", "Dm")
    bpm = config.get("bpm", 125)

    if not audio_paths:
        raise ValueError("No audio paths to process")

    with tempfile.TemporaryDirectory(prefix="openmusic-video-base-") as tmpdir:
        temp_dir = Path(tmpdir)

        base_audio, sr = sf.read(str(audio_paths[0]))
        for other_path in audio_paths[1:]:
            other_audio, other_sr = sf.read(str(other_path))
            assert other_sr == sr, "Sample rate mismatch"
            base_audio = np.concatenate([base_audio, other_audio])

        processed_audio = base_audio.copy()
        sample_rate = sr

        for start_sec, end_sec, stage_name in stage_timings:
            start_sample = int(start_sec * sample_rate)
            end_sample = min(int(end_sec * sample_rate), len(processed_audio))

            if start_sample >= end_sample:
                continue

            stage_segment = processed_audio[start_sample:end_sample]

            try:
                processed_segment = _apply_stage_modifications(stage_segment, sample_rate, stage_name, key, bpm)
                processed_audio[start_sample:end_sample] = processed_segment
                logger.info(f"Applied automation for stage {stage_name} ({start_sec}-{end_sec}s)")
            except Exception as e:
                logger.warning(f"Failed to apply automation for stage {stage_name}: {e}")

        output_dir = Path.home() / ".cache" / "openmusic" / "video" / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_with_automation = output_dir / "audio_with_automation.flac"

        sf.write(str(audio_with_automation), processed_audio, sample_rate)
        logger.info(f"Saved audio with automation to {audio_with_automation}")

    return {"audio_with_automation": audio_with_automation}