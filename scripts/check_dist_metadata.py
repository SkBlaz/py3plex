#!/usr/bin/env python3
"""Check that wheel and sdist metadata match the source release version."""

from __future__ import annotations

import email.parser
import os
from pathlib import Path
import re
import sys
import tarfile
import zipfile


def source_version() -> str:
    text = Path("py3plex/_version.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not find __version__ in py3plex/_version.py")
    return match.group(1)


def metadata_version(text: str, label: str) -> str:
    message = email.parser.Parser().parsestr(text)
    version = message.get("Version")
    if not version:
        raise RuntimeError(f"{label} does not contain a Version metadata field")
    return version


def main(dist_dir: str) -> None:
    path = Path(dist_dir)
    wheels = list(path.glob("py3plex-*.whl"))
    sdists = list(path.glob("py3plex-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"Expected one py3plex wheel and sdist in {path}; "
            f"found {len(wheels)} wheels and {len(sdists)} sdists"
        )

    expected = source_version()
    with zipfile.ZipFile(wheels[0]) as archive:
        metadata_path = next(
            name for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        )
        wheel_version = metadata_version(
            archive.read(metadata_path).decode("utf-8"), str(wheels[0])
        )

    with tarfile.open(sdists[0], "r:gz") as archive:
        metadata_file = next(
            member for member in archive.getmembers()
            if member.name.endswith("/PKG-INFO")
        )
        stream = archive.extractfile(metadata_file)
        if stream is None:
            raise RuntimeError(f"Could not read sdist metadata from {sdists[0]}")
        sdist_version = metadata_version(
            stream.read().decode("utf-8"), str(sdists[0])
        )

    for label, actual in (("wheel", wheel_version), ("sdist", sdist_version)):
        if actual != expected:
            raise RuntimeError(
                f"{label} metadata version {actual!r} does not match "
                f"source version {expected!r}"
            )

    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/tags/"):
        tag_version = ref[len("refs/tags/"):]
        if tag_version.startswith("v"):
            tag_version = tag_version[1:]
        if tag_version != expected:
            raise RuntimeError(
                f"Release tag {tag_version!r} does not match package version {expected!r}"
            )

    print(f"Wheel, sdist, and source versions agree: {expected}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
