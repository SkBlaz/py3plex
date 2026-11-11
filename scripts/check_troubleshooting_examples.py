"""Execute the published plotting, Arrow, and algorithm recovery examples."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

from check_onboarding_guides import python_blocks, ROOT


def main() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    page = ROOT / "docfiles/getting_started/common_issues.rst"
    lines = page.read_text(encoding="utf-8").splitlines()
    first = lines.index("Visualization Issues") + 1
    last = lines.index("Docker Issues") + 1
    old_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            namespace = {"__name__": "__main__"}
            count = 0
            for line, code in python_blocks(page):
                if not first < line < last:
                    continue
                print(f"Executing {page.name}:{line}", flush=True)
                exec(compile(code, f"{page}:{line}", "exec"), namespace)
                if "matplotlib.use('Agg')" in code:
                    # Also exercise backend selection before any plotting or
                    # py3plex imports, in a fresh headless Python process.
                    subprocess.run([sys.executable, "-c", code], check=True, timeout=60)
                count += 1
            assert count >= 8, "Troubleshooting examples were not discovered"
            for name in ("network.png", "output.png"):
                image = Path(name).read_bytes()
                assert image.startswith(b"\x89PNG\r\n\x1a\n") and len(image) > 1000, name
            network = namespace["network"]
            assert network.core_network.number_of_edges() == 2
            assert network.core_network[("Bob", "layer1")][("Carol", "layer1")][0]["weight"] == 2.5
            assert not network.directed
            print(f"PASS: {count} troubleshooting blocks, headless plots, and Arrow round trip", flush=True)
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
