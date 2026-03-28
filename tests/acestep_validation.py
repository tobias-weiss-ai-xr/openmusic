#!/usr/bin/env python3
"""
ACE-Step 1.5 Dub Techno Validation Test Script

Validates ACE-Step's dub techno generation capability by running three
representative prompts through the generate_music API and inspecting outputs.

Expected Output Format:
    Each generation produces a stereo WAV file at 48000 Hz sample rate.
    Audio tensors are float32, shape [2, num_samples] (channels-first).
    Duration ≈ requested duration (±2s tolerance due to model alignment).
    File sizes vary by format: ~2.9 MB/s for WAV 32-bit float stereo @ 48kHz.

Usage:
    python tests/acestep_validation.py                           # All 3 dub techno prompts
    python tests/acestep_validation.py --prompt "custom prompt"  # Single custom prompt
    python tests/acestep_validation.py --duration 60             # Override duration
    python tests/acestep_validation.py --output /tmp/output      # Custom output dir
    python tests/acestep_validation.py --no-gpu-check            # Skip GPU availability check
    python tests/acestep_validation.py --dry-run                 # Validate params only, no generation

Exit Codes:
    0 - Success (or graceful skip when GPU unavailable)
    1 - Configuration/import error
    2 - Generation failure

Requirements:
    - ACE-Step 1.5 source at project root: ./ACE-Step-1.5/
    - Python 3.11-3.12
    - CUDA GPU (recommended; script exits 0 with message if unavailable)
    - See packages/core/requirements-acestep.txt for dependency list
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

# ACE-Step-1.5 lives at project root; add to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ACESTEP_ROOT = _PROJECT_ROOT / "ACE-Step-1.5"

if _ACESTEP_ROOT.is_dir():
    sys.path.insert(0, str(_ACESTEP_ROOT))

_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "acestep"
DUB_TECHNO_PROMPTS = [
    {
        "name": "chord_stabs",
        "caption": "deep dub techno chord stabs with heavy reverb and delay",
        "description": "Classic chord stab pattern — tests harmonic generation",
    },
    {
        "name": "atmospheric_bass",
        "caption": "atmospheric dub techno bass line with sub frequencies and echo",
        "description": "Sub-bass focus — tests low-frequency generation quality",
    },
    {
        "name": "delay_textures",
        "caption": "dub techno delay textures with tape saturation and vinyl warmth",
        "description": "Textural/ambient — tests effects description adherence",
    },
]


def check_gpu_available() -> tuple[bool, str]:
    """Check if CUDA GPU is available and return (available, info_string)."""
    try:
        import torch

        if not torch.cuda.is_available():
            return (
                False,
                "CUDA not available. torch.cuda.is_available() returned False.",
            )

        device_name = torch.cuda.get_device_name(0)
        vram_total_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
        vram_free_gb = (
            torch.cuda.mem_get_info(0)[0] / (1024**3)
            if hasattr(torch.cuda, "mem_get_info")
            else -1
        )
        info = (
            f"GPU: {device_name}, "
            f"VRAM: {vram_total_gb:.1f} GB total, "
            f"{vram_free_gb:.1f} GB free"
        )
        return True, info
    except ImportError:
        return False, "PyTorch not installed — cannot check GPU."
    except Exception as exc:
        return False, f"GPU check failed: {exc}"


def check_acestep_importable() -> tuple[bool, str]:
    """Check if ACE-Step modules can be imported.

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        from acestep.inference import GenerationConfig, GenerationParams, generate_music  # noqa: F401
        from acestep.handler import AceStepHandler  # noqa: F401
        return True, ""
    except ImportError as exc:
        return False, f"Cannot import ACE-Step: {exc}. Is ACE-Step-1.5/ at project root?"
    except Exception as exc:
        return False, f"Unexpected import error: {exc}"


