"""GPU semaphore for concurrent task limiting."""

import torch


def detect_max_concurrent_gpu_tasks() -> int:
    """Detect GPU capabilities to determine safe concurrent task count.

    Heuristic: 6GB VRAM per SDXL task.

    Returns:
        Max concurrent AI generation tasks (1-4 recommended)
    """
    if not torch.cuda.is_available():
        return 1

    try:
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9

        if vram_gb < 6:
            return 1
        elif vram_gb < 12:
            return 2
        elif vram_gb < 16:
            return 3
        else:
            return 4
    except Exception:
        return 2