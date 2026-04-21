from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKETEST_SCRIPT = (
    REPO_ROOT
    / "components"
    / "generate_data_dev"
    / "scripts"
    / "run_smoketests.py"
)


def _has_docker_runtime() -> bool:
    if shutil.which("docker") is None:
        return False
    result = subprocess.run(
        ["docker", "info"],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


class SimulatorSmoketestScripts(unittest.TestCase):
    @unittest.skipUnless(_has_docker_runtime(), "docker runtime is required for simulator smoketests")
    def test_dyngen_simulator_smoketest(self) -> None:
        completed = subprocess.run(
            [
                str(Path(".venv/bin/python") if Path(".venv/bin/python").exists() else "python"),
                str(SMOKETEST_SCRIPT),
                "--simulator",
                "dyngen",
            ],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            self.fail(
                "dyngen simulator smoketest failed:\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
