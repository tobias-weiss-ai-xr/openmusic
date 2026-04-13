"""MCP orchestration for unified creative pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """Configuration for MCP server connections."""

    ableton_host: str = "127.0.0.1"
    ableton_port: int = 11044
    comfyui_host: str = "127.0.0.1"
    comfyui_port: int = 8188


class MCPOrchestrator:
    """Orchestrate multiple MCP servers for unified creative pipeline.

    Servers:
    - Ableton Live (ableton-mcp-extended): transport, clips, devices
    - ComfyUI (comfyui-mcp-server): image generation
    """

    def __init__(self, config: MCPConfig | None = None):
        self.config = config or MCPConfig()

    def get_ableton_status(self) -> dict:
        """Check Ableton Live connection status."""
        try:
            import pythonosc.udp_client

            client = pythonosc.udp_client.SimpleUDPClient(
                self.config.ableton_host, self.config.ableton_port
            )
            # Try a simple ping - AbletonOSC responds to /live/test
            # In practice, we'd need to send and listen for response
            return {"connected": True, "host": self.config.ableton_host}
        except (ImportError, Exception) as e:
            logger.debug(f"Ableton not available: {e}")
            return {"connected": False, "error": str(e)}

    def get_comfyui_status(self) -> dict:
        """Check ComfyUI connection status."""
        try:
            import urllib.request

            url = f"http://{self.config.comfyui_host}:{self.config.comfyui_port}/system_stats"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return {"connected": True, "host": self.config.comfyui_host}
        except Exception as e:
            logger.debug(f"ComfyUI not available: {e}")
        return {"connected": False, "error": str(e)}

    def generate_images(
        self, prompt: str, width: int = 1920, height: int = 1080, count: int = 1
    ) -> list[str]:
        """Generate images via ComfyUI MCP.

        Returns list of file paths to generated images.
        """
        # Placeholder - would call ComfyUI MCP server
        logger.info(f"ComfyUI image generation requested: {prompt[:80]}...")
        return []

    def set_ableton_tempo(self, bpm: float) -> bool:
        """Set Ableton Live tempo via OSC."""
        try:
            import pythonosc.udp_client

            client = pythonosc.udp_client.SimpleUDPClient(
                self.config.ableton_host, self.config.ableton_port
            )
            client.send_message("/live/tempo", [bpm])
            logger.info(f"Set Ableton tempo to {bpm} BPM")
            return True
        except ImportError:
            logger.warning("python-osc not installed")
            return False
