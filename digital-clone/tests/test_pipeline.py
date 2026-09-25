#!/usr/bin/env python3
"""End-to-end test of everything that does not need a GPU.

Builds synthetic stand-ins for the source video, photo and deck, then runs the
real scripts and the notebook's own cells — stubbing only the two model
inferences (XTTS, Wav2Lip/SadTalker), which need a GPU and pretrained weights.

That covers the wiring the GPU run depends on: filenames, ordering, the
hand-off from the notebook's `segments/` to make_demo.py, and slide timings
tracking each narration line.

    python3 digital-clone/tests/test_pipeline.py

Needs ffmpeg, ffprobe, pdftoppm, numpy, soundfile.
"""
import json
import os
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
NOTEBOOK = os.path.join(ROOT, "notebook", "digital_clone_kaggle.ipynb")

SLIDE_LINES = [
    "This project automates our reporting pipeline.",
    "It cuts a two-day manual process to about ten minutes. The team reviews only exceptions now.",
    "Next quarter we extend it to the finance data set.",
]

run = subprocess.run


def sh(*cmd, **kw):
    return run([str(c) for c in cmd], check=True, capture_output=True, text=True, **kw)


def duration(path):
    out = sh("ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path)
    return float(out.stdout.strip())


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------
def make_source_video(path, seconds=40):
    sh("ffmpeg", "-y", "-loglevel", "error",
       "-f", "lavfi", "-i", f"testsrc=size=720x1280:rate=30:duration={seconds}",
       "-f", "lavfi", "-i", f"sine=frequency=200:duration={seconds}",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)


def make_photo(path):
    sh("ffmpeg", "-y", "-loglevel", "error",
       "-f", "lavfi", "-i", "color=c=gray:s=512x512", "-frames:v", "1", path)


def make_deck_pdf(path, pages):
    """Hand-rolled PDF so the test needs no PDF library."""
    objs, out = [], bytearray(b"%PDF-1.4\n")

    def add(body):
        objs.append(len(out))
        out.extend(f"{len(objs)} 0 obj\n".encode() + body + b"\nendobj\n")

    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(pages))
    add(b"<< /Type /Catalog /Pages 2 0 R >>")
    add(f"<< /Type /Pages /Kids [{kids}] /Count {pages} >>".encode())
    for i in range(1, pages + 1):
        stream = f"BT /F1 60 Tf 60 400 Td (Slide {i}) Tj ET".encode()
        add(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {4 + 2 * (i - 1)} 0 R /Resources << /Font << /F1 << /Type /Font "
            f"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>".encode())
        add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

    start = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in objs:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
               f"startxref\n{start}\n%%EOF\n".encode())
    open(path, "wb").write(bytes(out))


# --------------------------------------------------------------------------
# stubs for the GPU-only steps
# --------------------------------------------------------------------------
SAMPLE_RATE = 24000


class _FakeTTS:
    """Mimics TTS.api.TTS: .tts() returns samples, length tracking the text."""
    synthesizer = types.SimpleNamespace(output_sample_rate=SAMPLE_RATE)

    def __init__(self, *a, **k):
        pass

    def to(self, device):
        return self

    def tts(self, text, speaker_wav, language):
        assert os.path.exists(speaker_wav), f"voice reference missing: {speaker_wav}"
        return [0.0] * int(SAMPLE_RATE * 0.06 * len(text))


def _fake_run(cmd, *a, **kw):
    """Stand in for Wav2Lip / SadTalker: emit a real mp4 as long as the audio."""
    if isinstance(cmd, list) and cmd[:2] == ["bash", "scripts/download_models.sh"]:
        return types.SimpleNamespace(returncode=0)  # no real SadTalker clone here

    if isinstance(cmd, list) and "inference.py" in cmd:
        audio_flag = "--audio" if "--audio" in cmd else "--driven_audio"
        audio = cmd[cmd.index(audio_flag) + 1]
        out_flag = "--outfile" if "--outfile" in cmd else "--result_dir"
        dest = cmd[cmd.index(out_flag) + 1]
        if out_flag == "--result_dir":  # SadTalker writes into a nested dir
            os.makedirs(f"{dest}/nested", exist_ok=True)
            dest = f"{dest}/nested/generated.mp4"
        sh("ffmpeg", "-y", "-loglevel", "error",
           "-f", "lavfi", "-i", f"testsrc=size=256x256:rate=25:duration={duration(audio)}",
           "-i", audio, "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", dest)
        return types.SimpleNamespace(returncode=0)

    return run(cmd, *a, **kw)


def notebook_code_cells():
    nb = json.load(open(NOTEBOOK))
    cells = {}
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            src = c["source"]
            lines = src.split("\n") if isinstance(src, str) else src
            # drop IPython magics / shell escapes, which aren't valid Python
            cells[c["id"]] = "\n".join(
                l for l in lines if not l.lstrip().startswith(("!", "%"))
            )
    return cells


