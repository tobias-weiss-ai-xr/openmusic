# ACE-Step 1.5 Validation Report

## Summary

ACE-Step 1.5 is an open-source music generation model that achieves commercial-grade quality while running efficiently on consumer hardware. It supports 10 seconds to 10 minutes of audio generation with ultra-fast inference (under 2s on A100, under 10s on RTX 3090). The model uses a hybrid architecture combining a Language Model (LM) as a planner with a Diffusion Transformer (DiT) for audio synthesis.

**Repository**: https://github.com/ace-step/ACE-Step-1.5
**License**: MIT
**Python**: 3.11-3.12

---

## Output Format

| Property | Value |
|----------|-------|
| **Formats** | MP3, WAV, FLAC |
| **Default Format** | FLAC (fast saving, lossless) |
| **Sample Rate** | 48000 Hz |
| **Channels** | Stereo (2 channels) |
| **Bit Depth** | 32-bit float (tensor), format-dependent on disk |

### Format Selection

```python
# Python API
config = GenerationConfig(
    audio_format="flac"  # Options: "mp3", "wav", "flac"
)

# REST API
{
    "audio_format": "wav"
}

# CLI
--audio-format mp3
```

---

## Latency

### Generation Speed (Turbo Model)

| Hardware | 30s Audio | Full Song (~4min) |
|----------|-----------|-------------------|
| **A100 (80GB)** | ~0.5-2s | ~8-15s |
| **RTX 3090 (24GB)** | ~3-10s | ~30-60s |
| **RTX 3060 (12GB)** | ~10-15s | ~60-120s |
| **Apple Silicon (M1/M2 Max)** | ~15-30s | ~120-240s |

### Time Breakdown

| Component | % of Total (with LM) | % of Total (no LM) |
|-----------|---------------------|-------------------|
| **LM Planning** | 40-50% | 0% |
| **DiT Diffusion** | 25-35% | 70-80% |
| **VAE Decode** | 5-10% | 10-15% |
| **Audio Save** | 2-5% | 5-10% |
| **Other/Overhead** | 10-15% | 5-10% |

### Inference Steps Impact

| Steps | Quality | Speed |
|-------|---------|-------|
| 8 | High (turbo) | Fast |
| 16 | Very High | Moderate |
| 32-64 | Highest (base) | Slow |

---

## Hardware Requirements

### GPU VRAM Tiers

| VRAM | Tier | LM Models | Max Duration | Max Batch | Offload | Quantization |
|------|------|-----------|--------------|-----------|---------|--------------|
| ≤4GB | Tier 1 | None | 4-6 min | 1 | CPU + DiT | INT8 |
| 4-6GB | Tier 2 | None | 8-10 min | 1 | CPU + DiT | INT8 |
| 6-8GB | Tier 3 | 0.6B | 8-10 min | 2 | CPU + DiT | INT8 |
| 8-12GB | Tier 4 | 0.6B | 8-10 min | 2-4 | CPU + DiT | INT8 |
| 12-16GB | Tier 5 | 0.6B, 1.7B | 8-10 min | 4 | CPU | INT8 |
| 16-20GB | Tier 6a | 0.6B, 1.7B | 8-10 min | 4-8 | CPU | INT8 |
| 20-24GB | Tier 6b | 0.6B, 1.7B, 4B | 8 min | 8 | None | None |
| ≥24GB | Unlimited | All | 10 min | 8 | None | None |

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU VRAM** | 4GB | 8GB+ |
| **System RAM** | 16GB | 32GB |
| **CPU** | Modern multi-core | - |
| **Storage** | 20GB for models | SSD |

### Supported Platforms

| Platform | Backend | Notes |
|----------|---------|-------|
| NVIDIA CUDA | vllm, pt | Recommended |
| Apple Silicon | mlx, pt | M1/M2/M3 series |
| AMD ROCm | pt | Linux only |
| Intel XPU | pt | Arc GPUs |
| CPU | pt | Slow, fallback only |

### CPU Fallback

- **Performance Impact**: 10-50x slower than GPU
- **Automatic**: VAE decode falls back to CPU if GPU OOM
- **Full CPU Mode**: Supported but impractical for production

---

## Dub Techno Capability

### Can Generate Electronic Music: **YES**

ACE-Step supports 1000+ instruments and styles with fine-grained timbre description. Electronic music genres including dub techno are well within its capabilities.

