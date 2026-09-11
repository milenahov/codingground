#!/usr/bin/env python3
"""Normalize the source video for Wav2Lip: trim silent bookends, re-encode
to a consistent H.264/yuv420p format. Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import subprocess
import sys

from extract_voice_sample import probe_duration


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="path to the raw source video")
    parser.add_argument("-o", "--output", default="face_clip.mp4")
    parser.add_argument(
        "--skip-start", type=float, default=1.5,
        help="seconds to trim from the start (default: 1.5)",
    )
    parser.add_argument(
        "--skip-end", type=float, default=1.5,
        help="seconds to trim from the end (default: 1.5)",
    )
    parser.add_argument(
        "--fps", type=int, default=25,
        help="output frame rate Wav2Lip expects (default: 25)",
    )
    args = parser.parse_args()

    duration = probe_duration(args.video)
    end = duration - args.skip_end
    if end <= args.skip_start:
        sys.exit(
            f"Video is only {duration:.1f}s — not enough left after "
            f"trimming {args.skip_start}s/{args.skip_end}s from each end."
        )

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", args.video,
            "-ss", str(args.skip_start), "-to", str(end),
            "-r", str(args.fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-an",
            args.output,
        ],
        check=True,
    )
    print(f"Wrote face clip: {args.output} ({end - args.skip_start:.1f}s @ {args.fps}fps)")


if __name__ == "__main__":
    main()
