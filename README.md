# faceless-video-kit

A free starter kit for a faceless video channel in **any niche**: history, science, finance, motivation,
cooking, anything. You write a script; code does the rest:

```
script.json ──► voice ──► animation ──► sound ──► captions ──► final.mp4 ──► YouTube / TikTok
```

Every visual beat is timed to the exact word the narrator says, so videos feel edited by hand without
anyone editing them. Built by [CodeRapid](https://www.youtube.com/@CodeRapid) and used for the channel's own
videos. It is designed to be driven by an AI coding assistant such as
[Claude Code](https://claude.com/claude-code), but every step is a plain Python script you can run yourself.

## What's inside

| Folder | What it does |
| --- | --- |
| `voice/` | Script → narration (free Microsoft Edge voices via `edge-tts`) + the start time of every word |
| `animation/` | [Manim](https://www.manim.community) base scene (wait for a spoken word, log a sound, move the camera), theme, captions |
| `sound/` | Sound effects made in code + a mixer: voice on top, quiet effects, music ducked under the voice, −14 LUFS |
| `posting/` | Upload with the **official** YouTube Data API and TikTok Content Posting API |
| `videos/example/` | A complete 22-second Short ("Why is the sky blue?") to copy |
| `make.py` | One command from script to finished video |

## Quick start

Needs Python 3.10+. FFmpeg is included through `imageio-ffmpeg`.

```bash
pip install -r requirements.txt
python fonts/fetch.py                 # free fonts (Poppins, JetBrains Mono)
python make.py example --draft        # fast low-res check
python make.py example                # -> out/example/final.mp4 (1080x1920)
```

Background music is optional: `python make.py example --music "audio/your track.mp3"`.
Only use music you have the rights to, and credit it in the description if its licence asks for that.

## Make your own video

1. Copy `videos/example/` to `videos/<your-slug>/`.
2. Edit `script.json`: the narration, one line per beat. `"format": "vertical"` (Shorts/TikTok/Reels) or `"wide"` (16:9).
3. Run `python voice/voice.py <your-slug>`. It prints every word with its start time.
4. Edit `scene.py`. Every beat waits for its word:

   ```python
   self.at(self.w(2, "blue"))   # wait until the narrator says "blue" in line 2 (lines count from 0)
   self.sfx("pop")              # quiet sound effect right here
   self.play(FadeIn(arrow))
   ```

5. Run `python make.py <your-slug> --draft`, watch it, fix it, then run `python make.py <your-slug>`.

## Using it with Claude Code

Open this folder in Claude Code and ask for a video, for example
*"Make a 30-second Short about why the Roman Empire split in two"*.
[`CLAUDE.md`](CLAUDE.md) tells it the workflow:

1. Draft the script.
2. Check the facts.
3. Build the scene.
4. Render a draft and look at the frames.
5. Wait for your approval before anything is posted.

You stay the one who chooses the topic and approves the result.

## Posting

```bash
python posting/youtube.py login
python posting/youtube.py upload out/my-video/final.mp4 --title "..." --description-file desc.txt
python posting/tiktok.py login
python posting/tiktok.py upload out/my-video/final.mp4
```

YouTube uploads are **unlisted** by default: watch the real upload, then switch it to public. TikTok
uploads land in your TikTok app inbox, where you add the caption and post. Setup steps are at the top of
each script. Keys and tokens live in `config.json`, which is git-ignored. Never commit or share it.

## Before you monetize: the rules that matter

These change; always check the platforms' own help pages.

- **YouTube Partner Program:** currently 1,000 subscribers, plus either 4,000 public watch hours on
  long videos in 12 months or 10 million Shorts views in 90 days.
- **Inauthentic content:** in July 2025 YouTube clarified that mass-produced, repetitive content isn't
  monetizable. AI is fine when the result is original and adds value. Use this kit to make *better*
  videos, not *more of the same* video.
- **Disclosure:** realistic AI-generated people, places or events must be labelled as altered or
  synthetic content. Clearly animated explainers like the example normally don't need the label.

## Licence

Code: [MIT](LICENSE). Fonts are downloaded from their official sources under the SIL Open Font License.
The narration voices come from Microsoft's online text-to-speech service via `edge-tts`. Check its terms
for your use.
