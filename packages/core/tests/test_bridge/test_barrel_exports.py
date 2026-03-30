"""Tests for bridge barrel exports."""

from openmusic.bridge import (
    BridgeError,
    TypeScriptBridge,
)


class TestBarrelExports:
    """Verify all public classes are exported."""

    def test_bridge_error_exported(self):
        assert BridgeError is not None

    def test_typescript_bridge_exported(self):
        assert TypeScriptBridge is not None
