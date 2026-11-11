#!/usr/bin/env python3
"""One command from script to finished video.

  python make.py <slug>                 # videos/<slug>/script.json + scene.py -> out/<slug>/final.mp4
  python make.py <slug> --draft         # fast low-res render to check the animation
  python make.py <slug> --music "audio/My Track.mp3"

Steps: voice (voice/voice.py) -> animation (Manim renders videos/<slug>/scene.py, silent)
       -> sound (sound/mix.py: voice + effects + ducked music, -14 LUFS) -> captions burned in.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from animation import captions  # noqa: E402

PY = sys.executable


def step(name, cmd, env=None):
    print(f"\n== {name}", flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    if r.returncode:
        sys.exit(f"{name} failed (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--draft", action="store_true", help="low resolution, faster")
    ap.add_argument("--music", help="music file (looped, ducked under the voice)")
    ap.add_argument("--skip-voice", action="store_true", help="reuse out/<slug>/voice.wav")
    a = ap.parse_args()

    vdir, out = ROOT / "videos" / a.slug, ROOT / "out" / a.slug
    script = json.loads((vdir / "script.json").read_text(encoding="utf-8"))
    fmt = script.get("format", "vertical")
    W, H = (1080, 1920) if fmt == "vertical" else (1920, 1080)
    if a.draft:
        W, H = W // 2, H // 2

    if not a.skip_voice:
        step("voice", [PY, "voice/voice.py", a.slug])

    env = {**os.environ, "KIT_SLUG": a.slug, "KIT_FORMAT": fmt, "PYTHONPATH": str(ROOT), "PYTHONUTF8": "1"}
    media = out / "manim"
    step("animation", [PY, "-m", "manim", "render", "-q", "l" if a.draft else "h", "--resolution", f"{W},{H}",
                       "--frame_rate", "30", "-v", "WARNING", "--progress_bar", "none", "--media_dir", str(media), "-o", "silent",
                       str(vdir / "scene.py"), "Video"], env)
    silent = next(media.glob("videos/**/silent.mp4"))

    mixed = out / "mixed.mp4"
    step("sound", [PY, "sound/mix.py", str(silent), str(out / "cues.json"), str(out / "voice.wav"), str(mixed),
                   *([a.music] if a.music else [])])

    print("\n== captions", flush=True)
    timing = json.loads((out / "timing.json").read_text())
    ass = ROOT / "_captions.ass"  # libass wants a plain relative path; fonts/ supplies Poppins
    ass.write_text(captions.build(timing, fmt), encoding="utf-8")
    final = out / ("draft.mp4" if a.draft else "final.mp4")
    vf = "subtitles=_captions.ass:fontsdir=fonts"  # PlayRes is full size; libass scales it to drafts
    try:
        r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-y", "-loglevel", "error", "-i", str(mixed),
                            "-vf", vf, "-c:a", "copy", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)], cwd=ROOT)
    finally:
        ass.unlink(missing_ok=True)
    if r.returncode:
        sys.exit("captions failed")
    print(f"\ndone: {final}")


if __name__ == "__main__":
    main()
