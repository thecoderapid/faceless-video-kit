#!/usr/bin/env python3
"""The sound mixer: narration on top, effects quiet underneath, music ducked whenever the voice speaks,
then the whole mix normalised to -14 LUFS (YouTube / TikTok loudness).

  python sound/mix.py <silent.mp4> <cues.json> <voice.wav> <out.mp4> [music file] [music volume] [fx volume]

cues.json = [{"t": seconds, "kind": "pop"}, ...]  (written by the animation, see animation/base.py)
Music is optional and is looped if shorter than the video. Only use music you have the rights to,
and credit it in the description if its licence asks for that.
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from sfx import SR, sound  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
MUSIC_VOLUME = 0.06  # quiet bed: viewers must hear every word
FX_VOLUME = 0.35     # effects support the picture, they never compete with the voice


def duration(video):
    return imageio_ffmpeg.count_frames_and_secs(str(video))[1]


def write_wav(path, samples, sr):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())


def main(video, cues, voice, out, music=None, music_volume=MUSIC_VOLUME, fx_volume=FX_VOLUME):
    dur = duration(video)
    fx = np.zeros(int((dur + 1) * SR))
    for c in json.loads(Path(cues).read_text()):
        s = sound(c["kind"])
        i = int(c["t"] * SR)
        fx[i:i + len(s)] += s[:max(0, len(fx) - i)]
    with tempfile.TemporaryDirectory() as tmp:
        fx_wav = Path(tmp) / "fx.wav"
        write_wav(fx_wav, fx, SR)
        inputs = ["-i", str(video), "-i", str(voice), "-i", str(fx_wav)]
        graph = f"[2:a]volume={fx_volume}[f];"
        if music:
            inputs += ["-stream_loop", "-1", "-i", str(music)]
            graph += (f"[3:a]volume={music_volume},afade=t=in:d=0.8,afade=t=out:st={max(0, dur - 1.5):.2f}:d=1.5[m];"
                      "[1:a]asplit[v][key];"
                      "[m][key]sidechaincompress=threshold=0.015:ratio=10:attack=15:release=450[md];"
                      "[md][f][v]amix=inputs=3:duration=first:normalize=0,")
        else:
            graph += "[1:a][f]amix=inputs=2:duration=first:normalize=0,"
        graph += "apad,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
        cmd = [FF, "-nostdin", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
               "-map", "0:v", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr[-1500:])
    print(f"mixed: {out} ({dur:.1f}s{', music ' + Path(music).name if music else ', no music'})")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 4:
        sys.exit(__doc__)
    main(*a[:4], a[4] if len(a) > 4 else None, *(float(v) for v in a[5:7]))
