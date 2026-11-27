# Generates the profile README SVGs in the kasko-yurii.vercel.app brand.
# usage: python gen.py <cv-site>/public/fonts <this-repo>/assets   (needs: pip install fonttools brotli)
# Data source: cv-site src/locales/en.json + src/components/jobs.ts. Update README alt texts too.
import base64, io, sys, math, html
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

FONTDIR, OUT = sys.argv[1], sys.argv[2]
PAPER, INK, MUTED, ACC, SOFT = '#ecedef', '#000000', '#55585e', '#2f3cff', '#9ea4ff'

def instance(fn, w):
    f = instancer.instantiateVariableFont(TTFont(f'{FONTDIR}/{fn}'), {'wght': w})
    b = io.BytesIO(); f.flavor = None; f.save(b); return b.getvalue()

FONTS = {  # key -> (css family, ttf bytes)
    'D': instance('unbounded-latin.woff2', 800),
    'B': instance('onest-latin.woff2', 400),
    'M': instance('onest-latin.woff2', 600),
}
_m = {}
for k, b in FONTS.items():
    f = TTFont(io.BytesIO(b)); cmap = f.getBestCmap(); hm = f['hmtx']; upm = f['head'].unitsPerEm
    _m[k] = (cmap, hm, upm, f['OS/2'].sCapHeight / upm)

def W(text, k, size, ls=0):
    cmap, hm, upm, _ = _m[k]
    return sum(hm[cmap.get(ord(c), cmap[32])][0] for c in text) * size / upm + ls * len(text)

def CAP(k): return _m[k][3]

def wrap(text, k, size, maxw):
    lines, cur = [], ''
    for w in text.split(' '):
        t = (cur + ' ' + w).strip()
        if W(t, k, size) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur]

def esc(s): return html.escape(s, quote=False)

def arrow_ne(cx, cy, a, color, sw=2.4):
    return (f'<path d="M{cx-a:.1f} {cy+a:.1f}L{cx+a:.1f} {cy-a:.1f}M{cx-a*.35:.1f} {cy-a:.1f}H{cx+a:.1f}V{cy+a*.35:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

def arrow_r(x, y, l, color, sw=2):
    return (f'<path d="M{x} {y}H{x+l}M{x+l-5} {y-5}L{x+l} {y}L{x+l-5} {y+5}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

class Svg:
    def __init__(s, name, w, h, label):
        s.name, s.w, s.h, s.label = name, w, h, label
        s.body, s.css, s.defs = [], [], []
        s.chars = {k: set(' ') for k in FONTS}
    def t(s, x, y, text, k='B', size=16, fill=INK, anchor='start', ls=0, extra=''):
        s.chars[k] |= set(text)
        a = '' if anchor == 'start' else f' text-anchor="{anchor}"'
        l = f' letter-spacing="{ls}"' if ls else ''
        s.body.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{k}" font-size="{size}" fill="{fill}"{a}{l} {extra}>{esc(text)}</text>')
    def use(s, k, text): s.chars[k] |= set(text)
    def r(s, *parts): s.body.extend(parts)
    def save(s):
        faces = []
        for k, chars in s.chars.items():
            if chars == {' '}: continue
            f = TTFont(io.BytesIO(FONTS[k]))
            o = subset.Options(); o.flavor = 'woff2'; o.layout_features = ['kern', 'liga', 'calt']
            sub = subset.Subsetter(o); sub.populate(text=''.join(chars)); sub.subset(f)
            f.flavor = 'woff2'; b = io.BytesIO(); f.save(b)
            faces.append(f"@font-face{{font-family:'{k}{s.name}';src:url(data:font/woff2;base64,{base64.b64encode(b.getvalue()).decode()}) format('woff2')}}"
                         f".{k}{{font-family:'{k}{s.name}',{'Unbounded,' if k == 'D' else 'Onest,'}-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}}")
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h}" width="{s.w}" height="{s.h}" role="img" aria-label="{html.escape(s.label)}">\n'
               f'<defs>{"".join(s.defs)}<clipPath id="card"><rect width="{s.w}" height="{s.h}" rx="28"/></clipPath></defs>\n'
               f'<style>{"".join(faces)}\n{chr(10).join(s.css)}\n@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>\n'
               f'<g clip-path="url(#card)">\n' + '\n'.join(s.body) + '\n</g>\n</svg>\n')
        open(f'{OUT}/{s.name}.svg', 'w').write(svg)

