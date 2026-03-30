"""OpenMusic Core - AI-powered dub techno generation."""

__version__ = "0.1.0"

from openmusic.acestep import (
    ACEStepConfig,
    GenerationParams,
    CacheManager,
    ACEStepGenerator,
    ACEStepNotAvailableError,
    GPUOutOfMemoryError,
)
from openmusic.bridge import (
    BridgeError,
    TypeScriptBridge,
)
from openmusic.orchestrator import (
    MixConfig,
    MixOrchestrator,
    PipelineResult,
    PipelineStage,
    ProgressReporter,
    run_pipeline,
)
from openmusic.config import ConfigParser  # re-export for convenience
from openmusic.arrangement import (
    Timeline,
    Track,
    crossfade_numpy,
    generate_crossfade_curve,
    MixArranger,
)
from openmusic.export import (
    AudioEncoder,
    AudioInfo,
    EncoderNotFoundError,
    EncodingError,
    EmbeddingError,
    TrackMetadata,
    embed_metadata,
)
