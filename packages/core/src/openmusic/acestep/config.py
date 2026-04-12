from dataclasses import dataclass, field


@dataclass
class ACEStepConfig:
    """Configuration for the ACE-Step AI model."""

    model_path: str = "acestep-v15-turbo"
    device: str = "auto"
    audio_format: str = "wav"
    max_duration: int = 600
    inference_steps: int = 8


@dataclass
class GenerationParams:
    """Parameters for a single audio generation request."""

    prompt: str = ""
    bpm: int | None = None
    key: str | None = None
    duration: int = 30
    instrumental: bool = True
