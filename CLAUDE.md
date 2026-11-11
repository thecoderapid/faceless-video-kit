# Instructions for Claude Code

This repo turns a narration script into a finished, captioned video and can upload it. The user chooses
topics and approves every video; you do the production.

## Workflow for a new video

1. **Agree the script first.** Propose the narration as `videos/<slug>/script.json` lines and wait for the
   user's OK. Each line is one visual beat.
   - Vertical Shorts: about 20–45 s.
   - The first line is the hook: a surprising claim or question, understood in under 3 seconds.
   - The last line is one easy comment question (answerable in a word or a number).
2. **Check every fact** against a primary or official source. Say which sources you used, and flag
   anything you couldn't verify. Never invent quotes, statistics, comments or reviews.
3. **Voice:** `python voice/voice.py <slug>`. Read the printed word timings and use them for the scene.
4. **Scene:** copy `videos/example/scene.py`.
   - Every beat waits for its word: `self.at(self.w(line, "word"))`.
   - Something new appears every 2–3 seconds.
   - Frame 0 already shows the topic: no fade from black and no empty intro.
   - Vertical layout: keep content between y = −2.6 and y = 6.5. Captions and platform buttons cover the rest.
5. **Draft:** run `python make.py <slug> --draft`. Then extract stills with ffmpeg and look at them:
   text inside the frame, nothing overlapping, nothing left on screen from an earlier beat. Fix, re-render.
6. **Final:** run `python make.py <slug>`, then tell the user the path, the duration and what you checked.
7. **Post only when the user says so.**
   - YouTube: `posting/youtube.py upload` uploads unlisted unless the user asks for `--public`.
   - TikTok: goes to the app inbox.

## Rules

- Sound: the voice must always be clear. Keep effects quiet (`sound/mix.py` defaults) and music low.
- Music: only tracks the user has rights to, credited in the description when the licence asks.
- No mass-produced, repetitive videos. Each one needs its own script and visuals, and must be worth
  watching on its own (YouTube's inauthentic-content policy).
- Realistic AI people or events must be disclosed when uploading. Animated explainers normally don't need it.
- Never print, commit or upload `config.json`. It holds the user's tokens.
- YouTube descriptions can't contain `<` or `>`. The uploader replaces them.

## Gotchas

- Manim overwrites `self.duration`. The narration length is `self.total`.
- Animating a piece of a group adds that piece to the scene on its own: use `self.drop(group)` to clear a finished stage.
- Two animations on the same object in one `play()` fight each other. Combine them into one animation.
- `edge-tts` sometimes merges tokens (e.g. "in 2038"). If `self.w()` raises, it prints the line's actual words.
- Captions are burned in after rendering (`animation/captions.py`). Don't draw them in the scene.
