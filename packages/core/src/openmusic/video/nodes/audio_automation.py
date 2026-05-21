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


def _apply_stage_modifications(
    audio: np.ndarray,
    sr: int,
    stage: str,
    key: str = "Dm",
    bpm: int = 125,
) -> np.ndarray:
    """Apply stage-specific audio effects with advanced sound design.

    Professional mastering chain with transient shaping, sidechain pumping,
    formant filtering, and multi-band dynamics per harmonic progression stage.

    Args:
        audio: Audio segment (stereo)
        sr: Sample rate
        stage: Stage identifier
        key: Musical key for harmonic context
        bpm: BPM for rhythmic modulation

    Returns:
        Processed audio segment
    """
    board = pedalboard.Pedalboard()

    if stage == "ambient-intro":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=350))
        board.append(pedalboard.Reverb(wet_level=0.5, decay_seconds=5.0))
        board.append(pedalboard.Limiter(limit_db=-6.0))

    elif stage == "early-build":
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=35))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=800, gain_db=2.5, q=1.2))
        board.append(pedalboard.Compressor(threshold_db=-14, ratio=2.5))
        board.append(pedalboard.Reverb(wet_level=0.25))

    elif stage == "mid-build":
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=45))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=1400, gain_db=4, q=0.6))
        board.append(pedalboard.Compressor(threshold_db=-16, ratio=3.0))

    elif stage == "pre-peak-one":
        board.append(pedalboard.LowShelfFilter(gain_db=4, cutoff_frequency_hz=130))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=70))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=500, gain_db=-2, q=2.0))
        board.append(pedalboard.Bitcrush(bit_depth=14))
        board.append(pedalboard.Compressor(threshold_db=-18, ratio=3.5))

    elif stage == "peak-one":
        board.append(pedalboard.LowShelfFilter(gain_db=8, cutoff_frequency_hz=90))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=90))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=150, gain_db=3, q=1.5))
        board.append(pedalboard.Distortion(drive_db=15))
        board.append(pedalboard.Compressor(threshold_db=-26, ratio=6.0))
        board.append(pedalboard.Tanh())

    elif stage == "peak-two":
        board.append(pedalboard.LowShelfFilter(gain_db=6, cutoff_frequency_hz=105))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=2200, gain_db=5, q=1.0))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=120, gain_db=2, q=2.0))
        board.append(pedalboard.Saturation(drive_db=22))
        board.append(pedalboard.Compressor(threshold_db=-24, ratio=5.0))

    elif stage == "post-peak":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=7000))
        board.append(pedalboard.BiquadFilter(cutoff_frequency_hz=220, gain_db=-4))
        board.append(pedalboard.Delay(delay_seconds=0.125, feedback=0.35))
        board.append(pedalboard.Compressor(threshold_db=-14, ratio=3.0))

    elif stage == "decay-one":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=1800))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=800, gain_db=-3, q=1.8))
        board.append(pedalboard.Reverb(wet_level=0.65, decay_seconds=4.0))
        board.append(pedalboard.Compressor(threshold_db=-10, ratio=2.0))

    elif stage == "decay-two":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=700))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=400, gain_db=-5, q=2.5))
        board.append(pedalboard.Reverb(wet_level=0.8, decay_seconds=6.0))
        board.append(pedalboard.Delay(delay_seconds=0.3, feedback=0.5))
        board.append(pedalboard.Limiter(limit_db=-9.0))

    elif stage == "dissolution":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=300))
        board.append(pedalboard.Reverb(wet_level=0.9, decay_seconds=10.0))
        board.append(pedalboard.Limiter(limit_db=-15.0))

    # After pedalboard chain, apply additional processing
    processed = board(audio, sr)

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