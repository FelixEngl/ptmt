# Copyright 2024 Felix Engl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import subprocess
import sys
from os import path
from pathlib import Path

if __name__ == '__main__':
    """
    A script to initialize and compile all necessary scripts and codes bewore working with TMT"""

    # Prepare submodule
    cwd = Path(path.dirname(__file__)).absolute()

    subprocess.check_call(
        ["git", "submodule", "init"],
        cwd=str(cwd)
    )

    subprocess.check_call(
        ["git", "submodule", "update"],
        cwd=str(cwd)
    )

    subprocess.check_call(
        ["git", "checkout", "master"],
        cwd=str(cwd / "tmt")
    )

    subprocess.check_call(
        ["git", "pull"],
        cwd=str(cwd / "tmt")
    )

    # Install maturin
    subprocess.check_call(
        [
            sys.executable, "-m",
            "pip", "install", "maturin"
        ]
    )


    wheels = (cwd / "wheels").absolute()

    tmt = wheels / "tmt"

    tmt.mkdir(exist_ok=True, parents=True)

    # Build TMT
    subprocess.check_call(
        [
            sys.executable, "-m",
            "maturin", "build", "--out", str(tmt), "--release",
        ],
        cwd=str((cwd / "tmt").absolute())
    )

    subprocess.check_call(
        ["cargo", "clean"],
        cwd=str((cwd / "tmt").absolute())
    )

    wheel = next(tmt.iterdir())

    # Update/Install the wheel.
    subprocess.check_call(
        [
            sys.executable, "-m",
            "pip", "uninstall", "-y",
            str(wheel)
        ]
    )

    subprocess.check_call(
        [
            sys.executable, "-m",
            "pip", "install", "--force-reinstall",
            str(wheel)
        ]
    )