def run_notebook(work, mode, dataset):
    """Execute the notebook's real cells with only the models stubbed."""
    cells = notebook_code_cells()
    missing = {"params", "sad-ckpt", "speech", "animate", "slides"} - cells.keys()
    assert not missing, f"notebook is missing expected cells: {sorted(missing)}"

    fake_tts = types.ModuleType("TTS")
    fake_api = types.ModuleType("TTS.api")
    fake_api.TTS = _FakeTTS
    fake_tts.api = fake_api
    sys.modules["TTS"], sys.modules["TTS.api"] = fake_tts, fake_api

    ns = {"__name__": "__main__"}
    exec(cells["params"], ns)
    ns.update(
        MODE=mode,
        DATASET_DIR=dataset,
        VOICE_REFERENCE=f"{dataset}/voice_reference.wav",
        FACE_CLIP=f"{dataset}/face_clip.mp4",
        IMAGE_PATH=f"{dataset}/photo.jpg",
        WORK_DIR=work,
        WAV2LIP_DIR=f"{work}/Wav2Lip",
        SADTALKER_DIR=f"{work}/SadTalker",
        GENERATED_SPEECH=f"{work}/generated_speech.wav",
        OUTPUT_VIDEO=f"{work}/output.mp4",
        SCRIPT_TEXT=" ".join(SLIDE_LINES),
    )
    os.makedirs(ns["SADTALKER_DIR"], exist_ok=True)

    subprocess.run = _fake_run
    try:
        for cell in ("sad-ckpt", "speech", "animate", "slides"):
            exec(cells[cell], ns)
    finally:
        subprocess.run = run
    return ns


# --------------------------------------------------------------------------
def main():
    failures = []

    with tempfile.TemporaryDirectory() as tmp:
        dataset = os.path.join(tmp, "dataset")
        os.makedirs(dataset)

        print("building fixtures...")
        source = os.path.join(tmp, "raw_phone_video.mp4")
        make_source_video(source)
        make_photo(os.path.join(dataset, "photo.jpg"))
        make_deck_pdf(os.path.join(tmp, "deck.pdf"), len(SLIDE_LINES))
        json.dump(
            [{"slide": f"slide_{i:03d}.png", "text": t}
             for i, t in enumerate(SLIDE_LINES, start=1)],
            open(os.path.join(dataset, "slides_script.json"), "w"),
        )

        # --- prepare_assets.py -------------------------------------------
        sh(sys.executable, f"{SCRIPTS}/prepare_assets.py", source, "-o", dataset)
        for name in ("voice_reference.wav", "face_clip.mp4"):
            path = os.path.join(dataset, name)
            if not os.path.exists(path):
                failures.append(f"prepare_assets did not produce {name}")
        print(f"  prepare_assets  -> voice {duration(dataset + '/voice_reference.wav'):.1f}s, "
              f"face {duration(dataset + '/face_clip.mp4'):.1f}s")

        # --- ppt_to_slides.py --------------------------------------------
        slides_dir = os.path.join(tmp, "slides")
        sh(sys.executable, f"{SCRIPTS}/ppt_to_slides.py",
           os.path.join(tmp, "deck.pdf"), "-o", slides_dir, "--dpi", "60")
        slides = sorted(os.listdir(slides_dir))
        expected = [f"slide_{i:03d}.png" for i in range(1, len(SLIDE_LINES) + 1)]
        if slides != expected:
            failures.append(f"ppt_to_slides gave {slides}, expected {expected}")
        print(f"  ppt_to_slides   -> {len(slides)} slides, correctly ordered")

        # --- the notebook, both modes ------------------------------------
        for mode in ("video", "image"):
            work = os.path.join(tmp, f"work_{mode}")
            os.makedirs(work)
            run_notebook(work, mode, dataset)

            segments = os.path.join(work, "segments")
            avatars = sorted(f for f in os.listdir(segments) if f.startswith("avatar_"))
            want = [f"avatar_{i:03d}.mp4" for i in range(1, len(SLIDE_LINES) + 1)]
            if avatars != want:
                failures.append(f"[{mode}] segments gave {avatars}, expected {want}")
            if not os.path.exists(os.path.join(work, "output.mp4")):
                failures.append(f"[{mode}] single-clip output.mp4 missing")
            print(f"  notebook {mode:5s}  -> output.mp4 + {len(avatars)} per-slide clips")

            # --- make_demo.py --------------------------------------------
            demo = os.path.join(work, "demo.mp4")
            sh(sys.executable, f"{SCRIPTS}/make_demo.py",
               "--slides", slides_dir, "--segments", segments, "-o", demo)

            narration = sum(duration(os.path.join(segments, f"speech_{i:03d}.wav"))
                            for i in range(1, len(SLIDE_LINES) + 1))
            got = duration(demo)
            if abs(got - narration) > 0.5:
                failures.append(
                    f"[{mode}] demo is {got:.2f}s but narration totals {narration:.2f}s"
                )
            print(f"  make_demo {mode:4s} -> demo.mp4 {got:.2f}s "
                  f"(narration {narration:.2f}s)")

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASSED — everything but the GPU model inference is verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
