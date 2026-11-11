"""Karaoke captions as an .ass subtitle file: the spoken word lights up. Burned in by make.py with ffmpeg.

Each caption line has a FIXED position (\\pos) and lines never overlap in time; otherwise the subtitle
renderer stacks the new line above the old one and the caption visibly jumps.
"""
INK, HOT, BOX = "&H00F4ECE8&", "&H003FB5F5&", "&H33261B16"  # off-white, amber, slate box (ASS colours are BGR)

LAYOUT = {  # W, H, font size, caption baseline y (vertical: above the platforms' buttons and description)
    "vertical": (1080, 1920, 76, 1440),
    "wide": (1920, 1080, 46, 1010),
}


def ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def chunks(words, max_words, pause=0.3):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w[0] - cur[-1][1] > pause):
            out.append(cur)
            cur = []
        cur.append(w)
    return out + [cur] if cur else out


def build(timing, fmt="vertical"):
    W, H, size, y = LAYOUT[fmt]
    max_words = 4 if fmt == "vertical" else 6
    pos = f"{{\\an2\\pos({W // 2},{y})}}"
    all_chunks = [c for ln in timing["lines"] for c in chunks(ln["words"], max_words)]
    events, lead = [], 0.08
    for k, ch in enumerate(all_chunks):
        nxt = all_chunks[k + 1][0][0] - lead if k + 1 < len(all_chunks) else None
        end = min(ch[-1][1] + 0.45, nxt) if nxt is not None else ch[-1][1] + 0.6
        for i, w in enumerate(ch):
            t0 = w[0] - (lead if i == 0 else 0)
            t1 = ch[i + 1][0] if i + 1 < len(ch) else end
            text = " ".join(f"{{\\c{HOT}}}{x[2]}{{\\c{INK}}}" if j == i else x[2] for j, x in enumerate(ch))
            events.append([t0, t1, text])
    for a, b in zip(events, events[1:]):  # each event ends exactly where the next begins
        a[1] = min(a[1], b[0])
    style = (f"Style: Cap,Poppins SemiBold,{size},{INK},{INK},&H00261B16,{BOX},0,0,0,0,100,100,0,0,"
             "3,14,0,2,60,60,60,1")  # BorderStyle 3 = box behind the text
    head = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding", style, "", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    body = [f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{pos}{t}" for a, b, t in events if b > a]
    return "\n".join(head + body) + "\n"
