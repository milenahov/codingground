# Digital Clone

Turn one 30–60s selfie video into a reusable voice + lip-sync pipeline: type any
script, get back a video of yourself saying it.

## How it works

1. **Voice cloning** — [Coqui XTTS-v2](https://github.com/coqui-ai/TTS) generates
   speech in your voice from a few seconds of reference audio plus arbitrary text.
2. **Lip-sync** — [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) re-renders your
   source video so your mouth matches the newly generated audio.
3. Both models need a GPU. The notebook in `notebook/` is written to run on
   **Kaggle's free GPU tier** (T4/P100) — no local GPU required.

## Workflow

1. Record and send the source video (see requirements below).
2. Run the local prep scripts on it (CPU-only, no GPU needed):
   - `scripts/extract_voice_sample.py` — pulls a clean voice reference clip out
     of the video.
   - `scripts/prepare_face_clip.py` — trims the silent lead-in/lead-out and
     normalizes the video for Wav2Lip.
3. Upload the two prepared files (`voice_reference.wav`, `face_clip.mp4`) to
   Kaggle as a private dataset, attach it to `notebook/digital_clone_kaggle.ipynb`.
4. Open the notebook on Kaggle, edit `SCRIPT_TEXT` in the first cell, **Run All**.
5. Download `output.mp4` from `/kaggle/working/`.

## PPT demo video (script + slides → narrated avatar demo)

For a full "AI-narrated" project demo instead of one clip:

1. Convert your deck to slide images: `scripts/ppt_to_slides.py deck.pptx -o slides/`.
2. Write `slides_script.json` — one narration line per slide, in the same
   order as the slides:
   ```json
   [
     {"slide": "slide_001.png", "text": "This project solves..."},
     {"slide": "slide_002.png", "text": "The architecture is..."}
   ]
   ```
3. Add `slides_script.json` to the Kaggle dataset alongside
   `voice_reference.wav` / `face_clip.mp4`, then run **section 6** of the
   notebook. It generates one voice-cloned, lip-synced avatar clip per slide
   into `segments/avatar_001.mp4`, `avatar_002.mp4`, …
4. Download `segments/` locally. For each slide, composite the avatar as a
   picture-in-picture over the slide image:
   `scripts/compose_slide_avatar.py slides/slide_001.png segments/avatar_001.mp4 -o out/segment_001.mp4`
5. Stitch the segments into the final demo:
   `scripts/concat_segments.py out/segment_*.mp4 -o demo.mp4`

Steps 1, 4 and 5 are CPU-only (ffmpeg + LibreOffice/poppler) — no Kaggle GPU
needed for those; only step 3 (voice cloning + lip-sync) runs on Kaggle.

Requires `soffice` (LibreOffice) and `pdftoppm` (poppler-utils) on whatever
machine runs `ppt_to_slides.py`.

## Source video requirements

- 30–60 seconds, front camera, phone propped up at eye level (not handheld).
- Soft light facing the subject, plain background, quiet room.
- 2 seconds still + mouth closed at the very start and end.
- Natural speech in between, face fully visible (no hands/hair over the mouth).
- Unedited, straight off the phone.

## Notes

- `SCRIPT_TEXT` defaults to: *"Hi, this is my digital clone. Everything you
  hear was typed, not recorded."* — override it with anything else in the
  notebook's first cell.
- Raw video/audio and generated outputs are gitignored — this repo only holds
  code, not media.
