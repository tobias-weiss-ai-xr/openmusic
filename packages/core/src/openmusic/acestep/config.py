from dataclasses import dataclass, field


@dataclass
class ACEStepConfig:
    model_path: str = "acestep-v15-turbo"
    device: str = "auto"
    audio_format: str = "flac"
    max_duration: int = 600
    inference_steps: int = 8


@dataclass
class GenerationParams:
    prompt: str = ""
    bpm: int | None = None
    key: str | None = None
    duration: int = 30
    instrumental: bool = True
