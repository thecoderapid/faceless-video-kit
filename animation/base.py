"""Base scene: every animation beat waits for the spoken word it belongs to.

  class Video(VoicedScene):
      def build(self):
          title = txt("Why is the sky blue?")
          self.at(self.w(0, "sky"))        # wait until the narrator says "sky" in line 0
          self.sfx("pop")                  # log a sound effect at this moment
          self.play(FadeIn(title))

make.py sets KIT_SLUG (which video) and KIT_FORMAT (vertical 9:16 or wide 16:9) before rendering.
Captions are not drawn here: make.py burns them in afterwards (animation/captions.py), so camera moves
never drag them around.
"""
import json
import os
from pathlib import Path

import numpy as np
from manim import ImageMobject, MovingCameraScene, config, rate_functions
from PIL import Image, ImageDraw, ImageFilter

from animation import theme

ROOT = Path(__file__).resolve().parents[1]
SLUG = os.environ.get("KIT_SLUG", "example")
FORMAT = os.environ.get("KIT_FORMAT", "vertical")
OUT = ROOT / "out" / SLUG
config.frame_width, config.frame_height = (9, 16) if FORMAT == "vertical" else (16, 9)
config.background_color = theme.PAPER
SMOOTH, SNAP = rate_functions.ease_in_out_cubic, rate_functions.ease_out_back


def backdrop(width=None, height=None, center=(0, 0), px=90):
    """Dot grid + soft colour glows as ONE image (thousands of dots as shapes would slow every frame).
    Make it bigger than the frame if the camera travels."""
    w = width or config.frame_width
    h = height or config.frame_height
    rgb = lambda c: tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))  # noqa: E731
    cache = ROOT / "out" / "_cache" / f"bg_{w}x{h}_{'_'.join(c[1:] for c in theme.GLOWS)}.png"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        W, H = int(w * px), int(h * px)
        img = Image.new("RGB", (W, H), rgb(theme.PAPER))
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        g = ImageDraw.Draw(glow)
        spots = ((0.15, 0.2), (0.85, 0.8), (0.8, 0.15))
        for (fx, fy), col in zip(spots, theme.GLOWS):
            r = min(W, H) * 0.35
            g.ellipse([fx * W - r, fy * H - r, fx * W + r, fy * H + r], fill=tuple(int(v * 0.12) for v in rgb(col)))
        glow = glow.filter(ImageFilter.GaussianBlur(px * 2))
        img = Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(glow, np.int16), 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        step, dot = px // 2, max(2, px // 45)
        for x in range(step // 2, W, step):
            for y in range(step // 2, H, step):
                d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=rgb(theme.LINE))
        img.save(cache)
    bg = ImageMobject(str(cache)).stretch_to_fit_width(w).stretch_to_fit_height(h)
    bg.move_to([center[0], center[1], 0]).set_z_index(-20)
    return bg


class VoicedScene(MovingCameraScene):
    def setup(self):
        super().setup()
        timing = json.loads((OUT / "timing.json").read_text())
        self.lines, self.total = timing["lines"], timing["duration"]  # not self.duration: Manim uses that name
        self.cues = []
        self._angle = 0.0

    def construct(self):
        self.build()
        self.at(self.total)  # hold the last frame until the narration ends

    def build(self):
        raise NotImplementedError("write your animation in build()")

    def tear_down(self):
        (OUT / "cues.json").write_text(json.dumps(self.cues, indent=1))

    # ---- timing ----
    def w(self, line, word, nth=0):
        """Time the narrator starts saying `word` (its nth occurrence) in script line `line` (0-based)."""
        norm = lambda s: s.lower().replace("’", "'").strip(".,?!:;\"")  # noqa: E731
        hits = [x[0] for x in self.lines[line]["words"] if norm(x[2]) == norm(word)]
        if len(hits) <= nth:
            spoken = " ".join(x[2] for x in self.lines[line]["words"])
            raise KeyError(f"word {word!r} (#{nth}) not in line {line}: {spoken}")
        return hits[nth]

    def start(self, line):
        return self.lines[line]["start"]

    def at(self, t):
        """Wait until time t (seconds). If we're already past it, carry on."""
        if t - self.time >= 1 / config.frame_rate:  # shorter than one frame: nothing to wait for
            self.wait(t - self.time)

    def sfx(self, kind, t=None):
        """Log a sound effect (see sound/sfx.py KINDS) now, or at time t."""
        self.cues.append({"t": round(self.time if t is None else t, 3), "kind": kind})

    # ---- camera ----
    @property
    def cam(self):
        return self.camera.frame

    def fly(self, to, width=None, angle=0.0, run_time=1.0, rate_func=SMOOTH):
        """Move the camera to a point, zoom (frame width) and tilt (radians), smoothly."""
        target = self.cam.copy().rotate(-self._angle)
        target.scale_to_fit_width(width or config.frame_width).move_to(to).rotate(angle)
        self._angle = angle
        self.play(self.cam.animate.become(target), run_time=run_time, rate_func=rate_func)

    def drop(self, *groups):
        """Remove finished stages completely (including pieces Manim added on their own)."""
        fam = set()
        for g in groups:
            fam.update(g.get_family())
        self.remove(*[m for m in self.mobjects if fam.intersection(m.get_family())])
