import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class BridgeError(Exception):
    def __init__(self, message: str, stderr: str = ""):
        self.stderr = stderr
        if stderr:
            super().__init__(f"{message}: {stderr.strip()}")
        else:
            super().__init__(message)


class TypeScriptBridge:
    DEFAULT_TIMEOUT = 600

    def __init__(self, effects_bin: str | None = None):
        if effects_bin is not None:
            self.effects_bin = effects_bin
        else:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            self.effects_bin = str(
                repo_root / "packages" / "effects" / "dist" / "index.js"
            )

    def is_available(self) -> bool:
        node_exists = shutil.which("node") is not None
        bin_exists = os.path.exists(self.effects_bin)
        return node_exists and bin_exists

    def call_audio_engine(
        self, input_files: list[str], output_path: str, config: dict
    ) -> str:
        tmpdir = tempfile.mkdtemp(prefix="openmusic-")
        try:
            input_dir = os.path.join(tmpdir, "input")
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(input_dir)
            os.makedirs(output_dir)

            for i, stem_path in enumerate(input_files):
                shutil.copy2(stem_path, os.path.join(input_dir, f"stem_{i}.wav"))

            bridge_config = {
                **config,
                "inputStems": [
                    {"path": f"input/stem_{i}.wav", "role": "stem"}
                    for i in range(len(input_files))
                ],
                "outputPath": "output/processed.wav",
            }

            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w") as f:
                json.dump(bridge_config, f)

            result = subprocess.run(
                ["node", self.effects_bin, "--config", config_path],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=self.DEFAULT_TIMEOUT,
            )

            if result.returncode != 0:
                raise BridgeError("Effects processing failed", stderr=result.stderr)

            return output_path
        finally:
            self.cleanup(tmpdir)

    def cleanup(self, temp_dir: str):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
