# Digital Clone

Type any script, get back a video of yourself saying it — from either a
recorded clip or a single photo.

## How it works

1. **Voice cloning** — [Coqui XTTS-v2](https://github.com/coqui-ai/TTS) generates
   speech in your voice from a few seconds of reference audio plus arbitrary text,
   any length (long scripts are split into sentences and stitched back together).
2. **Animation** — one of two engines, chosen by `MODE` in the notebook:
   - `MODE = "video"` — [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) re-renders
     your source video so your mouth matches the newly generated audio.
   - `MODE = "image"` — [SadTalker](https://github.com/OpenTalker/SadTalker)
     animates a single still photo into a full talking-head video, as long as
     the audio requires — no recorded clip needed.
3. Both engines need a GPU. The notebook in `notebook/` is written to run on
   **Kaggle's free GPU tier** (T4/P100) — no local GPU required.

## Workflow — video mode

1. Record the source video (see requirements below).
2. Run the local prep scripts on it (CPU-only, no GPU needed):
   - `scripts/extract_voice_sample.py` — pulls a clean voice reference clip out
     of the video.
   - `scripts/prepare_face_clip.py` — trims the silent lead-in/lead-out and
     normalizes the video for Wav2Lip.
   - Or do both in one step: `scripts/prepare_assets.py raw_video.mp4 -o kaggle_assets/`.
3. Upload `kaggle_assets/` (`voice_reference.wav`, `face_clip.mp4`) to Kaggle
   as a private dataset, attach it to `notebook/digital_clone_kaggle.ipynb`.
4. In the notebook, set `MODE = "video"`, edit `SCRIPT_TEXT`, **Run All**.
5. Download `output.mp4` from `/kaggle/working/`.

## Workflow — image mode (one photo, no recording)

1. Take one clear, forward-facing, well-lit photo (`photo.jpg`).
2. Provide a short voice sample separately — either a clean recording of just
   your voice, or reuse `voice_reference.wav` extracted from any earlier video.
3. Upload both (`voice_reference.wav`, `photo.jpg`) to Kaggle as a private dataset.
4. In the notebook, set `MODE = "image"`, edit `SCRIPT_TEXT`, **Run All**. Section 2b
   fetches SadTalker's checkpoints; section 4 generates the full video, matching
   however long the script's audio runs — not capped to a short loop.
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
3. Add `slides_script.json` to the Kaggle dataset alongside your voice/face
   assets, then run **section 6** of the notebook. It generates one
   voice-cloned avatar clip per slide (video or image mode, same as above)
   into `segments/avatar_001.mp4`, `avatar_002.mp4`, …
4. Download `segments/` locally, next to `slides/`, and run
   `scripts/make_demo.py --slides slides --segments segments -o demo.mp4` —
   composites each slide with its avatar clip and stitches the final video
   in one step. (Or run `compose_slide_avatar.py` and `concat_segments.py`
   separately for more control over each segment.)

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
