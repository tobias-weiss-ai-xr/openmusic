"""Base effect class for OpenMusic audio effects."""

from abc import ABC, abstractmethod
from typing import Any, Dict

import numpy as np


class Effect(ABC):
    """Abstract base class for audio effects.

    All effects must implement the process method which takes audio data
    and parameters, returning the processed audio.
    """

    @abstractmethod
    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio data with the effect.

        Args:
            audio: Input audio data as numpy array. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary of effect parameters.

        Returns:
            Processed audio data with same shape as input.
        """
        pass
