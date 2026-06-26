"""Tests for MCP orchestrator."""

import pytest
from unittest.mock import patch


class TestMCPOrchestrator:
    def test_config_dataclass(self):
        from openmusic.mcp.orchestrator import MCPConfig

        config = MCPConfig()
        assert config.ableton_host == "127.0.0.1"
        assert config.ableton_port == 11044
        assert config.comfyui_host == "127.0.0.1"
        assert config.comfyui_port == 8188

    def test_mcp_orchestrator_creation(self):
        from openmusic.mcp.orchestrator import MCPOrchestrator, MCPConfig

        config = MCPConfig()
        orch = MCPOrchestrator(config)
        assert orch.config == config

    def test_get_ableton_status_not_connected(self):
        from openmusic.mcp.orchestrator import MCPOrchestrator, MCPConfig

        orch = MCPOrchestrator(MCPConfig())
        with patch.dict("sys.modules", {"pythonosc": None, "pythonosc.udp_client": None}):
            status = orch.get_ableton_status()
        assert status["connected"] is False
