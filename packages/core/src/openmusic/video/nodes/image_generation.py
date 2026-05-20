"""Image generation node for video pipeline."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from diffusers import StableDiffusionXLPipeline
import torch
from tenacity import retry, stop_after_attempt, wait_exponential

from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
def _run_sdxl_generation(
    prompt: str,
    model_path: str,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
) -> None:
    """Generate image using SDXL with retry logic."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
    ).to(device)

    with torch.inference_mode():
        image = pipe(
            prompt,
            num_inference_steps=30,
            guidance_scale=7.5,
            width=width,
            height=height,
        ).images[0]

    image.save(output_path)
    logger.info(f"Generated image saved to {output_path}")


async def generate_image_for_stage(state: VideoPipelineState) -> Dict[str, Any]:
    """Generate AI artwork for one musical stage using SDXL.

    Acquires GPU semaphore to prevent OOM, generates image,
    stores path in state.image_paths.

    Args:
        state: VideoPipelineState with stage_prompts, gpu_semaphore
        stage_name: Name of stage (e.g., "ambient-intro")

    Returns:
        State update: image_paths[stage_name] = Path or None
    """
    stage_name = state.get("stage_name", "unknown")
    base_prompt = state["stage_prompts"].get(stage_name, "")
    visual_modifiers = "deep dub aesthetic, abstract generative art, pitch black atmosphere"
    full_prompt = f"{base_prompt}. {visual_modifiers}. High contrast, film grain."

    output_dir = Path.home() / ".cache" / "openmusic" / "video" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stage_name}.png"

    gpu_semaphore = state.get("gpu_semaphore")
    if not gpu_semaphore:
        # Fallback: create a new semaphore for this task
        max_concurrent = state.get("max_concurrent_images", 2)
        gpu_semaphore = asyncio.Semaphore(max_concurrent)

    async with gpu_semaphore:
        try:
            await asyncio.to_thread(
                _run_sdxl_generation,
                full_prompt,
                state.get("sdxl_model_path", "stabilityai/sdxl-turbo"),
                output_path,
            )
            image_path = output_path
        except Exception as e:
            logger.error(f"Image generation failed for stage {stage_name}: {e}")
            image_path = None

    return {"image_paths": {stage_name: image_path}}