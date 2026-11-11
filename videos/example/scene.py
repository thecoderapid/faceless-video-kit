"""Example video: "Why is the sky blue?" (9:16 Short, ~25 s). Copy this folder to start a new video.

Layout rule for vertical videos: keep content between y = -2.6 and y = 6.5. Captions sit just below
(around y = -4) and the platforms' buttons cover the bottom and right edges.
"""
import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Circle, Create, Ellipse, FadeIn, FadeOut, Flash, LaggedStart, Line,
                   Rectangle, Transform, VGroup)

from animation.base import SNAP, VoicedScene, backdrop
from animation.theme import AMBER, BLUE, CORAL, INK, LINE, MUTED, badge, card, disc, glow, txt

RAINBOW = ("#FF5A5F", "#FF9F43", "#F5B53F", "#34D399", "#5B8CFF", "#A78BFA")


def eye():
    white = Ellipse(width=1.5, height=0.85, fill_color=INK, fill_opacity=0.12, stroke_color=INK, stroke_width=5)
    iris = Circle(radius=0.28, fill_color=BLUE, fill_opacity=1, stroke_width=0)
    return VGroup(white, iris)


def ray(a, b, color, width=6):
    return Line(a, b, color=color, stroke_width=width).add_tip(tip_length=0.22)


