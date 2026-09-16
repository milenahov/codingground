#!/usr/bin/env python3
"""One command: slides + the avatar clips Kaggle produced -> final demo.mp4.

Pairs slide_NNN.png with avatar_NNN.mp4 by number, composites each, then
stitches them in order. Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def index_of(path: str) -> int:
    match = re.search(r"(\d+)(?=\.[^.]+$)", os.path.basename(path))
    if not match:
        sys.exit(f"Cannot read a slide number from {path}")
    return int(match.group(1))


def by_index(pattern: str) -> dict[int, str]:
    return {index_of(p): p for p in glob.glob(pattern)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides", default="slides", help="dir of slide_NNN.png")
    parser.add_argument(
        "--segments", default="segments", help="dir of avatar_NNN.mp4 from Kaggle"
    )
    parser.add_argument("-o", "--output", default="demo.mp4")
    parser.add_argument("--resolution", default="1280x720")
    parser.add_argument("--pip-width", type=int, default=320)
    parser.add_argument("--corner", default="bottom-right")
    args = parser.parse_args()

    slides = by_index(os.path.join(args.slides, "slide_*.png"))
    avatars = by_index(os.path.join(args.segments, "avatar_*.mp4"))

    missing = sorted(set(slides) ^ set(avatars))
    if missing:
        sys.exit(
            f"Slides and avatar clips don't line up — unmatched number(s): {missing}. "
            "Every slide needs exactly one narration segment."
        )
    if not slides:
        sys.exit(f"No slides found in {args.slides}/")

    with tempfile.TemporaryDirectory() as tmp:
        composed = []
        for i in sorted(slides):
            out = os.path.join(tmp, f"segment_{i:03d}.mp4")
            subprocess.run(
                [
                    sys.executable, os.path.join(HERE, "compose_slide_avatar.py"),
                    slides[i], avatars[i], "-o", out,
                    "--resolution", args.resolution,
                    "--pip-width", str(args.pip_width),
                    "--corner", args.corner,
                ],
                check=True,
            )
            composed.append(out)

        subprocess.run(
            [
                sys.executable, os.path.join(HERE, "concat_segments.py"),
                *composed, "-o", args.output,
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
