#!/usr/bin/env python3
"""Pull a clean voice-reference clip out of the source video.

Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import subprocess
import sys


def probe_duration(video_path: str) -> float:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="path to the raw source video")
    parser.add_argument("-o", "--output", default="voice_reference.wav")
    parser.add_argument(
        "--skip-start", type=float, default=2.0,
        help="seconds of silent lead-in to skip (default: 2.0)",
    )
    parser.add_argument(
        "--skip-end", type=float, default=2.0,
        help="seconds of silent lead-out to skip (default: 2.0)",
    )
    args = parser.parse_args()

    duration = probe_duration(args.video)
    end = duration - args.skip_end
    if end <= args.skip_start:
        sys.exit(
            f"Video is only {duration:.1f}s — not enough speech left after "
            f"trimming {args.skip_start}s/{args.skip_end}s from each end."
        )

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", args.video,
            "-ss", str(args.skip_start), "-to", str(end),
            "-vn", "-ac", "1", "-ar", "24000", "-acodec", "pcm_s16le",
            args.output,
        ],
        check=True,
    )
    print(f"Wrote voice reference: {args.output} ({end - args.skip_start:.1f}s)")


if __name__ == "__main__":
    main()