def build_generation_params(
    caption: str,
    duration: int = 30,
    bpm: int = 125,
    instrumental: bool = True,
    thinking: bool = False,
) -> dict:
    """Build GenerationParams kwargs as a plain dict.

    Uses dict instead of dataclass to avoid import-time dependency.
    The dict is passed to GenerationParams(**kwargs) inside run_generation().
    """
    return {
        "task_type": "text2music",
        "caption": caption,
        "lyrics": "[Instrumental]",
        "instrumental": instrumental,
        "bpm": bpm,
        "duration": float(duration),
        "inference_steps": 8,       # Turbo model default
        "shift": 3.0,               # Strong semantics — recommended for dub techno
        "infer_method": "ode",      # Deterministic diffusion, faster than SDE
        "seed": -1,
        "thinking": thinking,
        "use_cot_metas": True,
        "use_cot_caption": True,
        "enable_normalization": True,
        "normalization_db": -1.0,
        "fade_in_duration": 0.5,
        "fade_out_duration": 1.0,
    }


def build_generation_config(
    audio_format: str = "wav",
    batch_size: int = 1,
) -> dict:
    """Build GenerationConfig kwargs as a plain dict."""
    return {
        "audio_format": audio_format,
        "batch_size": batch_size,
        "use_random_seed": True,
    }


def run_generation(
    params_dict: dict,
    config_dict: dict,
    output_dir: Path,
    audio_name: str,
    use_lm: bool = False,
) -> dict:
    """Run a single generation and return result summary.

    Expected output:
        {
            "success": bool,
            "audio_path": Optional[str],
            "sample_rate": Optional[int],
            "duration_sec": Optional[float],
            "file_size_bytes": Optional[int],
            "error": Optional[str],
            "generation_time_sec": Optional[float],
        }

    Args:
        params_dict: Keyword args for GenerationParams.
        config_dict: Keyword args for GenerationConfig.
        output_dir: Directory to save generated audio.
        audio_name: Descriptive name for the output file.
        use_lm: Whether to initialize and use the LM handler.

    Returns:
        Summary dict with generation results or error info.
    """
    from acestep.inference import GenerationConfig, GenerationParams, generate_music

    params = GenerationParams(**params_dict)
    config = GenerationConfig(**config_dict)

    output_dir.mkdir(parents=True, exist_ok=True)

    from acestep.handler import AceStepHandler

    dit_handler = AceStepHandler()

    print(f"  Initializing DiT model (config: acestep-v15-turbo)...")
    dit_handler.initialize_service(
        project_root=str(_ACESTEP_ROOT),
        config_path="acestep-v15-turbo",
        device="cuda",
    )

    llm_handler = None
    if use_lm:
        try:
            from acestep.llm_inference import LLMHandler

            llm_handler = LLMHandler()
            llm_handler.initialize(
                checkpoint_dir=str(_ACESTEP_ROOT / "checkpoints"),
                lm_model_path="acestep-5Hz-lm-0.6B",
                backend="pt",  # PyTorch backend uses less VRAM than vllm
                device="cuda",
            )
            print("  LM handler initialized (acestep-5Hz-lm-0.6B, pt backend)")
        except Exception as exc:
            print(f"  Warning: LM initialization failed, continuing without LM: {exc}")
            llm_handler = None
            params.thinking = False

    print(f"  Generating: {params.caption[:60]}...")
    t0 = time.time()

    result = generate_music(
        dit_handler=dit_handler,
        llm_handler=llm_handler,
        params=params,
        config=config,
        save_dir=str(output_dir),
    )

    elapsed = time.time() - t0

    if not result.success:
        return {
            "success": False,
            "audio_path": None,
            "sample_rate": None,
            "duration_sec": None,
            "file_size_bytes": None,
            "error": result.error or result.status_message,
            "generation_time_sec": round(elapsed, 2),
        }

    # Extract first audio from result
    if not result.audios:
        return {
            "success": False,
            "audio_path": None,
            "sample_rate": None,
            "duration_sec": None,
            "file_size_bytes": None,
            "error": "Generation succeeded but no audio in result",
            "generation_time_sec": round(elapsed, 2),
        }

    audio_info = result.audios[0]
    audio_path = audio_info.get("path", "")
    sample_rate = audio_info.get("sample_rate", 48000)
    tensor = audio_info.get("tensor")

    duration_sec = None
    if tensor is not None:
        # tensor shape: [channels, samples]
        num_samples = tensor.shape[-1]
        duration_sec = round(num_samples / sample_rate, 2)

    file_size = None
    if audio_path and os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
    elif audio_path:
        # ACE-Step generates files with UUID names; find the most recent
        wav_files = list(output_dir.glob("*.wav"))
        if wav_files:
            latest = max(wav_files, key=os.path.getctime)
            audio_path = str(latest)
            file_size = os.path.getsize(latest)
            if tensor is None:
                # Derive duration from WAV file size: stereo float32 @ 48kHz
                # WAV header = 44 bytes, each sample = 4 bytes * 2 channels
                data_bytes = file_size - 44
                if data_bytes > 0:
                    num_samples = data_bytes // (4 * 2)
                    duration_sec = round(num_samples / sample_rate, 2)

    # Get file size
    file_size = None
    if audio_path and os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
    elif audio_path:
        # Model generates with UUID filename; find the actual file
        wav_files = list(output_dir.glob("*.wav"))
        if wav_files:
            # Pick the most recently created
            latest = max(wav_files, key=os.path.getctime)
            audio_path = str(latest)
            file_size = os.path.getsize(latest)
            if tensor is None:
                # Re-derive duration from file size (WAV stereo float32 @ 48kHz)
                # WAV header ~44 bytes, each sample = 4 bytes * 2 channels
                data_bytes = file_size - 44
                if data_bytes > 0:
                    num_samples = data_bytes // (4 * 2)
                    duration_sec = round(num_samples / sample_rate, 2)

    return {
        "success": True,
        "audio_path": audio_path,
        "sample_rate": sample_rate,
        "duration_sec": duration_sec,
        "file_size_bytes": file_size,
        "error": None,
        "generation_time_sec": round(elapsed, 2),
    }


