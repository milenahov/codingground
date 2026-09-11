#!/usr/bin/env python3
"""Composite one slide image with its avatar clip: slide fills the frame,
avatar sits as a picture-in-picture in a corner. Duration follows the avatar
clip (and its audio). Requires ffmpeg on PATH. CPU-only.
"""
import argparse
import subprocess

CORNERS = {
    "bottom-right": "W-w-{m}:H-h-{m}",
    "bottom-left": "{m}:H-h-{m}",
    "top-right": "W-w-{m}:{m}",
    "top-left": "{m}:{m}",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slide", help="static slide image (png/jpg)")
    parser.add_argument("avatar", help="avatar clip with matching audio (mp4)")
    parser.add_argument("-o", "--output", default="segment.mp4")
    parser.add_argument("--resolution", default="1280x720")
    parser.add_argument("--pip-width", type=int, default=320)
    parser.add_argument("--corner", choices=CORNERS, default="bottom-right")
    parser.add_argument("--margin", type=int, default=40)
    args = parser.parse_args()

    width, height = args.resolution.split("x")
    overlay_pos = CORNERS[args.corner].format(m=args.margin)

    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1[bg];"
        f"[1:v]scale={args.pip_width}:-1[pip];"
        f"[bg][pip]overlay={overlay_pos}:shortest=1[v]"
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", args.slide,
            "-i", args.avatar,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest",
            args.output,
        ],
        check=True,
    )
    print(f"Wrote segment: {args.output}")


if __name__ == "__main__":
    main()
