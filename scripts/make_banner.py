"""Writes banner-light.svg and banner-dark.svg for the GitHub profile README.

A grid of cells stands for one set of weights. Three nested blocks light up
in turn (6B, then 9B, then 12B), each sweeping in column by column, hold,
then fade back. CSS keyframes only, so it animates inside an <img>.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
W, H = 1200, 300
COLS, ROWS, CELL, GAP = 26, 10, 14, 5
STEP = CELL + GAP
GX = W - 56 - (COLS * STEP - GAP)   # grid's left edge, 56px from the right
GY = (H - (ROWS * STEP - GAP)) // 2 - 6
NEST = [("6B", 18, 7), ("9B", 22, 9), ("12B", 26, 10)]  # area ~ 0.48, 0.76, 1
PERIOD = 9.0
EASE = "cubic-bezier(0.77, 0, 0.175, 1)"  # strong ease-in-out, on-screen change

THEMES = {
    "light": dict(bg="#fdfcf9", ink="#1d1c1a", ink2="#5d5850", ink3="#8d877c", base="#ece8e0", accent="#ad3a1f"),
    "dark": dict(bg="#131211", ink="#ebe7df", ink2="#b2aca1", ink3="#888277", base="#252320", accent="#ef8a62"),
}
# Inner blocks glow strongest: the small model is the core of the big one.
LAYER_OPACITY = {"6B": 1.0, "9B": 0.62, "12B": 0.34}
# Each layer turns on later in the cycle, as a share of PERIOD.
ON = {"6B": 0.10, "9B": 0.30, "12B": 0.50}
HOLD_END, OFF_END = 0.80, 0.90


def ring(i):
    """Cells in nest i that are not in nest i-1, grouped by column."""
    _, c, r = NEST[i]
    inner = (0, 0) if i == 0 else NEST[i - 1][1:]
    cols = {}
    for x in range(c):
        for y in range(r):
            if x < inner[0] and y < inner[1]:
                continue
            cols.setdefault(x, []).append(y)
    return cols


def keyframes(name, start, peak):
    rise = start + 0.08
    pct = lambda v: f"{v * 100:.1f}%"
    return (f"@keyframes {name}{{0%,{pct(start)}{{opacity:0}}"
            f"{pct(rise)},{pct(HOLD_END)}{{opacity:{peak}}}"
            f"{pct(OFF_END)},100%{{opacity:0}}}}")


def svg(t):
    css = [
        f".l{{opacity:0;animation:{PERIOD}s {EASE} infinite both}}",
        ".lab{opacity:0;animation:" + f"{PERIOD}s {EASE} infinite both}}",
    ]
    for label, *_ in NEST:
        key = label.lower()
        css.append(keyframes(f"k{key}", ON[label], LAYER_OPACITY[label]))
        css.append(keyframes(f"t{key}", ON[label] + 0.06, 1))
        css.append(f".l{key}{{animation-name:k{key}}}.lab{key}{{animation-name:t{key}}}")
    # Reduced motion: no sweep, just the finished picture.
    css.append("@media (prefers-reduced-motion:reduce){.l,.lab{animation:none}"
               + "".join(f".l{n.lower()}{{opacity:{LAYER_OPACITY[n]}}}" for n, *_ in NEST)
               + ".lab{opacity:1}}")

    rect = lambda x, y, fill: f'<rect x="{GX + x * STEP}" y="{GY + y * STEP}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}"/>'
    parts = [f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>']
    parts.append("<g>" + "".join(rect(x, y, t["base"]) for x in range(COLS) for y in range(ROWS)) + "</g>")
    for i, (label, c, r) in enumerate(NEST):
        key = label.lower()
        for x, ys in sorted(ring(i).items()):
            delay = x * 0.045  # left-to-right sweep, 45ms per column
            cells = "".join(rect(x, y, t["accent"]) for y in ys)
            parts.append(f'<g class="l l{key}" style="animation-delay:{delay:.3f}s">{cells}</g>')
        # A key under the grid: each entry appears as its block lights up.
        kx, ky = GX + i * 78, GY + ROWS * STEP + 22
        parts.append(f'<g class="lab lab{key}"><rect x="{kx}" y="{ky - 10}" width="11" height="11" rx="2" '
                     f'fill="{t["accent"]}" fill-opacity="{LAYER_OPACITY[label]}"/>'
                     f'<text x="{kx + 18}" y="{ky}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
                     f'font-size="12" letter-spacing="1" fill="{t["ink2"]}">{label}</text></g>')

    serif = "Newsreader,'Iowan Old Style','Palatino Linotype',Georgia,serif"
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    parts.append(f'<text x="56" y="128" font-family="{serif}" font-size="58" fill="{t["ink"]}">Ishaan Ranjan</text>')
    parts.append(f'<text x="58" y="170" font-family="{serif}" font-style="italic" font-size="22" fill="{t["ink2"]}">Very bullish on AI, but definitely concerned with safety.</text>')
    parts.append(f'<text x="58" y="222" font-family="{mono}" font-size="13" letter-spacing="1.6" fill="{t["ink3"]}">CS AT GEORGIA TECH · CYFI LAB · ISHAANRANJAN.COM</text>')
    parts.append(f'<text x="{GX}" y="{GY - 14}" font-family="{mono}" font-size="12" letter-spacing="1" fill="{t["ink3"]}">one set of weights, three models</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-label="Ishaan Ranjan. Very bullish on AI, but definitely concerned with safety.">'
            f"<style>{''.join(css)}</style>{''.join(parts)}</svg>\n")


for name, theme in THEMES.items():
    (OUT / f"banner-{name}.svg").write_text(svg(theme))
    print(name, len(svg(theme)), "bytes")
