# Initializes the repository.
import subprocess
import sys
from os import path
from pathlib import Path

if __name__ == '__main__':
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "maturin"]
    )

    cwd = Path(path.dirname(__file__))

    wheels = (cwd / "wheels").absolute()

    tmt = wheels / "tmt"

    tmt.mkdir(exist_ok=True, parents=True)

    subprocess.check_call(
        [
            sys.executable, "-m",
            "maturin", "build",
            "--out", str(tmt),
            "--release",
        ],
        cwd=str((cwd / "tmt").absolute())
    )

    wheel = next(tmt.iterdir())

    subprocess.check_call(
        [
            sys.executable, "-m",
            "pip", "uninstall",
            str(wheel)
        ]
    )

    subprocess.check_call(
        [
            sys.executable, "-m",
            "pip", "install",
            "--force-reinstall",
            str(wheel)
        ]
    )


