#!/usr/bin/env python3
"""Render dark.svg and light.svg for the GitHub profile README.

usage:
  swift tools/mask.swift <photo> /tmp/mask.png      # macOS Vision person mask
  python3 tools/build.py <photo> /tmp/mask.png

All text comes from PROFILE (sourced from the resume). The photo only feeds the
ASCII portrait; no raster data ends up in the SVGs.
"""
import random
import sys
from itertools import groupby
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

PROFILE = {
    "name": "Asad Hanif",
    "host": "asadali1010@github",
    "headline": "AI-Powered User Interfaces · Angular · TypeScript",
    "rotate": [
        "Real-time streaming UIs for AI agents",
        "Conversational & voice interfaces",
        "Reusable component architecture",
        "Mobile-first, responsive web apps",
    ],
    "rows": [
        ("ROLE", "Senior Frontend Developer"),
        ("COMPANY", "Flow9 · remote · 07/2025 – now"),
        ("LOCATION", "Lahore, Pakistan"),
        ("EXPERIENCE", "Building frontends since 2017"),
        ("FOCUS", "AI-powered UIs · streaming · chat & voice"),
        ("BUILDING", "UI for an AI-native CRM & outreach platform"),
    ],
    "stack": [  # (label, kind) kind -> dot colour: f=frontend, a=AI, e=engineering
        ("Angular", "f"), ("TypeScript", "f"), ("JavaScript", "f"), ("SCSS", "f"),
        ("Tailwind CSS", "f"), ("PrimeNG", "f"), ("Material UI", "f"),
        ("REST APIs", "e"), ("Streaming UIs", "a"), ("Tool calling", "a"), ("Prompt engineering", "a"),
    ],
    "projects": [("JARVIS", "Voice-first agentic AI software-engineering platform", "INDEPENDENT")],
    "links": [("in", "asad-hanif-994b051a"), ("gh", "Asadali1010"), ("@", "asadalihaneef@hotmail.com")],
    "tag": "PROFILE / FRONTEND ENGINEERING",
    "tagline": "UI for AI-powered products",
    "sub": "Angular · TypeScript · mobile-first",
    "command": "ship --mobile-first",
    "aria": "Asad Hanif, Senior Frontend Developer at Flow9 in Lahore, Pakistan, building AI-powered user "
            "interfaces with Angular and TypeScript. ASCII portrait beside a terminal panel listing focus areas, "
            "stack, the JARVIS project and contact links.",
}

CROP = (100, 405, 640, 840)         # head + shoulders + upper chest, source-photo pixels
COLS, ROWS = 140, 66
RAMP = " .·:+*o#%@"

W, H = 1180, 610
FONT = "ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono',monospace"
EM = 0.6                            # monospace advance per em
PX, PY, PW, PH = 52, 114, 392, 316  # portrait box
LX, RX = 512, 1124                  # right panel content edges
LBL, VAL = 616, 640                 # label column (right-aligned) / value column

THEMES = {
    "dark": dict(
        bg=("#030712", "#07111F", "#0B1220"), glow=(("#7C3AED", .22), ("#22D3EE", .14), ("#10B981", .09)),
        panel="#0F172A", panel_op=.38, strip_op=.55, line="#94A3B8", line_op=.14,
        text="#F8FAFC", muted="#94A3B8", dim="#64748B",
        v="#A78BFA", c="#22D3EE", e="#34D399",
        ascii=("#A78BFA", "#22D3EE", "#34D399"), ascii_glow=True,
        grid=.05, noise=("#FFFFFF", .035), scan="#22D3EE", scan_op=.05, sweep=.06, shadow=0,
        chip="#FFFFFF", chip_op=.03,
    ),
    "light": dict(
        bg=("#FFFFFF", "#F8FAFC", "#EEF6FF"), glow=(("#7C3AED", .07), ("#06B6D4", .10), ("#2563EB", .08)),
        panel="#FFFFFF", panel_op=.55, strip_op=.7, line="#0F172A", line_op=.09,
        text="#0F172A", muted="#475569", dim="#64748B",
        v="#6D28D9", c="#0E7490", e="#047857",
        ascii=("#1E3A8A", "#1D4ED8", "#0E7490"), ascii_glow=False,
        grid=.06, noise=("#0F172A", .025), scan="#2563EB", scan_op=.022, sweep=.35, shadow=.07,
        chip="#FFFFFF", chip_op=.6,
    ),
}


