"""Sound effects synthesized in code (no sample files, no licences to worry about).

  sound("pop") -> float numpy array at SR. Kinds: see KINDS. Add your own by adding a branch.
"""
import numpy as np

SR = 44100
rng = np.random.default_rng(7)
KINDS = ("click", "pop", "ding", "whoosh", "hit", "tick", "chop", "buzz", "powerup", "flip")


def env(n, attack=0.004, decay=8.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t * decay)


def tone(freq, dur, decay=8.0, amp=0.3):
    t = np.arange(int(dur * SR)) / SR
    f = np.broadcast_to(freq, t.shape) if np.ndim(freq) else np.full(t.shape, float(freq))
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), decay=decay)


def noise(dur, decay=30.0, amp=0.3, smooth=1):
    n = rng.standard_normal(int(dur * SR))
    if smooth > 1:  # crude low-pass: moving average
        n = np.convolve(n, np.ones(smooth) / smooth, mode="same")
    return amp * n * env(len(n), decay=decay)


def layer(*parts):
    """Sum sounds of different lengths."""
    out = np.zeros(max(len(p) for p in parts))
    for p in parts:
        out[:len(p)] += p
    return out


def at(out, d, s):
    """Add sound s into out starting at d seconds."""
    i = int(d * SR)
    out[i:i + len(s)] += s[:max(0, len(out) - i)]
    return out


def sound(kind):
    if kind == "click":  # one keyboard key
        return layer(noise(0.03, decay=160, amp=0.35, smooth=3), tone(rng.uniform(1800, 2600), 0.02, decay=200, amp=0.08))
    if kind == "pop":  # something appears
        return tone(np.linspace(380, 760, int(0.07 * SR)), 0.07, decay=40, amp=0.35)
    if kind == "ding":  # success: two bell tones
        out = np.zeros(int(1.1 * SR))
        at(out, 0, tone(1046, 0.9, decay=4, amp=0.22) + tone(2093, 0.9, decay=6, amp=0.06))
        return at(out, 0.12, tone(1568, 0.9, decay=4, amp=0.2))
    if kind == "whoosh":  # camera move / transition
        n = noise(0.45, decay=0, amp=0.18, smooth=12)
        return n * np.sin(np.linspace(0, np.pi, len(n)))
    if kind == "hit":  # hook impact on frame 0: sub-bass drop + click
        t = np.arange(int(0.7 * SR)) / SR
        boom = 0.55 * np.sin(2 * np.pi * np.cumsum(np.linspace(90, 38, len(t))) / SR) * np.exp(-t * 5)
        return layer(boom, noise(0.02, decay=200, amp=0.3, smooth=2))
    if kind == "tick":  # clock tick
        return layer(tone(1500, 0.05, decay=90, amp=0.3), noise(0.02, decay=200, amp=0.15, smooth=2))
    if kind == "chop":  # stamp / blade: low thump + metallic ring
        return layer(tone(np.linspace(120, 60, int(0.35 * SR)), 0.35, decay=9, amp=0.5),
                     tone(2400, 0.6, decay=7, amp=0.06), noise(0.06, decay=60, amp=0.25, smooth=2))
    if kind == "buzz":  # wrong answer: two detuned square waves
        t = np.arange(int(0.45 * SR)) / SR
        sq = np.sign(np.sin(2 * np.pi * 110 * t)) + 0.6 * np.sign(np.sin(2 * np.pi * 116 * t))
        return 0.13 * sq * env(len(t), decay=3.5)
    if kind == "powerup":  # rising whine + soft chime
        t = np.arange(int(0.7 * SR)) / SR
        whine = 0.18 * np.sin(2 * np.pi * np.cumsum(np.linspace(80, 620, len(t))) / SR) * np.minimum(1, t / 0.15)
        out = at(np.zeros(int(1.2 * SR)), 0, whine * np.linspace(1, 0.3, len(whine)))
        return at(out, 0.6, tone(1318, 0.5, decay=6, amp=0.15))
    if kind == "flip":  # page flip: a quick swell of soft noise
        n = noise(0.28, decay=0, amp=0.22, smooth=6)
        return n * np.sin(np.linspace(0, np.pi, len(n))) ** 2
    raise ValueError(f"unknown sound {kind!r}; choose from {KINDS}")
