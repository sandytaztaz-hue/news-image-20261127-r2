#!/usr/bin/env python3
"""Copy the pre-rendered entry.png into the output directory.

make.fun program/v1 entry: the program writes one image to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png). Node-free, Python
standard library only; the image itself is drawn at build time by render.py.
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "entry.png", OUT / "entry.png")


if __name__ == "__main__":
    main()
