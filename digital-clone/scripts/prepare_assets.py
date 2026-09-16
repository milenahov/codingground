#!/usr/bin/env python3
"""One command: raw phone video -> a Kaggle-ready asset folder.

Produces voice_reference.wav + face_clip.mp4 (and copies slides_script.json
if given) into a single folder to upload as one private Kaggle dataset.
Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run_tool(script: str, *args: str) -> None:
    subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="raw source video, straight off the phone")
    parser.add_argument("-o", "--outdir", default="kaggle_assets")
    parser.add_argument(
        "--slides-script", help="optional slides_script.json to bundle along"
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    run_tool(
        "extract_voice_sample.py",
        args.video,
        "-o", os.path.join(args.outdir, "voice_reference.wav"),
    )
    run_tool(
        "prepare_face_clip.py",
        args.video,
        "-o", os.path.join(args.outdir, "face_clip.mp4"),
    )

    if args.slides_script:
        shutil.copy(args.slides_script, os.path.join(args.outdir, "slides_script.json"))

    print(
        f"\nAssets ready in {args.outdir}/\n"
        "Next: upload that folder to Kaggle as a PRIVATE dataset, attach it to\n"
        "the notebook, set DATASET_DIR to match, and Run All."
    )


if __name__ == "__main__":
    main()
