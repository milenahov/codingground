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