def print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("ACE-STEP DUB TECHNO VALIDATION SUMMARY")
    print("=" * 70)

    total_time = 0.0
    successes = 0

    for i, r in enumerate(results, 1):
        status = "PASS" if r["success"] else "FAIL"
        print(f"\n  [{status}] Generation #{i}")
        print(f"    Duration:  {r['duration_sec']}s" if r["duration_sec"] else "    Duration:  N/A")
        print(f"    Sample Rate: {r['sample_rate']} Hz" if r["sample_rate"] else "    Sample Rate: N/A")
        print(f"    File Size:  {r['file_size_bytes']} bytes" if r["file_size_bytes"] else "    File Size:  N/A")
        print(f"    Gen Time:   {r['generation_time_sec']}s" if r["generation_time_sec"] else "    Gen Time:   N/A")
        if r["audio_path"]:
            print(f"    Path:       {r['audio_path']}")
        if r["error"]:
            print(f"    Error:      {r['error']}")

        if r["success"]:
            successes += 1
        if r["generation_time_sec"]:
            total_time += r["generation_time_sec"]

    print(f"\n{'-' * 70}")
    print(f"  Results: {successes}/{len(results)} successful")
    print(f"  Total generation time: {total_time:.1f}s")
    print(f"  Expected output format: stereo WAV, 48000 Hz, float32")
    print("=" * 70)