### Recommended Prompts for Dub Techno

```python
# Chord stabs
caption = "deep dub techno chord stabs with heavy reverb and delay"

# Atmospheric bass
caption = "atmospheric dub techno bass line with sub frequencies and echo"

# Textures
caption = "dub techno delay textures with tape saturation and vinyl warmth"

# Full track
caption = "deep dub techno track at 125 BPM with metallic percussion, 
           spacious delays, warm analog bass, and ethereal pad textures"

# Basic/Minimal
caption = "minimal dub techno with repetitive rhythms and deep bass"
```

### Extended Dub Techno Prompt Templates

```python
# Classic Basic Channel / Chain Reaction style
caption = """
deep dub techno in Basic Channel style, heavy analog processing,
thick chord stabs with infinite reverb tail, sub-bass frequencies,
tape saturation warmth, 125 BPM, atmospheric and hypnotic
"""

# Rhythm & Sound inspired
caption = """
dub techno with stripped-back percussion, crisp hi-hats,
deep sub bass, minimal chord changes, heavy delay feedback,
lo-fi analog texture, moody and meditative atmosphere
"""

# Modern deep dub techno
caption = """
contemporary dub techno with lush pad textures, subtle arpeggios,
deep filtered bass, warm analog synth tones, spacious reverb,
ethereal atmosphere, 122 BPM, building tension gradually
"""

# Echocord / echospace style
caption = """
dub techno with layered delay effects, shimmering reverb,
dense atmospheric textures, slow evolving chords,
binaural processing, deep ambient undertones, 120 BPM
"""

# Club-focused dub techno
caption = """
driving dub techno with punchy kick drum, rolling bass line,
percussive chord stabs, syncopated hi-hats, 126 BPM,
dark warehouse atmosphere, hypnotic groove
"""

# Ambient dub techno (beatless)
caption = """
ambient dub techno without drums, floating chord progressions,
deep immersive textures, slow modulation, cavernous reverb,
meditative atmosphere, ethereal pads, no percussion
"""

# Industrial dub techno
caption = """
industrial dub techno with metallic percussion, distorted textures,
cold analog sounds, aggressive filtering, dystopian atmosphere,
mechanical rhythms, 128 BPM, dark and oppressive
"""
```

### Structure Tags for Dub Techno Lyrics

Since dub techno is primarily instrumental, use these structure tags:

```python
lyrics = """
[Intro]
deep atmospheric intro with filtered pad

[Verse - Atmospheric Build]
chord stabs enter gradually with increasing delay feedback

[Bridge - Textural Break]
stripped back to bass and subtle percussion

[Chorus - Full Depth]
all elements combine, maximum reverb and delay

[Outro - Fade to Dub]
elements drop out one by one, infinite delay trails
"""
```

Or simply:
```python
lyrics = "[Instrumental]"  # For pure instrumental generation
```

### Metadata Recommendations for Dub Techno

```python
params = GenerationParams(
    caption="deep dub techno with chord stabs and atmospheric delays",
    bpm=125,                    # Classic dub techno tempo
    keyscale="Am",              # Minor key works well
    timesignature="4",          # 4/4 time
    duration=180,               # 3 minutes typical
    instrumental=True,          # Usually instrumental
)
```

### Dub Techno Generation Tips

1. **Use "instrumental"** - Dub techno is typically instrumental
2. **BPM 120-130** - Classic dub techno tempo range
3. **Minor keys** - Am, Dm, Em work well for dark atmosphere
4. **Descriptive captions** - Include effects like "reverb", "delay", "tape saturation"
5. **Longer duration** - Dub techno benefits from extended development (3-6 min)
6. **Enable LM thinking** - Better metadata and style understanding

### Advanced Generation Parameters for Dub Techno

```python
params = GenerationParams(
    caption="deep dub techno with atmospheric delays",
    bpm=125,
    duration=180,  # 3 minutes for full track development
    instrumental=True,
    
    # Turbo model optimization
    inference_steps=8,      # Turbo default (fast, high quality)
    shift=3.0,              # Recommended for turbo: stronger semantics
    infer_method="ode",     # Deterministic, faster than SDE
    
    # LM parameters for better style understanding
    thinking=True,          # Enable LM chain-of-thought
    use_cot_metas=True,     # Auto-generate BPM, key, duration
    use_cot_caption=True,   # Enhance caption understanding
    lm_temperature=0.85,    # Balance creativity/consistency
)

config = GenerationConfig(
    batch_size=2,           # Generate variations for selection
    audio_format="wav",     # Lossless for dub techno quality
    use_random_seed=True,   # Explore variations
)
```

