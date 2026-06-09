from dataclasses import dataclass, field


@dataclass
class ACEStepConfig:
    """Configuration for the ACE-Step AI model."""

    model_preset: str = "sft"
    model_path: str = ""
    device: str = "auto"
    audio_format: str = "wav"
    max_duration: int = 600
    inference_steps: int = 0

    def __post_init__(self):
        if not self.model_path:
            if self.model_preset == "turbo":
                self.model_path = "acestep-v15-turbo"
                if self.inference_steps == 0:
                    self.inference_steps = 8
            else:
                self.model_path = "acestep-v15-sft"
                if self.inference_steps == 0:
                    self.inference_steps = 50


@dataclass
class GenerationParams:
    """Parameters for a single audio generation request."""

    prompt: str = ""
    bpm: int | None = None
    key: str | None = None
    duration: int = 30
    instrumental: bool = True