def tw(s, size, ls=0):
    return len(s) * (size * EM + ls)


def reveal(t, dy=6, fade=.5):
    """Fade (and rise) in at t. Starts at 0 on frame one; renderers without SMIL show the final state."""
    d = t + fade
    if t > 0:
        kt, ks, op, tr = f"0;{t / d:.4f};1", "0 0 1 1;.2 .7 .3 1", "0;0;1", f"0 {dy};0 {dy};0 0"
    else:
        kt, ks, op, tr = "0;1", ".2 .7 .3 1", "0;1", f"0 {dy};0 0"
    k = f'keyTimes="{kt}" calcMode="spline" keySplines="{ks}" dur="{d:.2f}s" fill="freeze"'
    out = f'<animate attributeName="opacity" values="{op}" {k}/>'
    if dy:
        out += f'<animateTransform attributeName="transform" type="translate" values="{tr}" {k}/>'
    return out


def txt(x, y, s, size, fill, anchor="start", weight=None, ls=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    a += f' font-weight="{weight}"' if weight else ""
    a += f' letter-spacing="{ls}"' if ls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"{a}{extra}>{escape(s)}</text>'


def ascii_rows(photo, mask, dark):
    img = Image.open(photo).convert("L")
    m = Image.open(mask).convert("L").resize(img.size, Image.BILINEAR)
    big = (COLS * 4, ROWS * 4)
    img, m = img.crop(CROP).resize(big, Image.LANCZOS), m.crop(CROP).resize(big, Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(1))
    img = ImageOps.equalize(img, mask=m.point(lambda v: 255 if v > 128 else 0))   # contrast from the subject only
    g = np.asarray(img, float) / 255
    a = np.asarray(m, float) / 255
    g = g * a + (0 if dark else 1) * (1 - a)       # flatten background so the silhouette becomes an edge
    gy, gx = np.gradient(g)
    edge = np.clip(np.hypot(gx, gy) / np.percentile(np.hypot(gx, gy)[a > .5], 98), 0, 1)
    tone = g ** 1.3 if dark else (1 - g) ** .85
    v = np.clip(.8 * tone + .3 * edge, 0, 1)
    v = (.08 + .92 * v) * a                        # floor keeps dark hair/beard readable
    v = v.reshape(ROWS, 4, COLS, 4).mean((1, 3))
    idx = np.rint(v * (len(RAMP) - 1)).astype(int)
    tier = np.digitize(v, [.35, .6])               # brightness tier on top of glyph density: o0 faint, o1 mid, 2 full
    rows = []
    for r in range(ROWS):
        runs = []
        for t, grp in groupby(zip(idx[r], tier[r]), key=lambda p: p[1]):
            s = "".join(RAMP[i] for i, _ in grp).replace(" ", " ")
            runs.append(s if t == 2 else f'<tspan class="o{t}">{s}</tspan>')
        rows.append("".join(runs))
    return rows


def portrait(rows, th):
    lh = PH / ROWS
    # No textLength here: WebKit mis-spaces textLength across <tspan> runs. Centre-anchored rows of equal
    # length stay column-aligned and centred even when the fallback font is narrower than 0.6em.
    lines = "".join(
        f'<text x="{PX + PW / 2}" y="{PY + (i + .8) * lh:.2f}" text-anchor="middle">'
        f'{r}{reveal(.35 + i * .014, 0, .3)}</text>'
        for i, r in enumerate(rows))
    glow = ' filter="url(#aglow)"' if th["ascii_glow"] else ""
    return f'''<g clip-path="url(#pclip)">
<g{glow}><g fill="url(#agrad)" font-size="{PW / (COLS * EM):.3f}">
<animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0" dur="7s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/>
<animate attributeName="opacity" values="1;1;.8;1;1;.9;1;1" keyTimes="0;.41;.42;.43;.77;.78;.79;1" dur="9s" repeatCount="indefinite"/>
{lines}</g></g>
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="url(#scanlines)"/>
<rect x="{PX}" y="{PY - 44}" width="{PW}" height="44" fill="url(#scanbar)">
<animate attributeName="y" values="{PY - 44};{PY + PH}" dur="5.5s" repeatCount="indefinite"/></rect>
</g>'''


def rotator(x, y, phrases, size, th, begin):
    """Types each phrase one character at a time (discrete clip steps), holds, fades, loops."""
    cw = size * EM
    tc, hold, fade, gap = .045, 2.2, .35, .25
    windows, t = [], 0.0
    for p in phrases:
        s, fs = t, t + len(p) * tc + hold
        windows.append((s, fs, fs + fade))
        t = fs + fade + gap
    T = t
    clips, texts, cursor = [], [], [(0.0, 0)]
    for i, (p, (s, fs, fe)) in enumerate(zip(phrases, windows)):
        n = len(p)
        pts = [(0.0, 0)] + [(s + k * tc, k) for k in range(1, n + 1)] + [(fe, 0)]
        kt = ";".join(f"{a / T:.4f}" for a, _ in pts)
        vals = ";".join(f"{c * cw:.2f}" for _, c in pts)
        base = n * cw if i == 0 else 0
        clips.append(
            f'<clipPath id="rc{i}"><rect x="{x}" y="{y - size}" width="{base:.2f}" height="{size * 1.5:.1f}">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" calcMode="discrete" '
            f'dur="{T:.2f}s" begin="{begin}s" repeatCount="indefinite"/></rect></clipPath>')
        texts.append(  # clip on a wrapper <g>: WebKit ignores clip-path on a <text> that has textLength
            f'<g clip-path="url(#rc{i})"><text x="{x}" y="{y}" font-size="{size}" fill="{th["text"]}" '
            f'textLength="{n * cw:.2f}" lengthAdjust="spacing">{escape(p)}'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{fs / T:.4f};{fe / T:.4f};1" '
            f'dur="{T:.2f}s" begin="{begin}s" repeatCount="indefinite"/></text></g>')
        cursor += pts[1:]
    ckt = ";".join(f"{a / T:.4f}" for a, _ in cursor)
    cvals = ";".join(f"{x + c * cw + 2:.2f}" for _, c in cursor)
    cur = (f'<rect x="{x + len(phrases[0]) * cw + 2:.2f}" y="{y - size + 2:.1f}" width="{cw * .9:.1f}" '
           f'height="{size + 1:.1f}" fill="{th["c"]}">'
           f'<animate attributeName="x" values="{cvals}" keyTimes="{ckt}" calcMode="discrete" '
           f'dur="{T:.2f}s" begin="{begin}s" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>')
    return "".join(clips), "".join(texts) + cur


def chips(items, x0, x1, y, size, h, gap, pad):
    """Greedy-wrap items into rows, then widen each chip so every row spans x0..x1 exactly."""
    if not items:
        return []
    rows, row, used = [], [], 0.0
    for it in items:
        w = tw(it[0], size) + pad
        if row and used + gap + w > x1 - x0:
            rows.append(row)
            row, used = [], 0.0
        used += (gap if row else 0) + w
        row.append((it, w))
    rows.append(row)
    out = []
    for r, row in enumerate(rows):
        extra = (x1 - x0 - sum(w for _, w in row) - gap * (len(row) - 1)) / len(row)
        x = x0
        for it, w in row:
            out.append((it, x, y + r * (h + 8), w + extra))
            x += w + extra + gap
    return out


def heading(x, x1, y, label, th):
    end = x + tw(label, 10.5, 1.8) + 12
    return (txt(x, y, label, 10.5, th["c"], weight=600, ls=1.8)
            + f'<line x1="{end:.1f}" y1="{y - 3.5}" x2="{x1}" y2="{y - 3.5}" stroke="{th["line"]}" '
              f'stroke-opacity="{th["line_op"] * 1.6:.2f}" stroke-dasharray="2 4"/>')


def build(th, rows_ascii):
    P = PROFILE
    rnd = random.Random(7)
    kind = {"f": th["c"], "a": th["v"], "e": th["e"]}

    # background particles
    parts = []
    for i in range(22):
        x, y, r = rnd.uniform(30, W - 30), rnd.uniform(40, H - 30), rnd.uniform(.6, 1.5)
        col = (th["c"], th["v"], th["e"])[i % 3]
        dur = rnd.uniform(9, 16)
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" opacity="0">'
            f'<animate attributeName="cy" values="{y:.0f};{y - 36:.0f}" dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;.55;0" dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')

    (g1, o1), (g2, o2), (g3, o3) = th["glow"]
    shadow = (f'<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" '
              f'stdDeviation="14" flood-color="#0F172A" flood-opacity="{th["shadow"]}"/></filter>') if th["shadow"] else ""
    pshadow = ' filter="url(#shadow)"' if th["shadow"] else ""

    def panel(x, y, w, h, title, right, t):
        return f'''<g>{reveal(t, 0, .6)}
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{th["panel"]}" fill-opacity="{th["panel_op"]}"{pshadow}/>
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="url(#gloss)"/>
<path d="M{x} {y + 32}V{y + 16}a16 16 0 0 1 16-16H{x + w - 16}a16 16 0 0 1 16 16V{y + 32}Z" fill="{th["panel"]}" fill-opacity="{th["strip_op"]}"/>
<line x1="{x}" y1="{y + 32}" x2="{x + w}" y2="{y + 32}" stroke="{th["line"]}" stroke-opacity="{th["line_op"]}"/>
<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="15.5" fill="none" stroke="url(#edge)"/>
<circle cx="{x + 18}" cy="{y + 16}" r="3" fill="{th["c"]}"/>
{txt(x + 28, y + 20.5, title, 11, th["text"], weight=700, ls=2.2)}
{txt(x + w - 18, y + 20.5, right, 10.5, th["dim"], anchor="end", ls=.5)}</g>'''

    # ---- left: VISUAL.MAP ----
    cx = PX + PW / 2
    corners = "".join(
        f'<path d="M{x0} {y0 + 12 * sy}V{y0}H{x0 + 12 * sx}" fill="none" stroke="{th["c"]}" stroke-opacity=".7" stroke-width="1.5"/>'
        for x0, y0, sx, sy in ((PX - 6, PY - 6, 1, 1), (PX + PW + 6, PY - 6, -1, 1),
                               (PX - 6, PY + PH + 6, 1, -1), (PX + PW + 6, PY + PH + 6, -1, -1)))
    tagw = tw(P["tag"], 10, 1.6) + 28
    cmd = f"~/profile $ {P['command']}"
    cmdw = tw(cmd, 12)
    left = f'''
<rect x="{PX - 6}" y="{PY - 6}" width="{PW + 12}" height="{PH + 12}" rx="10" fill="{th["panel"]}" fill-opacity="{th["panel_op"] * .8:.2f}" stroke="{th["line"]}" stroke-opacity="{th["line_op"]}"/>
<ellipse cx="{cx}" cy="{PY + PH * .45}" rx="170" ry="150" fill="url(#halo)"><animate attributeName="opacity" values=".7;1;.7" dur="6s" repeatCount="indefinite"/></ellipse>
{portrait(rows_ascii, th)}
<g>{reveal(.3, 0)}{corners}</g>
<g>{reveal(1.25)}
<rect x="{cx - tagw / 2:.1f}" y="450" width="{tagw:.1f}" height="22" rx="11" fill="{th["chip"]}" fill-opacity="{th["chip_op"]}" stroke="{th["c"]}" stroke-opacity=".35"/>
{txt(cx, 464.5, P["tag"], 10, th["c"], anchor="middle", weight=600, ls=1.6)}</g>
<g>{reveal(1.35)}{txt(cx, 498, P["tagline"], 16, th["text"], anchor="middle", weight=700)}
{txt(cx, 520, P["sub"], 12, th["muted"], anchor="middle")}</g>
<g>{reveal(1.45)}
<rect x="{PX}" y="538" width="{PW}" height="28" rx="8" fill="{th["panel"]}" fill-opacity="{th["strip_op"]}" stroke="{th["line"]}" stroke-opacity="{th["line_op"]}"/>
<text x="{cx + cmdw / 2 - 5:.1f}" y="556" font-size="12" text-anchor="end" fill="{th["text"]}"><tspan fill="{th["e"]}">~/profile</tspan><tspan fill="{th["dim"]}"> $ </tspan>{escape(P["command"])}</text>
<rect x="{cx + cmdw / 2 - 2:.1f}" y="546" width="7" height="13" fill="{th["c"]}"><animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.1s" repeatCount="indefinite"/></rect></g>'''

    # ---- right: SYSTEM.INFO ----
    user, _, _ = P["host"].partition("@")
    clips, rot = rotator(LX + 2 * 13.5 * EM, 222, P["rotate"], 13.5, th, 1.0)   # begins with its reveal: no pop
    info = "".join(
        f'<g>{reveal(1.15 + i * .07)}{txt(LBL, 260 + i * 22, k, 10.5, th["muted"], anchor="end", weight=600, ls=1.6)}'
        f'{txt(VAL, 260 + i * 22, v, 13, th["text"])}</g>'
        for i, (k, v) in enumerate(P["rows"]))
    pills = ""
    for i, ((label, k), x, y, w) in enumerate(chips(P["stack"], LX, RX, 418, 11, 24, 8, 30)):
        pills += f'''<g>{reveal(1.6 + i * .035, 4)}<g>
<animateTransform attributeName="transform" type="translate" values="0 0;0 -1.5;0 0" dur="{4 + i % 3:.0f}s" begin="-{i * .6:.1f}s" repeatCount="indefinite"/>
<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="{th["chip"]}" fill-opacity="{th["chip_op"]}" stroke="{kind[k]}" stroke-opacity=".32"/>
<circle cx="{x + 13:.1f}" cy="{y + 12}" r="2.6" fill="{kind[k]}"/>
{txt(x + w / 2 + 5, y + 16, label, 11, th["text"], anchor="middle")}</g></g>'''
    proj = "".join(
        f'<g>{reveal(2.05 + i * .08)}{txt(LX, 516 + i * 22, name, 13, th["v"], weight=700)}'
        f'{txt(LX + tw(name, 13) + 14, 516 + i * 22, desc, 12.5, th["text"])}'
        f'{txt(RX, 516 + i * 22, tag, 10, th["dim"], anchor="end", ls=1.4)}</g>'
        for i, (name, desc, tag) in enumerate(P["projects"]))
    links = ""
    for i, ((_, key, val), x, y, w) in enumerate(chips([(f"{k}\u00a0\u00a0{v}", k, v) for k, v in P["links"]], LX, RX, 538, 11.5, 24, 10, 28)):
        tx = x + w / 2 - tw(f"{key}__{val}", 11.5) / 2
        links += f'''<g>{reveal(2.2 + i * .07, 4)}
<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="7" fill="{th["chip"]}" fill-opacity="{th["chip_op"]}" stroke="{th["line"]}" stroke-opacity="{th["line_op"] * 1.4:.2f}"/>
<text x="{tx:.1f}" y="{y + 16}" font-size="11.5" fill="{th["muted"]}"><tspan fill="{th["c"]}" font-weight="700">{escape(key)}</tspan>\u00a0\u00a0{escape(val)}</text></g>'''

    right = f'''
<g>{reveal(.5, 0)}<text x="{LX}" y="128" font-size="12.5" fill="{th["text"]}"><tspan fill="{th["e"]}">{escape(P["host"])}</tspan><tspan fill="{th["dim"]}">:</tspan><tspan fill="{th["c"]}">~</tspan><tspan fill="{th["dim"]}">$ </tspan>./profile.sh</text></g>
<g>{reveal(.7, 8)}{txt(LX - 2, 172, P["name"], 40, th["text"], weight=800, ls=-1)}</g>
<g>{reveal(.85)}{txt(LX, 198, P["headline"], 14.5, "url(#hgrad)", weight=600)}</g>
<g>{reveal(1.0, 0)}{txt(LX, 222, ">", 13.5, th["e"], weight=700)}{rot}</g>
<g>{reveal(1.05, 0)}<line x1="{LX}" y1="238" x2="{RX}" y2="238" stroke="{th["line"]}" stroke-opacity="{th["line_op"] * 1.4:.2f}"/>
<line x1="{(LBL + VAL) / 2 - 1}" y1="248" x2="{(LBL + VAL) / 2 - 1}" y2="376" stroke="{th["line"]}" stroke-opacity="{th["line_op"] * 1.4:.2f}"/></g>
{info}
<g>{reveal(1.55, 0)}{heading(LX, RX, 404, "STACK", th)}</g>
{pills}
<g>{reveal(2.0, 0)}{heading(LX, RX, 496, "PROJECTS", th)}</g>
{proj}
{links}'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(P["aria"])}">
<title>{escape(P["name"])} · GitHub profile</title>
<defs>
<style>text{{font-family:{FONT};}}.o0{{fill-opacity:.38}}.o1{{fill-opacity:.7}}</style>
<clipPath id="frame"><rect x="10" y="10" width="1160" height="590" rx="22"/></clipPath>
<clipPath id="pclip"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="4"/></clipPath>
<clipPath id="panels"><rect x="28" y="68" width="440" height="516" rx="16"/><rect x="484" y="68" width="668" height="516" rx="16"/></clipPath>
{clips}
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["bg"][0]}"/><stop offset=".55" stop-color="{th["bg"][1]}"/><stop offset="1" stop-color="{th["bg"][2]}"/></linearGradient>
<radialGradient id="r1"><stop offset="0" stop-color="{g1}" stop-opacity="{o1}"/><stop offset="1" stop-color="{g1}" stop-opacity="0"/></radialGradient>
<radialGradient id="r2"><stop offset="0" stop-color="{g2}" stop-opacity="{o2}"/><stop offset="1" stop-color="{g2}" stop-opacity="0"/></radialGradient>
<radialGradient id="r3"><stop offset="0" stop-color="{g3}" stop-opacity="{o3}"/><stop offset="1" stop-color="{g3}" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="{th["c"]}" stop-opacity="{.10 if th["ascii_glow"] else .07}"/><stop offset="1" stop-color="{th["c"]}" stop-opacity="0"/></radialGradient>
<radialGradient id="gridfade" cx=".5" cy=".45" r=".7"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="gridmask"><rect width="{W}" height="{H}" fill="url(#gridfade)"/></mask>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="{th["muted"]}" stroke-opacity="{th["grid"]}"/></pattern>
<pattern id="scanlines" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="{th["scan"]}" fill-opacity="{th["scan_op"]}"/></pattern>
<linearGradient id="scanbar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["scan"]}" stop-opacity="0"/><stop offset=".85" stop-color="{th["scan"]}" stop-opacity=".12"/><stop offset="1" stop-color="{th["scan"]}" stop-opacity="0"/></linearGradient>
<linearGradient id="agrad" gradientUnits="userSpaceOnUse" x1="{PX}" y1="{PY}" x2="{PX + PW}" y2="{PY + PH}">
<stop offset="0" stop-color="{th["ascii"][0]}"/><stop offset=".5" stop-color="{th["ascii"][1]}"/><stop offset="1" stop-color="{th["ascii"][2]}"/>
<animateTransform attributeName="gradientTransform" type="rotate" values="-12 {cx} {PY + PH / 2};12 {cx} {PY + PH / 2};-12 {cx} {PY + PH / 2}" dur="14s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="hgrad" gradientUnits="userSpaceOnUse" x1="{LX}" y1="0" x2="{LX + tw(P["headline"], 14.5)}" y2="0"><stop offset="0" stop-color="{th["v"]}"/><stop offset=".6" stop-color="{th["c"]}"/><stop offset="1" stop-color="{th["e"]}"/></linearGradient>
<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="{.05 if th["ascii_glow"] else .5}"/><stop offset=".3" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["c"]}" stop-opacity=".35"/><stop offset=".5" stop-color="{th["line"]}" stop-opacity="{th["line_op"]}"/><stop offset="1" stop-color="{th["v"]}" stop-opacity=".3"/></linearGradient>
<linearGradient id="shimmer" gradientUnits="userSpaceOnUse" x1="10" y1="10" x2="1170" y2="600">
<stop offset="0" stop-color="{th["v"]}" stop-opacity=".0"/><stop offset=".45" stop-color="{th["v"]}" stop-opacity=".55"/><stop offset=".55" stop-color="{th["c"]}" stop-opacity=".55"/><stop offset="1" stop-color="{th["e"]}" stop-opacity="0"/>
<animateTransform attributeName="gradientTransform" type="rotate" values="0 590 305;360 590 305" dur="16s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity="{th["sweep"]}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="noise" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch" result="n"/><feFlood flood-color="{th["noise"][0]}"/><feComposite operator="in" in2="n"/></filter>
<filter id="aglow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="1.3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
{shadow}
</defs>
<g clip-path="url(#frame)">{reveal(0, 0, .5)}
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<circle cx="230" cy="150" r="420" fill="url(#r1)"><animate attributeName="cx" values="230;300;230" dur="18s" repeatCount="indefinite"/><animate attributeName="cy" values="150;210;150" dur="22s" repeatCount="indefinite"/></circle>
<circle cx="980" cy="520" r="460" fill="url(#r2)"><animate attributeName="cx" values="980;900;980" dur="20s" repeatCount="indefinite"/></circle>
<circle cx="720" cy="60" r="320" fill="url(#r3)"><animate attributeName="cy" values="60;110;60" dur="16s" repeatCount="indefinite"/></circle>
<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridmask)"/>
<rect width="{W}" height="{H}" filter="url(#noise)" opacity="{th["noise"][1]}"/>
{"".join(parts)}
</g>
<rect x="10.5" y="10.5" width="1159" height="589" rx="21.5" fill="none" stroke="{th["line"]}" stroke-opacity="{th["line_op"] * 1.5:.2f}"/>
<rect x="10.5" y="10.5" width="1159" height="589" rx="21.5" fill="none" stroke="url(#shimmer)" stroke-width="1.2"/>
<g>{reveal(.1, 0)}
<path d="M10 52V32a22 22 0 0 1 22-22H1148a22 22 0 0 1 22 22V52Z" fill="{th["panel"]}" fill-opacity="{th["strip_op"] * .6:.2f}"/>
<line x1="10" y1="52" x2="1170" y2="52" stroke="{th["line"]}" stroke-opacity="{th["line_op"]}"/>
<circle cx="36" cy="31" r="6" fill="#FF5F57"/><circle cx="56" cy="31" r="6" fill="#FEBC2E"/><circle cx="76" cy="31" r="6" fill="#28C840"/>
<text x="590" y="35" font-size="12" text-anchor="middle" fill="{th["muted"]}"><tspan fill="{th["text"]}">{escape(user)}</tspan>@{escape(P["host"].split("@")[1])}: ~/profile</text>
<rect x="1070" y="20" width="82" height="22" rx="11" fill="{th["e"]}" fill-opacity=".1" stroke="{th["e"]}" stroke-opacity=".35"/>
<circle cx="1085" cy="31" r="3" fill="{th["e"]}"><animate attributeName="opacity" values="1;.35;1" dur="2.4s" repeatCount="indefinite"/></circle>
{txt(1095, 35, "ONLINE", 10, th["e"], weight=700, ls=1.5)}</g>
{panel(28, 68, 440, 516, "VISUAL.MAP", f"ascii · {COLS}×{ROWS}", .15)}
{panel(484, 68, 668, 516, "SYSTEM.INFO", "profile.sh — zsh", .25)}
{left}
{right}
<g clip-path="url(#panels)"><rect x="-260" y="0" width="200" height="{H}" fill="url(#sweep)" transform="skewX(-18)">
<animate attributeName="x" values="-260;-260;1700;1700" keyTimes="0;.55;.8;1" dur="11s" repeatCount="indefinite"/></rect></g>
</svg>
'''


def main():
    photo, mask = sys.argv[1], sys.argv[2]
    out = Path(__file__).resolve().parent.parent
    for name, th in THEMES.items():
        svg = build(th, ascii_rows(photo, mask, name == "dark"))
        (out / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"{name}.svg  {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