### Shift Parameter Guide for Dub Techno

| Shift | Effect | Dub Techno Use Case |
|-------|--------|---------------------|
| 1.0 | Default, even step distribution | General purpose |
| 2.0 | Moderate semantic emphasis | Balanced texture/detail |
| **3.0** | **Strong semantics** | **Recommended for dub techno** |
| 4.0-5.0 | Maximum semantic clarity | Very sparse, minimal tracks |

### Task Types for Dub Techno Production

| Task | Description | Dub Techno Use Case |
|------|-------------|---------------------|
| `text2music` | Generate from text description | Main generation mode |
| `cover` | Transform existing audio style | Apply dub techno style to reference |
| `repaint` | Regenerate specific time segment | Fix sections, add variation |
| `lego` (base model) | Add instrument layers | Add percussion, pads to stems |
| `extract` (base model) | Separate stems | Isolate bass, pads, percussion |

### Dub Techno Workflow with Task Types

```python
# 1. Generate base dub techno track
params = GenerationParams(
    task_type="text2music",
    caption="deep dub techno with chord stabs",
    bpm=125,
    duration=180,
    instrumental=True,
)

# 2. Create a dub version (style variation)
params = GenerationParams(
    task_type="cover",
    src_audio="base_track.wav",
    caption="stripped dub techno version with more delay",
    audio_cover_strength=0.5,  # Moderate transformation
)

# 3. Repaint a section for variation
params = GenerationParams(
    task_type="repaint",
    src_audio="base_track.wav",
    repainting_start=60.0,    # Start at 1 minute
    repainting_end=90.0,      # End at 1:30
    caption="intense breakdown with maximum reverb",
)

# 4. Extract stems for mixing (requires base model)
params = GenerationParams(
    task_type="extract",
    src_audio="full_track.wav",
    instruction="Extract the bass track from the audio:",
)
```

### Limitations

- **Precise sound design**: Cannot guarantee specific synth patches or exact timbres
- **Mixing quality**: Output may need post-processing for professional release
- **Stem separation**: Requires base model (`acestep-v15-base`), not turbo
- **Real-time**: Not suitable for live generation (latency 3-60s per track)
- **Copyright**: Cannot guarantee output is free from training data influence
- **Style consistency**: Results vary between seeds; use fixed seed for reproducibility

---

## API/CLI Usage

### Python API

```python
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

# Initialize handlers
dit_handler = AceStepHandler()
llm_handler = LLMHandler()

# Initialize services
dit_handler.initialize_service(
    project_root="/path/to/ACE-Step-1.5",
    config_path="acestep-v15-turbo",
    device="cuda"
)

llm_handler.initialize(
    checkpoint_dir="/path/to/checkpoints",
    lm_model_path="acestep-5Hz-lm-0.6B",
    backend="vllm",
    device="cuda"
)

# Configure generation
params = GenerationParams(
    caption="deep dub techno with atmospheric delays",
    bpm=125,
    duration=60,
    instrumental=True,
    thinking=True,  # Enable LM for better quality
)

config = GenerationConfig(
    batch_size=2,
    audio_format="wav",
)

# Generate music
result = generate_music(dit_handler, llm_handler, params, config, save_dir="/output")

if result.success:
    for audio in result.audios:
        print(f"Generated: {audio['path']}")
        print(f"Sample rate: {audio['sample_rate']}")
```

### REST API

```bash
# Start API server
uv run acestep-api
# Server runs on http://localhost:8001

# Submit generation task
curl -X POST http://localhost:8001/release_task \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "deep dub techno with atmospheric delays",
    "bpm": 125,
    "audio_duration": 60,
    "audio_format": "wav",
    "thinking": true,
    "batch_size": 2
  }'

# Query result (use task_id from response)
curl -X POST http://localhost:8001/query_result \
  -H 'Content-Type: application/json' \
  -d '{"task_id_list": ["your-task-id"]}'

# Download audio
curl "http://localhost:8001/v1/audio?path=/path/to/audio.wav" -o output.wav
```

