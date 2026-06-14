"""LangGraph-orchestrated video generation pipeline for OpenMusic."""

# Lazy imports via __getattr__ to avoid loading heavy deps (langgraph, diffusers)
# at package import time. Submodules are imported on first access.

__all__ = ["VideoPipelineState", "initialize_video_pipeline_state", "build_video_pipeline_graph"]


def __getattr__(name):
    if name == "VideoPipelineState":
        from openmusic.video.state import VideoPipelineState as _cls
        return _cls
    if name == "initialize_video_pipeline_state":
        from openmusic.video.state import initialize_video_pipeline_state as _fn
        return _fn
    if name == "build_video_pipeline_graph":
        from openmusic.video.graph import build_video_pipeline_graph as _fn
        return _fn
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)