def card(s, fill):
    s.r(f'<rect width="{s.w}" height="{s.h}" fill="{fill}"/>')

def border(s, color='#000', op=.1):
    s.r(f'<rect x=".5" y=".5" width="{s.w-1}" height="{s.h-1}" rx="27.5" fill="none" stroke="{color}" stroke-opacity="{op}"/>')

def pill(s, x, y, text, k='M', size=14, fill='none', stroke=INK, color=INK, h=34, padx=16, dot=None):
    w = W(text, k, size) + padx * 2 + (18 if dot else 0)
    s.r(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{stroke}"/>')
    tx = x + padx
    if dot:
        cy = y + h / 2
        s.r(f'<circle cx="{tx+4}" cy="{cy}" r="4" fill="{dot}"/>',
            f'<circle cx="{tx+4}" cy="{cy}" r="4" fill="none" stroke="{dot}" stroke-width="1.5"><animate attributeName="r" values="4;11" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0" dur="1.8s" repeatCount="indefinite"/></circle>')
        tx += 18
    s.t(tx, y + h / 2 + size * .36, text, k, size, color)
    return w

# ───────────────────────── HERO ─────────────────────────
def hero():
    first, last = 'YURII', 'KASKO'
    S = 1104 / W(last, 'D', 1)
    cap = CAP('D') * S
    y1 = 300 + cap
    y2 = y1 + cap + S * .12
    H = int(y2 - cap * .2)
    s = Svg('hero', 1200, H, 'Yurii Kasko — Full-stack engineer, Ukraine. Open to remote full-stack and frontend roles and contracts.')
    card(s, PAPER)
    # nav
    s.t(48, 62, 'YURII KASKO', 'D', 17)
    links = ['Projects', 'Experience', 'Stack']
    tot = sum(W(l, 'B', 16) for l in links) + 36 * 2
    x = 600 - tot / 2
    for l in links:
        s.t(x, 61, l, 'B', 16); x += W(l, 'B', 16) + 36
    cvw = W('CV', 'M', 15) + 40
    s.r(f'<rect x="{1152-cvw:.1f}" y="36" width="{cvw:.1f}" height="40" rx="20" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    s.t(1152 - cvw / 2, 61, 'CV', 'M', 15, anchor='middle')
    st = 'Open to remote roles'
    sw = W(st, 'M', 15) + 32 + 18
    pill(s, 1152 - cvw - 12 - sw, 36, st, 'M', 15, fill=ACC, stroke=ACC, color='#fff', h=40, dot='#fff')
    # meta + intro
    s.t(48, 160, 'Full-stack engineer', 'M', 22)
    s.t(48, 192, 'Ukraine · 5+ years from idea to production', 'B', 18, MUTED)
    intro = 'I build web products end to end: React and Vue frontends, Node backends on PostgreSQL, realtime features and integrations.'
    for i, ln in enumerate(wrap(intro, 'B', 20, 500)):
        s.t(652, 158 + i * 29, ln, 'B', 20)
    # giant name with a cobalt sweep
    s.defs.append(f'<clipPath id="sweep"><g transform="skewX(-18)"><rect y="0" width="260" height="{H}">'
                  f'<animate attributeName="x" values="-500;1600" dur="7s" repeatCount="indefinite"/></rect></g></clipPath>')
    for fill, extra in ((INK, ''), (ACC, 'clip-path="url(#sweep)"')):
        s.r(f'<g {extra}>')
        s.t(44, y1, first, 'D', round(S, 1), fill, ls=-S * .02)
        s.t(44, y2, last, 'D', round(S, 1), fill, ls=-S * .02)
        s.r('</g>')
    # rotating stamp next to YURII
    w1 = W(first, 'D', S, -S * .02)
    R = 86
    cx, cy = 44 + w1 + (1152 - 44 - w1) / 2, y1 - cap / 2
    cx = min(cx, 1152 - R)
    ring = 'OPEN TO REMOTE · FULL-STACK · '
    s.use('M', ring)
    rr = R - 20
    s.defs.append(f'<path id="ring" d="M{cx-rr} {cy}a{rr} {rr} 0 1 1 {2*rr} 0a{rr} {rr} 0 1 1 {-2*rr} 0"/>')
    s.css.append(f'.spin{{transform-origin:{cx:.1f}px {cy:.1f}px;animation:spin 16s linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}')
    s.r(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R}" fill="{ACC}"/>',
        f'<g class="spin"><text class="M" font-size="12.5" fill="#fff" letter-spacing="1"><textPath href="#ring" textLength="{2*math.pi*rr-4:.1f}" lengthAdjust="spacing">{ring}</textPath></text></g>',
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="30" fill="#fff"/>', arrow_ne(cx, cy, 9, ACC, 3))
    border(s)
    s.save()

# ───────────────────────── NUMBERS ─────────────────────────
def numbers():
    s = Svg('numbers', 1200, 236, 'In numbers: 5+ years from idea to production, 4 teams since 2020, 3 live products, 26 tools in the stack.')
    card(s, INK)
    items = [('5', '+', 'years taking products from idea to production'), ('4', '', 'teams and clients shipped with since 2020'),
             ('3', '', 'live products, one I use every day'), ('26', '', 'tools in the stack, AI pair programmers included')]
    cw = 1104 / 4
    for i, (n, suf, lab) in enumerate(items):
        x = 48 + i * cw
        if i: s.r(f'<rect x="{x-24:.1f}" y="40" width="1" height="156" fill="#fff" fill-opacity=".14"/>')
        s.t(x, 116, n, 'D', 72, '#fff')
        if suf: s.t(x + W(n, 'D', 72) + 4, 116, suf, 'D', 72, SOFT)
        s.r(f'<rect x="{x:.1f}" y="140" width="{cw-56:.1f}" height="2" fill="#fff" fill-opacity=".12"/>',
            f'<rect x="{x:.1f}" y="140" width="48" height="2" fill="{SOFT}"><animate attributeName="x" values="{x:.1f};{x+cw-104:.1f};{x:.1f}" dur="5s" begin="{-i*1.2}s" repeatCount="indefinite" calcMode="spline" keySplines=".6 0 .4 1;.6 0 .4 1"/></rect>')
        for j, ln in enumerate(wrap(lab, 'B', 17, cw - 34)):
            s.t(x, 174 + j * 24, ln, 'B', 17, '#a3a6ad')
    s.save()

# ───────────────────────── SECTION HEADER ─────────────────────────
def header(name, title, right):
    s = Svg(name, 1200, 132, f'{title} — {right}')
    card(s, PAPER)
    s.t(48, 86, title, 'D', 46)
    tw = W(title, 'D', 46)
    s.r(f'<circle cx="{48+tw+16:.1f}" cy="80" r="8" fill="{ACC}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>')
    s.t(1152, 84, right, 'B', 18, MUTED, anchor='end')
    border(s)
    s.save()

# ───────────────────────── PROJECT MOCKS ─────────────────────────
def mock_security(s, ox, oy):
    s.r(f'<rect x="{ox+24}" y="{oy+20}" width="392" height="276" rx="16" fill="#fff" fill-opacity=".1" stroke="#fff" stroke-opacity=".28"/>')
    s.t(ox + 46, oy + 54, 'Threat signals', 'M', 15, '#fff')
    pill(s, ox + 316, oy + 36, 'LIVE', 'M', 11, fill='#fff', stroke='#fff', color=ACC, h=24, padx=10, dot=ACC)
    pts = [(0, 70), (30, 62), (60, 66), (90, 40), (120, 52), (150, 30), (180, 44), (210, 20), (240, 38), (270, 26), (300, 48), (330, 34), (348, 40)]
    bx, by = ox + 46, oy + 76
    line = ' '.join(f'{bx+x},{by+y}' for x, y in pts)
    s.r(f'<polygon points="{bx},{by+90} {line} {bx+348},{by+90}" fill="#fff" fill-opacity=".14"/>',
        f'<polyline points="{line}" fill="none" stroke="#fff" stroke-width="2.4" stroke-linejoin="round"/>',
        f'<rect y="{by}" width="2" height="90" fill="#fff"><animate attributeName="x" values="{bx};{bx+346};{bx}" dur="6s" repeatCount="indefinite"/></rect>')
    rows = [('Microsoft Defender', '62;118;80;62'), ('Threat intel feeds', '96;54;120;96'), ('Cross-tenant KB', '40;90;70;40')]
    for i, (lab, vals) in enumerate(rows):
        y = oy + 196 + i * 32
        s.t(ox + 46, y + 5, lab, 'B', 14, '#fff')
        s.r(f'<rect x="{ox+246}" y="{y-4}" width="148" height="8" rx="4" fill="#fff" fill-opacity=".2"/>',
            f'<rect x="{ox+246}" y="{y-4}" width="{vals.split(";")[0]}" height="8" rx="4" fill="#fff"><animate attributeName="width" values="{vals}" dur="{4+i}s" repeatCount="indefinite"/></rect>')

def mock_kanban(s, ox, oy):
    s.t(ox + 26, oy + 44, 'Today’s queue', 'M', 15, '#fff')
    pill(s, ox + 316, oy + 26, 'LIVE', 'M', 11, fill='#fff', stroke='#fff', color=ACC, h=24, padx=10, dot=ACC)
    cols = ['Intake', 'In work', 'Ready']
    cards = [['Audi A4', 'Skoda Octavia'], ['BMW X5', 'Toyota RAV4'], ['VW Golf']]
    for i, c in enumerate(cols):
        x = ox + 24 + i * 134
        s.r(f'<rect x="{x}" y="{oy+64}" width="124" height="232" rx="12" fill="#fff" fill-opacity=".1"/>')
        s.t(x + 14, oy + 90, c, 'M', 13, '#fff')
        for j, name in enumerate(cards[i]):
            y = oy + 104 + j * 58
            s.r(f'<rect x="{x+8}" y="{y}" width="108" height="48" rx="9" fill="#fff"/>')
            s.t(x + 20, y + 21, name, 'M', 12, INK)
            s.r(f'<rect x="{x+20}" y="{y+31}" width="76" height="4" rx="2" fill="{ACC}" fill-opacity=".18"/>',
                f'<rect x="{x+20}" y="{y+31}" width="{[22,50,76][i]}" height="4" rx="2" fill="{ACC}"/>')
    # one car travelling through the stages
    x0, y0 = ox + 32, oy + 220
    s.r(f'<g><animateTransform attributeName="transform" type="translate" dur="7.5s" repeatCount="indefinite" calcMode="spline" '
        f'keyTimes="0;.12;.4;.52;.8;.92;1" values="0 0;0 0;134 0;134 0;268 -58;268 -58;0 0" keySplines=".6 0 .2 1;.6 0 .2 1;.6 0 .2 1;.6 0 .2 1;.6 0 .2 1;.6 0 .2 1"/>',
        f'<rect x="{x0}" y="{y0}" width="108" height="48" rx="9" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    s.t(x0 + 12, y0 + 21, 'Ford Focus', 'M', 12, INK)
    s.r(f'<rect x="{x0+12}" y="{y0+31}" width="76" height="4" rx="2" fill="{ACC}" fill-opacity=".18"/>',
        f'<rect x="{x0+12}" y="{y0+31}" width="22" height="4" rx="2" fill="{ACC}"><animate attributeName="width" dur="7.5s" repeatCount="indefinite" keyTimes="0;.12;.4;.52;.8;.92;1" values="22;22;50;50;76;76;22"/></rect>',
        '</g>')

def mock_finance(s, ox, oy):
    s.r(f'<rect x="{ox+24}" y="{oy+20}" width="230" height="276" rx="16" fill="#fff"/>')
    s.t(ox + 44, oy + 52, 'Balance', 'B', 13, MUTED)
    s.t(ox + 44, oy + 88, '48 210', 'D', 30, INK)
    s.t(ox + 44, oy + 112, '+12% this month', 'M', 12, ACC)
    heights = [38, 62, 48, 80, 56, 92, 70]
    for i, h in enumerate(heights):
        x = ox + 44 + i * 28
        s.r(f'<rect x="{x}" y="{oy+272-h}" width="18" height="{h}" rx="5" fill="{ACC if i == 5 else "#d9dbff"}">'
            f'<animate attributeName="height" values="{h};{h*.55:.0f};{h}" dur="3s" begin="{-i*.4}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{oy+272-h};{oy+272-h*.55:.0f};{oy+272-h}" dur="3s" begin="{-i*.4}s" repeatCount="indefinite"/></rect>')
    # category limit
    s.t(ox + 274, oy + 52, 'Food limit', 'M', 13, '#fff')
    s.t(ox + 416, oy + 52, '72%', 'M', 13, '#fff', anchor='end')
    s.r(f'<rect x="{ox+274}" y="{oy+64}" width="142" height="8" rx="4" fill="#fff" fill-opacity=".25"/>',
        f'<rect x="{ox+274}" y="{oy+64}" width="102" height="8" rx="4" fill="#fff"/>')
    s.t(ox + 274, oy + 112, 'Wishlist', 'M', 13, '#fff')
    s.t(ox + 274, oy + 134, 'price dropped 8%', 'B', 12, '#fff', extra='fill-opacity=".75"')
    # telegram bot bubbles
    s.css.append('.bub{animation:bub 6s ease-in-out infinite}.b2{animation-delay:-3s}'
                 '@keyframes bub{0%,100%{opacity:1;transform:none}45%{opacity:1;transform:none}50%{opacity:0;transform:translateY(8px)}55%{opacity:0;transform:translateY(8px)}}')
    s.t(ox + 274, oy + 186, 'via Telegram bot', 'B', 12, '#fff', extra='fill-opacity=".75"')
    for i, (txt, y) in enumerate([('coffee 4.50', 200), ('added to Food', 244)]):
        bw = W(txt, 'M', 13) + 28
        s.r(f'<g class="bub{" b2" if i else ""}">',
            f'<rect x="{ox+274+(0 if i==0 else 142-bw):.1f}" y="{oy+y}" width="{bw:.1f}" height="34" rx="17" fill="{"#fff" if i==0 else INK}"/>')
        s.t(ox + 274 + (14 if i == 0 else 142 - bw + 14), oy + y + 22, txt, 'M', 13, ACC if i == 0 else '#fff')
        s.r('</g>')

def mock_nda(s, ox, oy):
    s.r(f'<rect x="{ox+40}" y="{oy+98}" width="360" height="120" rx="16" fill="{INK}"/>')
    s.t(ox + 220, oy + 170, 'UNDER NDA', 'D', 30, '#fff', anchor='middle')

# ───────────────────────── PROJECT CARD ─────────────────────────
def project(name, idx, kind, title, desc, bullets, tags, url, mock, note=None):
    lw = 600
    dl = wrap(desc, 'B', 18, lw)
    bl = [wrap(b, 'B', 16, lw - 30) for b in bullets]
    y = 152 + len(dl) * 27 + 14
    by = []
    for b in bl: by.append(y); y += len(b) * 23 + 10
    ny = None
    if note:
        nl = wrap(note, 'B', 14, lw); ny = y + 2; y += len(nl) * 20 + 8
    # tags layout
    tx, ty, tagpos = 48, y + 8, []
    for t in tags:
        w = W(t, 'M', 13) + 28
        if tx + w > 48 + lw: tx, ty = 48, ty + 40
        tagpos.append((tx, ty, t)); tx += w + 8
    uy = ty + 34 + 44
    H = max(int(uy + 40 if url else uy), 392)
    s = Svg(name, 1200, H, f'{title}: {desc}')
    card(s, PAPER)
    s.t(48, 72, idx, 'D', 15, ACC)
    s.t(48 + W(idx, 'D', 15) + 14, 72, kind.upper(), 'M', 13, MUTED, ls=1.6)
    s.t(46, 124, title, 'D', 42)
    for i, ln in enumerate(dl): s.t(48, 164 + i * 27, ln, 'B', 18)
    for b, y0 in zip(bl, by):
        s.r(arrow_r(48, y0 + 10 + 14 - 9, 16, ACC))
        for j, ln in enumerate(b): s.t(78, y0 + 14 + 10 + j * 23, ln, 'B', 16, MUTED)
    if note:
        for j, ln in enumerate(nl): s.t(48, ny + 24 + j * 20, ln, 'B', 14, MUTED, extra='font-style="italic"')
    for x, y0, t in tagpos:
        pill(s, x, y0 + 14, t, 'M', 13, stroke='#000', h=32, padx=14)
    if url:
        s.t(48, uy, url, 'M', 17)
        uw = W(url, 'M', 17)
        s.r(f'<rect x="48" y="{uy+8}" width="{uw:.1f}" height="2" fill="{ACC}"/>', arrow_ne(48 + uw + 16, uy - 6, 6, ACC, 2.2))
    # mock panel
    ph = H - 64
    s.r(f'<rect x="712" y="32" width="440" height="{ph}" rx="20" fill="{ACC}"/>')
    s.r(f'<g opacity=".18" stroke="#fff">' + ''.join(f'<path d="M{712+i*40} 32V{32+ph}"/>' for i in range(1, 11)) + '</g>')
    mock(s, 712, 32 + (ph - 316) / 2)
    border(s)
    s.save()

# ───────────────────────── EXPERIENCE ─────────────────────────
def experience():
    rows = [
        ('APR 2025 — NOW', 'Freelance', 'Full-stack developer · Ukraine', (2025, 4), None,
         'Built an admin platform for an auto service end to end: Vue 3 frontend, Node and PostgreSQL API with realtime updates.'),
        ('AUG 2025 — MAY 2026', 'NDA startup', 'Front-end developer, part-time · Ukraine', (2025, 8), (2026, 5),
         'Took the frontend from zero to production on my own, including its architecture and component system.'),
        ('SEP 2021 — APR 2025', 'NSOC360', 'Front-end developer via Quardex · Netherlands', (2021, 9), (2025, 4),
         'Built UI for a monitoring and analytics product used by an EU client, and migrated it from Vue 2 to Vue 3 on my own.'),
        ('OCT 2020 — APR 2025', 'Quardex', 'Project manager, then front-end · Ukraine', (2020, 10), (2025, 4),
         'Started as a project manager, then moved into frontend: React and Strapi, a Nuxt company website, a shared component system.'),
    ]
    NOW = (2026, 11)
    X0, X1 = 430, 1152
    def X(ym): return X0 + ((ym[0] - 2020) * 12 + ym[1] - 1) / 84 * (X1 - X0)
    top, rh = 196, 128
    H = top + rh * len(rows) + 24
    s = Svg('experience', 1200, H, 'Experience: Freelance (Apr 2025 – now), NDA startup (Aug 2025 – May 2026), NSOC360 via Quardex (Sep 2021 – Apr 2025), Quardex (Oct 2020 – Apr 2025)')
    card(s, PAPER)
    s.t(48, 86, 'Experience', 'D', 46)
    s.r(f'<circle cx="{48+W("Experience","D",46)+16:.1f}" cy="80" r="8" fill="{ACC}"/>')
    s.t(1152, 84, 'Six years in tech, four teams', 'B', 18, MUTED, anchor='end')
    for yr in range(2020, 2027):
        x = X((yr, 1))
        s.r(f'<rect x="{x:.1f}" y="150" width="1" height="{H-174}" fill="#000" fill-opacity=".08"/>')
        s.t(x + 8, 164, str(yr), 'M', 13, MUTED)
    xn = X(NOW)
    s.r(f'<path d="M{xn:.1f} 176V{H-24}" stroke="{ACC}" stroke-width="1.5" stroke-dasharray="4 5"/>')
    s.t(xn, 164, 'NOW', 'M', 12, ACC, anchor='end', ls=1.2)
    s.defs.append(f'<pattern id="stripe" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                  f'<rect width="14" height="14" fill="{ACC}"/><rect width="6" height="14" fill="#fff" fill-opacity=".22"/>'
                  f'<animateTransform attributeName="patternTransform" type="translate" additive="sum" values="0 0;14 0" dur="1s" repeatCount="indefinite"/></pattern>')
    for i, (dates, co, role, a, b, hl) in enumerate(rows):
        y = top + i * rh
        s.r(f'<rect x="48" y="{y}" width="1104" height="1" fill="#000" fill-opacity=".14"/>')
        s.t(48, y + 34, dates, 'M', 12, MUTED, ls=1.4)
        s.t(46, y + 72, co, 'D', 26)
        s.t(48, y + 100, role, 'B', 15, MUTED)
        xa, xb = X(a), X(b or NOW)
        cur = b is None
        s.r(f'<rect x="{xa:.1f}" y="{y+26}" width="{xb-xa:.1f}" height="18" rx="9" fill="{"url(#stripe)" if cur else INK}"/>')
        if cur:
            s.r(f'<circle cx="{xb:.1f}" cy="{y+35}" r="5" fill="{ACC}"/>',
                f'<circle cx="{xb:.1f}" cy="{y+35}" r="5" fill="none" stroke="{ACC}" stroke-width="2"><animate attributeName="r" values="5;16" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0" dur="1.8s" repeatCount="indefinite"/></circle>')
        for j, ln in enumerate(wrap(hl, 'B', 16, xn - X0 - 16)):
            s.t(X0, y + 78 + j * 23, ln, 'B', 16)
    border(s)
    s.save()

# ───────────────────────── STACK ─────────────────────────
def stack():
    core = {'Vue 3', 'TypeScript', 'React', 'Nuxt', 'Pinia', 'Vite', 'Claude Code'}
    rows = [['Vue 3', 'Nuxt', 'React', 'Next.js', 'TypeScript', 'Pinia', 'Vuex', 'Vuetify', 'Quasar'],
            ['Tailwind CSS', 'TanStack Query', 'Chart.js', 'AmCharts', 'WebSocket', 'Node.js', 'PostgreSQL', 'Supabase', 'Vite'],
            ['Vitest', 'Docker', 'Git', 'CI/CD', 'Figma', 'Cursor', 'Claude Code', 'Codex']]
    H = 460
    s = Svg('stack', 1200, H, 'Stack: ' + ', '.join(sum(rows, [])))
    card(s, ACC)
    s.t(48, 86, 'Stack', 'D', 46, '#fff')
    s.t(1152, 84, '26 tools, from UI to database to AI', 'B', 18, '#fff', anchor='end', extra='fill-opacity=".8"')
    gap = 12
    for i, row in enumerate(rows):
        y = 144 + i * 92
        items, x = [], 0
        for t in row:
            w = W(t, 'M', 22) + 56
            items.append((x, w, t)); x += w + gap
        rw = x
        s.css.append(f'.m{i}{{animation:m{i} {rw/45:.1f}s linear infinite{" reverse" if i % 2 else ""}}}'
                     f'@keyframes m{i}{{from{{transform:translateX(0)}}to{{transform:translateX(-{rw:.1f}px)}}}}')
        s.r(f'<g class="m{i}">')
        for rep in range(int(1200 / rw) + 2):
            for x0, w, t in items:
                xx = 48 + rep * rw + x0 - (rw / 3 if i == 1 else 0)
                c = t in core
                s.r(f'<rect x="{xx:.1f}" y="{y}" width="{w:.1f}" height="68" rx="34" fill="{"#fff" if c else "none"}" stroke="#fff" stroke-opacity="{1 if c else .45}" stroke-width="1.5"/>')
                s.t(xx + 28, y + 42, t, 'M', 22, ACC if c else '#fff')
        s.r('</g>')
    s.defs.append(f'<linearGradient id="fadeL"><stop offset="0" stop-color="{ACC}"/><stop offset="1" stop-color="{ACC}" stop-opacity="0"/></linearGradient>'
                  f'<linearGradient id="fadeR"><stop offset="0" stop-color="{ACC}" stop-opacity="0"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
    s.r(f'<rect x="0" y="130" width="90" height="{H-130}" fill="url(#fadeL)"/>', f'<rect x="1110" y="130" width="90" height="{H-130}" fill="url(#fadeR)"/>')
    s.save()

# ───────────────────────── CONTACT ─────────────────────────
def contact():
    H = 470
    s = Svg('contact', 1200, H, "Let's build something. hellokasko@gmail.com — open to remote full-stack and frontend roles and contracts.")
    card(s, INK)
    s.t(48, 72, 'CONTACT', 'M', 13, '#8a8d93', ls=3)
    s.t(44, 200, 'Let’s build', 'D', 100, '#fff', ls=-2)
    s.t(44, 316, 'something', 'D', 100, SOFT, ls=-2)
    w = W('something', 'D', 100, -2)
    s.r(f'<rect x="{44+w+10:.1f}" y="{316-CAP("D")*100:.1f}" width="26" height="{CAP("D")*100:.1f}" fill="{ACC}"><animate attributeName="opacity" values="1;0;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    cx, cy = 1062, 166
    s.css.append(f'.nudge{{animation:nudge 2.4s ease-in-out infinite}}@keyframes nudge{{50%{{transform:translate(8px,-8px)}}}}'
                 f'.ring{{transform-origin:{cx}px {cy}px;animation:ring 2.4s ease-out infinite}}@keyframes ring{{from{{transform:scale(1);opacity:.6}}to{{transform:scale(1.5);opacity:0}}}}')
    s.r(f'<circle class="ring" cx="{cx}" cy="{cy}" r="64" fill="none" stroke="{ACC}" stroke-width="2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="64" fill="{ACC}"/>', f'<g class="nudge">{arrow_ne(cx, cy, 18, "#fff", 4)}</g>')
    s.r(f'<rect x="48" y="372" width="1104" height="1" fill="#fff" fill-opacity=".16"/>')
    s.t(48, 422, 'hellokasko@gmail.com', 'M', 24, '#fff')
    s.t(1152, 420, 'Open to remote full-stack and frontend roles and contracts', 'B', 17, '#a3a6ad', anchor='end')
    s.save()

def button(name, label, primary=False):
    s = Svg(name, 290, 76, label)
    bg, fg = (ACC, '#fff') if primary else (PAPER, INK)
    s.r(f'<rect width="290" height="76" rx="38" fill="{bg}"/>')
    s.t(32, 46, label, 'M', 20, fg)
    s.css.append('.nudge{animation:nudge 2.4s ease-in-out infinite}@keyframes nudge{50%{transform:translate(3px,-3px)}}')
    s.r(f'<circle cx="244" cy="38" r="24" fill="{"#fff" if primary else ACC}"/>', f'<g class="nudge">{arrow_ne(244, 38, 6.5, ACC if primary else "#fff", 2.4)}</g>')
    s.save()

hero(); numbers()
header('projects', 'Projects', 'Selected work, from idea to production')
project('project-unifiedone', '01', 'Frontend', 'UnifiedONE',
        'Security platform that connects Microsoft security signals, multi-vendor threat intelligence and cross-tenant knowledge.',
        ['Helped turn the codebase into a unified system of reusable components, cutting the time spent on new development',
         'Introduced unit testing for more stable code', 'Migrated the app from Vue 2 to Vue 3'],
        ['Vue', 'Vuetify', 'Docker'], 'app.unifiedone.com', mock_security)
project('project-autoservice', '02', 'Full cycle: frontend and API', 'Auto service platform',
        'Admin platform for an auto service: repair intake, service boards and work stages, planning, and a live queue of today’s cars.',
        ['Helped the business bring all management into one system, from orders to scheduling',
         'Covered the business’s need for auto service management built around its own processes'],
        ['Vue 3', 'Vuetify', 'Pinia', 'TypeScript', 'Node.js', 'Express', 'PostgreSQL', 'WebSocket', 'Docker'],
        None, mock_nda,
        note='Built for a specific client under NDA, so there is no public link. The Repair Service project below covers the same domain.')
project('project-repairservice', '03', 'Full cycle: frontend and API', 'Repair Service',
        'Multi-tenant SaaS for auto repair shops: companies and branches, a service board with drag and drop, clients, a calendar and realtime updates.',
        ['Tenant isolation is tested in every module, so one company never sees another’s data',
         'Permissions are enforced on the server, and the UI only reflects them',
         'Realtime updates across tabs, with edit-conflict detection on save'],
        ['React 19', 'TypeScript', 'Tailwind CSS', 'TanStack Query', 'Go', 'PostgreSQL', 'Docker', 'Playwright'],
        'repair-service-admin.vercel.app', mock_kanban, note='The link opens a live demo with sample data.')
project('project-vibewaller', '04', 'Hobby project', 'Vibewaller',
        'Personal finance tracker: balance and assets, transaction history, category limits, self-employed taxes, a wishlist with price tracking, and expenses logged through a Telegram bot.',
        ['Built for my own needs, and I use it every day', 'Realtime sync and per-user data protection with Supabase RLS'],
        ['Vue 3', 'TypeScript', 'Tailwind CSS', 'Chart.js', 'TanStack Query', 'Supabase', 'Vitest', 'Docker'],
        'app.vibewaller.xyz', mock_finance)
experience(); stack()
header('activity', 'Activity', 'Contributions, eaten daily by a cobalt snake')
contact()
for n, l, p in [('btn-email', 'Email', True), ('btn-telegram', 'Telegram', False), ('btn-linkedin', 'LinkedIn', False), ('btn-cv', 'Download CV', False)]:
    button(n, l, p)
print('ok')
