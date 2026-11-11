#!/usr/bin/env python3
"""Narration: one text-to-speech clip per script line, laid out on one track, with the start time of every word.

  python voice/voice.py <slug>        # reads videos/<slug>/script.json

Writes out/<slug>/voice.wav and out/<slug>/timing.json:
  {"duration": s, "lines": [{"text", "start", "end", "words": [[t0, t1, word], ...]}, ...]}
The animation reads timing.json, so every visual beat can land exactly on a spoken word.

Uses Microsoft Edge's free online voices (edge-tts). List them with:  edge-tts --list-voices
"""
import asyncio
import json
import subprocess
import sys
import time
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
DEFAULTS = {"voice": "en-US-AndrewNeural", "rate": "+0%", "lead_in": 0.3, "tail": 1.0, "gap": 0.45}


def load_script(slug):
    spec = {**DEFAULTS, **json.loads((ROOT / "videos" / slug / "script.json").read_text(encoding="utf-8"))}
    n = len(spec["lines"])
    gaps = spec.get("gaps") or [spec["gap"]] * n  # pause AFTER each line (s)
    spec["gaps"] = (list(gaps) + [spec["gap"]] * n)[:n]
    return spec


async def tts(text, voice, rate, mp3):
    """Speak one line; return [[t0, t1, word], ...] in seconds from the clip start."""
    com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                t0 = chunk["offset"] / 1e7
                words.append([round(t0, 3), round(t0 + chunk["duration"] / 1e7, 3), chunk["text"]])
    return words


def decode(mp3):
    """mp3 -> float32 mono samples at SR."""
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-v", "error", "-i", str(mp3), "-f", "s16le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768


def main(slug):
    spec = load_script(slug)
    out = ROOT / "out" / slug
    (out / "lines").mkdir(parents=True, exist_ok=True)
    clips, lines, t = [], [], spec["lead_in"]
    for i, text in enumerate(spec["lines"]):
        mp3 = out / "lines" / f"{i:02d}.mp3"
        cache = mp3.with_suffix(".json")
        key = {"text": text, "voice": spec["voice"], "rate": spec["rate"]}
        if cache.exists() and mp3.exists() and json.loads(cache.read_text()).get("key") == key:
            words = json.loads(cache.read_text())["words"]  # unchanged line: no new request
        else:
            for attempt in range(6):  # the free service sometimes answers "no audio" when busy
                try:
                    words = asyncio.run(tts(text, spec["voice"], spec["rate"], mp3))
                    break
                except Exception as e:  # noqa: BLE001 - any network/service failure is worth a retry
                    print(f"line {i}: {type(e).__name__}, retry {attempt + 1}/6", flush=True)
                    time.sleep(4 + 4 * attempt)
            else:
                sys.exit(f"line {i}: no audio after 6 tries")
            cache.write_text(json.dumps({"key": key, "words": words}))
        audio = decode(mp3)
        # the service pads each clip with silence: trim it so the gaps in script.json are the real pauses
        loud = np.flatnonzero(np.abs(audio) > 0.01)
        a, b = (loud[0], loud[-1] + int(0.08 * SR)) if loud.size else (0, len(audio))
        cut = max(0, a - int(0.03 * SR))
        audio, shift = audio[cut:b], cut / SR
        clips.append((t, audio))
        lines.append({"text": text, "start": round(t, 3), "end": round(t + len(audio) / SR, 3),
                      "words": [[round(t + w0 - shift, 3), round(t + w1 - shift, 3), w] for w0, w1, w in words]})
        t += len(audio) / SR + spec["gaps"][i]
    dur = t - spec["gaps"][-1] + spec["tail"]
    track = np.zeros(int(dur * SR) + 1, dtype=np.float32)
    for start, audio in clips:
        i = int(start * SR)
        track[i:i + len(audio)] += audio[:len(track) - i]
    with wave.open(str(out / "voice.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype("<i2").tobytes())
    (out / "timing.json").write_text(json.dumps({"duration": round(dur, 3), "lines": lines}, indent=1))
    for i, ln in enumerate(lines):
        print(f"line {i}: {ln['start']:6.2f}s  " + " ".join(f"{w}@{t0:.2f}" for t0, _, w in ln["words"]))
    print(f"voice: {dur:.2f}s -> {out / 'voice.wav'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
