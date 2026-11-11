"""Execute the published onboarding notebook cells against an installed package.

Run from outside the checkout after installing the built wheel. Notebook install
cells are skipped because CI installs the exact wheel under test beforehand.
All other code cells execute in order and any exception fails the check.
"""

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    for name in ("query_with_dsl", "community_detection"):
        path = ROOT / "notebooks" / f"{name}.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__main__"}
        for index, cell in enumerate(notebook["cells"], 1):
            if cell["cell_type"] != "code":
                continue
            code = "".join(cell["source"])
            if code.strip() == "!pip install py3plex -q":
                continue
            print(f"Executing {name}, cell {index}", flush=True)
            exec(compile(code, f"{path}:cell-{index}", "exec"), namespace)
        print(f"PASS: {name}", flush=True)


if __name__ == "__main__":
    main()