### CLI (Interactive Wizard)

```bash
# Launch interactive wizard
cd ACE-Step-1.5
uv run python cli.py

# Or with config file
uv run python cli.py -c config.toml

# Configure only (save config without generating)
uv run python cli.py --configure
```

### CLI (Non-Interactive with Config)

Create `dub_techno_config.toml`:
```toml
caption = "deep dub techno with atmospheric delays"
bpm = 125
duration = 60
instrumental = true
thinking = true
batch_size = 2
audio_format = "wav"
save_dir = "output"
```

```bash
uv run python cli.py -c dub_techno_config.toml
```

---

## Model Weights

### DiT Models

| Model | Size | Quality | Speed | Use Case |
|-------|------|---------|-------|----------|
| `acestep-v15-turbo` | ~3GB | Very High | Fast | Production (recommended) |
| `acestep-v15-base` | ~3GB | Medium | Slow | Multi-track tasks |
| `acestep-v15-sft` | ~3GB | High | Slow | High quality single track |

### LM Models

| Model | Parameters | VRAM Needed | Quality |
|-------|------------|-------------|---------|
| `acestep-5Hz-lm-0.6B` | 0.6B | 6-8GB | Medium |
| `acestep-5Hz-lm-1.7B` | 1.7B | 12-16GB | High |
| `acestep-5Hz-lm-4B` | 4B | 20GB+ | Best |

### Model Download

Models are auto-downloaded on first run from HuggingFace:
- DiT: https://huggingface.co/ACE-Step/Ace-Step1.5
- LM: Available from same repository

---

## Recommendations

### For Dub Techno Project

| Aspect | Recommendation |
|--------|----------------|
| **Use ACE-Step?** | **YES** - Excellent for dub techno generation |
| **Model** | `acestep-v15-turbo` (speed) or `acestep-v15-base` (multi-track) |
| **LM Model** | `acestep-5Hz-lm-1.7B` (best balance) |
| **Min GPU** | 8GB VRAM (Tier 4) for LM features |
| **API** | REST API for service integration |
| **Format** | WAV for quality, FLAC for speed |

### Integration Strategy

1. **Batch Generation**: Generate multiple variations, select best
2. **Post-Processing**: Add final mixing/mastering in DAW
3. **Stem Extraction**: Use base model + extract task for individual stems
4. **Style Consistency**: Use fixed seed for reproducible results
5. **Long Tracks**: Generate 2-3 min segments, concatenate

### Limitations to Consider

- Not suitable for real-time generation
- Output may need professional mixing
- Cannot guarantee copyright-free output
- Style consistency varies between seeds

---

## Quick Reference Commands

```bash
# Install
git clone https://github.com/ace-step/ACE-Step-1.5.git
cd ACE-Step-1.5
uv sync

# Launch Gradio UI
uv run acestep

# Launch API server
uv run acestep-api

# Profile performance
python profile_inference.py --thinking

# Test GPU tier compatibility
python profile_inference.py --mode tier-test

# Download models
uv run acestep-download              # Default models
uv run acestep-download --all        # All models
uv run acestep-download --model acestep-v15-base  # Specific model
```

### Dub Techno Benchmark Commands

```bash
# Profile dub techno generation with LM
python profile_inference.py \
  --thinking \
  --duration 180 \
  --batch-size 2 \
  --inference-steps 8

# Benchmark across configurations
python profile_inference.py \
  --mode benchmark \
  --thinking \
  --benchmark-output dub_techno_benchmark.json

# Test low-VRAM dub techno generation (simulated 8GB)
MAX_CUDA_VRAM=8 python profile_inference.py \
  --thinking \
  --lm-model acestep-5Hz-lm-0.6B \
  --duration 120
```

---

## Resources

- **Documentation**: `ACE-Step-1.5/docs/en/`
- **API Reference**: `ACE-Step-1.5/docs/en/API.md`
- **Inference Guide**: `ACE-Step-1.5/docs/en/INFERENCE.md`
- **GPU Compatibility**: `ACE-Step-1.5/docs/en/GPU_COMPATIBILITY.md`
- **Benchmark Tool**: `ACE-Step-1.5/profile_inference.py`
- **HuggingFace**: https://huggingface.co/ACE-Step/Ace-Step1.5
- **Discord**: https://discord.gg/PeWDxrkdj7
