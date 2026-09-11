#!/usr/bin/env python3
"""Concatenate per-slide segment videos (in order) into the final demo video.
Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import os
import subprocess
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments", nargs="+", help="segment mp4 files, in order")
    parser.add_argument("-o", "--output", default="demo.mp4")
    args = parser.parse_args()

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for path in args.segments:
            f.write(f"file '{os.path.abspath(path)}'\n")
        list_path = f.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_path, "-c", "copy", args.output,
            ],
            check=True,
        )
    finally:
        os.unlink(list_path)

    print(f"Wrote final demo video: {args.output} ({len(args.segments)} slide(s))")


if __name__ == "__main__":
    main()
