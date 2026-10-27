#!/usr/bin/env python3
"""Reject large Git blobs introduced between two revisions."""

import subprocess
import sys

LIMIT = 10 * 1024 * 1024


def git(*args, input=None):
    return subprocess.check_output(["git", *args], input=input)


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: check_new_blob_sizes.py BASE HEAD")
    base, head = sys.argv[1:]
    objects = git("rev-list", "--objects", head, "--not", base)
    ids = [line.split(b" ", 1)[0] for line in objects.splitlines()]
    if not ids:
        return
    metadata = git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                   input=b"\n".join(ids) + b"\n")
    paths = {line.split(b" ", 1)[0]: line.partition(b" ")[2]
             for line in objects.splitlines()}
    large = []
    for line in metadata.splitlines():
        oid, kind, size = line.split()
        if kind == b"blob" and int(size) > LIMIT:
            large.append((int(size), paths.get(oid, b"").decode(errors="replace")))
    if large:
        for size, path in sorted(large, reverse=True):
            print(f"{path}: {size / 1048576:.1f} MiB (limit: 10 MiB)", file=sys.stderr)
        sys.exit("Large files should be distributed separately, not committed to Git history.")


if __name__ == "__main__":
    main()