class Video(VoicedScene):
    def build(self):
        W = self.w
        self.add(backdrop())
        rng = np.random.default_rng(3)

        # 0 - hook: question + sun on frame 0 (no fade from black, the first second decides if people stay)
        q1 = txt("Why is the sky", 0.95, INK, "BOLD")
        q2 = txt("blue?", 1.6, BLUE, "ULTRABOLD")
        title = VGroup(q1, q2).arrange(DOWN, buff=0.15).move_to(UP * 5.3)
        core = disc(AMBER, 0.7)
        sun = VGroup(glow(core, AMBER), core).move_to(LEFT * 2.6 + UP * 2.6)
        self.sfx("hit", 0.0)
        self.play(FadeIn(title, scale=1.15), FadeIn(sun, scale=0.5), run_time=0.35, rate_func=SNAP)
        self.play(Flash(core, color=AMBER, flash_radius=1.1), run_time=0.5)

        # 1 - white light = every colour
        target = RIGHT * 2.6 + DOWN * 0.6
        beam = ray(sun.get_center(), target, INK, 9)
        self.at(W(1, "sunlight") - 0.1)
        self.sfx("whoosh")
        self.play(Create(beam), run_time=0.5)
        fan = VGroup(*[ray(sun.get_center(), target + UP * (k - 2.5) * 0.45, c, 6) for k, c in enumerate(RAINBOW)])
        self.at(W(1, "every") - 0.1)
        self.sfx("pop")
        self.play(Transform(beam, fan), run_time=0.45)
        self.at(W(1, "mixed") - 0.1)
        self.play(Transform(beam, ray(sun.get_center(), target, INK, 9)), run_time=0.45)

        # 2 - the air scatters blue far more than red
        air = VGroup(*[Circle(radius=0.07, fill_color=MUTED, fill_opacity=0.8, stroke_width=0).move_to(
            [x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), 0])
            for x in np.arange(-3.4, 3.6, 0.85) for y in np.arange(-1.8, 3.4, 0.85)])
        air_l = badge("air", MUTED, 0.4).move_to(RIGHT * 3.0 + UP * 3.75)
        self.at(W(2, "air") - 0.2)
        self.play(FadeOut(beam), LaggedStart(*[FadeIn(a, scale=0.3) for a in air], lag_ratio=0.01), FadeIn(air_l),
                  run_time=0.6)
        hubs = [air[i] for i in rng.choice(len(air), 7, replace=False)]
        blues = VGroup(*[ray(h.get_center(), h.get_center() + 0.9 * np.array([np.cos(a), np.sin(a), 0]), BLUE, 5)
                         for h in hubs for a in rng.uniform(0, 2 * np.pi, 2)])
        self.at(W(2, "blue") - 0.1)
        self.sfx("pop")
        self.play(LaggedStart(*[Create(b) for b in blues], lag_ratio=0.04), run_time=0.8)
        red = ray(LEFT * 4.2 + UP * 0.4, RIGHT * 4.2 + UP * 0.4, CORAL, 6)
        self.at(W(2, "red") - 0.1)
        self.play(Create(red), run_time=0.5)
        b_l = VGroup(badge("blue: bounces a lot", BLUE, 0.4), badge("red: goes straight", CORAL, 0.4)).arrange(
            DOWN, buff=0.18).move_to(DOWN * 2.6)
        self.play(FadeIn(b_l, shift=UP * 0.2), run_time=0.35)

        # 3 - blue arrives from everywhere -> the whole sky looks blue
        sky = Rectangle(width=9.2, height=16.2, fill_color=BLUE, fill_opacity=0, stroke_width=0)  # whole frame
        sky.set_z_index(-5)
        you = eye().move_to(DOWN * 2.0)
        self.at(self.start(3) - 0.1)
        self.play(FadeOut(VGroup(b_l, red)), FadeIn(you, scale=0.7), run_time=0.4)
        into = VGroup(*[ray(h.get_center(), you.get_center() + UP * 0.45, BLUE, 4) for h in hubs])
        self.at(W(3, "eyes") - 0.1)
        self.play(Transform(blues, into), run_time=0.7)
        self.at(W(3, "every") - 0.1)
        self.play(sky.animate.set_fill(BLUE, 0.22), run_time=0.8)

        # 4 - sunset: a longer path through the air, the blue is gone before it arrives
        self.at(W(4, "sunset") - 0.15)
        self.sfx("whoosh")
        horizon = Line(LEFT * 4.6 + DOWN * 1.0, RIGHT * 4.6 + DOWN * 1.0, color=LINE, stroke_width=4)
        self.play(FadeOut(blues), sun.animate.move_to(LEFT * 3.6 + DOWN * 0.7), sky.animate.set_fill(AMBER, 0.16),
                  FadeIn(horizon), run_time=0.9)
        path = ray(sun.get_center(), you.get_center() + LEFT * 0.7, AMBER, 7)
        self.at(W(4, "more") - 0.1)
        self.play(Create(path), run_time=0.7)
        lost = VGroup(*[ray(p, p + 0.8 * np.array([np.cos(a), np.sin(a), 0]), BLUE, 4)
                        for p, a in zip([path.point_from_proportion(x) for x in (0.2, 0.35, 0.5, 0.65)],
                                        (1.9, 1.3, 2.2, 1.5))])
        self.at(W(4, "scatters") - 0.1)
        self.play(LaggedStart(*[Create(b) for b in lost], lag_ratio=0.15), run_time=0.6)
        self.play(FadeOut(lost, shift=UP * 0.6), run_time=0.4)
        self.at(W(4, "reds") - 0.1)
        self.sfx("ding")
        self.play(path.animate.set_color(CORAL), sky.animate.set_fill(CORAL, 0.2),
                  Flash(you, color=CORAL, flash_radius=1.0), run_time=0.5)

        # 5 - easy comment question
        ask = card(7.6, 2.3, r=0.35).move_to(UP * 1.2)
        ask_t = VGroup(txt("Which question", 0.62, INK, "BOLD"), txt("should we answer next?", 0.62, INK, "BOLD"))
        ask_t.arrange(DOWN, buff=0.12).move_to(ask[1])
        tag = badge("tell us in the comments", AMBER, 0.42).next_to(ask, DOWN, buff=0.4)
        self.at(self.start(5) - 0.2)
        self.sfx("pop")
        self.play(FadeOut(VGroup(air, air_l, path, horizon, sun, you)), FadeIn(VGroup(ask, ask_t), scale=0.9),
                  run_time=0.4, rate_func=SNAP)
        self.at(W(5, "next") - 0.1)
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.35)