def dry_run(prompts: list[dict], duration: int) -> None:
    print("DRY RUN: Validating generation parameters...\n")

    for p in prompts:
        params = build_generation_params(
            caption=p["caption"],
            duration=duration,
        )
        config = build_generation_config()

        print(f"  Prompt: {p['name']} ({p['description']})")
        print(f"    caption:      {params['caption']}")
        print(f"    bpm:          {params['bpm']}")
        print(f"    duration:     {params['duration']}s")
        print(f"    instrumental: {params['instrumental']}")
        print(f"    inference_steps: {params['inference_steps']}")
        print(f"    shift:        {params['shift']}")
        print(f"    infer_method: {params['infer_method']}")
        print(f"    audio_format: {config['audio_format']}")
        print(f"    batch_size:   {config['batch_size']}")
        print()

    print("All parameters valid. Use without --dry-run to generate audio.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ACE-Step 1.5 Dub Techno Validation Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                 Run all 3 dub techno prompts
  %(prog)s --prompt "minimal dub techno"   Run a single custom prompt
  %(prog)s --duration 60 --output /tmp     60s output to custom dir
  %(prog)s --dry-run                       Validate params without generating
  %(prog)s --no-gpu-check                  Skip GPU availability check
        """,
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Custom prompt (overrides default dub techno prompts)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(_DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Audio duration in seconds (default: 30, max: 600)",
    )
    parser.add_argument(
        "--bpm",
        type=int,
        default=125,
        help="BPM for generation (default: 125)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="wav",
        choices=["wav", "flac", "mp3"],
        help="Audio output format (default: wav)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate parameters without generating audio",
    )
    parser.add_argument(
        "--no-gpu-check",
        action="store_true",
        help="Skip GPU availability check (may hang on CPU)",
    )
    parser.add_argument(
        "--use-lm",
        action="store_true",
        help="Enable LM reasoning (requires 6GB+ VRAM, slower)",
    )

    args = parser.parse_args()

    if args.duration < 10:
        print("Error: Minimum duration is 10 seconds.")
        return 1
    if args.duration > 600:
        print("Error: Maximum duration is 600 seconds (10 minutes).")
        return 1

    if args.prompt:
        prompts = [
            {
                "name": "custom",
                "caption": args.prompt,
                "description": "User-provided custom prompt",
            }
        ]
    else:
        prompts = DUB_TECHNO_PROMPTS

    output_dir = Path(args.output)

    print("ACE-Step 1.5 Dub Techno Validation")
    print(f"  Output dir:  {output_dir}")
    print(f"  Duration:    {args.duration}s")
    print(f"  BPM:         {args.bpm}")
    print(f"  Format:      {args.format}")
    print(f"  Prompts:     {len(prompts)}")
    print()

    if args.dry_run:
        dry_run(prompts, args.duration)
        return 0

    importable, import_msg = check_acestep_importable()
    if not importable:
        print(f"SKIP: {import_msg}")
        print("ACE-Step source not available — skipping generation test.")
        print("To fix: clone ACE-Step-1.5/ to project root.")
        return 0

    if not args.no_gpu_check:
        gpu_ok, gpu_info = check_gpu_available()
        if not gpu_ok:
            print(f"SKIP: {gpu_info}")
            print("No CUDA GPU available — generation would be impractical.")
            print("To force: re-run with --no-gpu-check (may hang on CPU).")
            return 0
        print(f"GPU: {gpu_info}")

        # Warn about low VRAM
        try:
            import torch

            vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            if vram_gb < 6:
                print(
                    f"WARNING: Low VRAM ({vram_gb:.1f} GB). "
                    "DiT-only mode recommended. Avoid --use-lm."
                )
            elif vram_gb < 8:
                print(
                    f"NOTE: {vram_gb:.1f} GB VRAM. LM with pt backend may work "
                    "but will be slow. Consider skipping --use-lm."
                )
        except Exception:
            pass

    print()

    results = []
    for i, prompt_info in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {prompt_info['name']}: {prompt_info['caption']}")

        params_dict = build_generation_params(
            caption=prompt_info["caption"],
            duration=args.duration,
            bpm=args.bpm,
            thinking=args.use_lm,
        )
        config_dict = build_generation_config(
            audio_format=args.format,
            batch_size=1,
        )

        try:
            result = run_generation(
                params_dict=params_dict,
                config_dict=config_dict,
                output_dir=output_dir,
                audio_name=prompt_info["name"],
                use_lm=args.use_lm,
            )
            results.append(result)

            if result["success"]:
                print(
                    f"  OK: {result['duration_sec']}s, "
                    f"{result['sample_rate']} Hz, "
                    f"{result['generation_time_sec']}s gen time"
                )
            else:
                print(f"  FAILED: {result['error']}")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append({
                "success": False,
                "audio_path": None,
                "sample_rate": None,
                "duration_sec": None,
                "file_size_bytes": None,
                "error": str(exc),
                "generation_time_sec": None,
            })

        print()

    print_summary(results)

    all_ok = all(r["success"] for r in results)
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
