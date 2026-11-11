"""Look of the videos: colours, fonts and small building blocks. Change this file to rebrand every video.

Fonts: Poppins (text) and JetBrains Mono (numbers/code), both free (SIL Open Font License).
Run  python fonts/fetch.py  once; without them Manim falls back to a system font.
"""
from pathlib import Path

import manimpango
from manim import Circle, RoundedRectangle, Text, VGroup

FONTS = Path(__file__).resolve().parents[1] / "fonts"
for _f in sorted(FONTS.glob("*.ttf")):
    manimpango.register_font(str(_f))
SANS = "Poppins" if any(FONTS.glob("Poppins-*.ttf")) else "sans-serif"
MONO = "JetBrains Mono" if any(FONTS.glob("JetBrainsMono-*.ttf")) else "monospace"

# Dark theme. Give each accent ONE meaning and keep it: viewers learn the colour code.
PAPER, INK, MUTED, LINE, CARD = "#0E1117", "#E8ECF4", "#8A93A6", "#2A3142", "#161B26"
CORAL, TEAL, AMBER, CYAN, BLUE = "#FF5A5F", "#34D399", "#F5B53F", "#22D3EE", "#5B8CFF"
GLOWS = (CYAN, BLUE, AMBER)  # soft background glows


def txt(s, size=0.6, color=INK, weight="BOLD"):
    return Text(s, font=SANS, weight=weight, color=color).scale(size)


def mono(s, size=0.6, color=INK, weight="BOLD"):
    return Text(s, font=MONO, weight=weight, color=color).scale(size)


def card(w, h, r=0.3, fill=CARD, border=LINE):
    """Slate card with a soft shadow. card[1] is the card itself (use it for positions)."""
    shadow = RoundedRectangle(corner_radius=r, width=w + 0.1, height=h + 0.1, fill_color="#000000",
                              fill_opacity=0.35, stroke_width=0).shift([0, -0.1, 0])
    body = RoundedRectangle(corner_radius=r, width=w, height=h, fill_color=fill, fill_opacity=1,
                            stroke_color=border, stroke_width=2)
    return VGroup(shadow, body)


def badge(s, color=AMBER, size=0.34):
    """Outlined pill label."""
    t = txt(s, size, color, "SEMIBOLD")
    box = RoundedRectangle(corner_radius=(t.height + 0.32) / 2, width=t.width + 0.6, height=t.height + 0.32,
                           fill_color=CARD, fill_opacity=1, stroke_color=color, stroke_width=2)
    return VGroup(box, t.move_to(box))


def glow(mob, color=CYAN):
    """Neon halo behind an outlined shape."""
    halo = VGroup(*[mob.copy().set_fill(opacity=0).set_stroke(color, w, opacity=o)
                    for w, o in ((16, 0.06), (9, 0.12), (4, 0.25))])
    halo.set_z_index(mob.z_index - 1)
    return halo


def disc(color, r=0.6):
    return Circle(radius=r, fill_color=color, fill_opacity=0.18, stroke_color=color, stroke_width=5)
