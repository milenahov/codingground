#!/usr/bin/env python3
"""Rasterize a .pptx/.ppt/.pdf deck into one PNG per slide.

Requires LibreOffice (`soffice`) and poppler (`pdftoppm`) on PATH — both
free/open-source and CPU-only.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", help="path to the .pptx/.ppt/.pdf deck")
    parser.add_argument("-o", "--outdir", default="slides")
    parser.add_argument(
        "--dpi", type=int, default=150, help="output image resolution (default: 150)"
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    pdf_path = args.deck
    tmp_dir = None
    if not args.deck.lower().endswith(".pdf"):
        tmp_dir = tempfile.mkdtemp(prefix="ppt_to_slides_")
        subprocess.run(
            [
                "soffice", "--headless", "--convert-to", "pdf",
                "--outdir", tmp_dir, args.deck,
            ],
            check=True,
        )
        stem = os.path.splitext(os.path.basename(args.deck))[0]
        pdf_path = os.path.join(tmp_dir, f"{stem}.pdf")
        if not os.path.exists(pdf_path):
            sys.exit(f"LibreOffice conversion failed: {pdf_path} not found")

    prefix = os.path.join(args.outdir, "slide")
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(args.dpi), pdf_path, prefix],
        check=True,
    )

    if tmp_dir:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # pdftoppm names files slide-1.png, slide-2.png, ... (or slide-01.png with
    # padding depending on page count) — renumber to a stable slide_NNN.png.
    produced = sorted(glob.glob(f"{prefix}-*.png"))
    for i, path in enumerate(produced, start=1):
        target = os.path.join(args.outdir, f"slide_{i:03d}.png")
        os.rename(path, target)

    print(f"Wrote {len(produced)} slide(s) to {args.outdir}/")


if __name__ == "__main__":
    main()
