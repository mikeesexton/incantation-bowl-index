"""Stage Burberry 2020 (Exeter PhD thesis) edition columns from PDF glyph positions.

Staging aid for proofreading, not a review. Output is protected source text and
must be written only under data/private/. Each bowl prints a Hebrew-script
column, a line-number column and an English column after an italic "Text"
heading. The script splits the columns at the median x of the line numbers,
orders Hebrew right to left, reads bracket orientation from the rendered glyph
(the Word text layer does not mirror brackets consistently, even in English),
marks grey highlights (partially visible) with U+05AF, cartouches with
U+27E6/U+27E7, crossed-out text with U+0336 and small raised insertions with
U+2E0C/U+2E0D, drops space glyphs laid over letters and footnote numerals, and
stops at italic "Notes"/"Commentary" headings. Every staged row must still be
compared with rendered pages.

Usage: PYTHONPATH=src python3 scripts/stage_burberry_edition_columns.py ROWS.json OUT.json
"""
import pdfplumber, re, json, sys, unicodedata, statistics
pdf = None
HEB = re.compile(r'[֐-׿]')
PART = '֯'      # partially visible (grey highlight)
STRIKE = '̶'
def setup(path):
    global pdf
    pdf = pdfplumber.open(path)

NUMRE = re.compile(r'^\d+(?:[–-]\d+)?[a-z]?$')
END = re.compile(r'^(Notes|Commentary|Drawing|Figure|Text on|Previous|Parallels|Translation notes)\b')

import numpy as np
_img = {}
PAIRS = {'[': 's', ']': 's', '(': 'p', ')': 'p', '{': 'c', '}': 'c'}
OPEN = {'s': '[', 'p': '(', 'c': '{'}; CLOSE = {'s': ']', 'p': ')', 'c': '}'}
def open_shape(c):
    p = c['page_number']
    if p not in _img:
        _img.clear(); _img[p] = np.array(pdf.pages[p - 1].to_image(resolution=600).original.convert('L'))
    a = _img[p]; k = 600 / 72
    sub = a[int(c['top'] * k):int(c['bottom'] * k) + 1, int(c['x0'] * k):int(c['x1'] * k) + 1] < 140
    ys, xs = np.nonzero(sub)
    if len(xs) < 5: return None
    y0, y1 = ys.min(), ys.max(); h = y1 - y0 + 1
    if c['text'] in '[]':
        # the horizontal ticks of '[' run to the right of the vertical stroke (slant-safe: compare each tick with the stroke just inside it)
        votes = []
        for tick, inner in ((y0, y0 + int(h * 0.25)), (y1, y1 - int(h * 0.25))):
            tx = xs[np.abs(ys - tick) <= 1]; sx = xs[np.abs(ys - inner) <= 1]
            if len(tx) and len(sx): votes.append(tx.mean() - sx.mean())
        if not votes: return None
        v = sum(votes)
        return None if abs(v) < 0.5 else v > 0
    mid = xs[(ys > y0 + h / 3) & (ys < y1 - h / 3)]; ends = xs[(ys <= y0 + h / 6) | (ys >= y1 - h / 6)]
    if len(mid) == 0 or len(ends) == 0: return None
    return mid.mean() < ends.mean()
def bracket(c, rtl, notes):
    k = PAIRS[c['text']]; sh = open_shape(c)
    if sh is None:
        notes.append(('bracket-shape-unknown', c['page_number'], c['text'])); return c['text']
    if rtl: sh = not sh
    return OPEN[k] if sh else CLOSE[k]

def cluster(chars, tol=3.0):
    lines = []
    for c in sorted(chars, key=lambda c: c['top']):
        if lines and abs(c['top'] - lines[-1]['top']) <= tol: lines[-1]['c'].append(c)
        else: lines.append({'top': c['top'], 'c': [c]})
    for L in lines: L['c'].sort(key=lambda c: c['x0'])
    return lines

def ltxt(L): return ''.join(c['text'] for c in L['c']).strip()

def page_objs(p):
    pg = pdf.pages[p - 1]
    greys = [r for r in pg.rects if r.get('non_stroking_color') in (0.827, (0.827,), [0.827]) and r['bottom'] - r['top'] > 6]
    thin = [r for r in pg.rects + pg.lines if min(r['x1'] - r['x0'], r['bottom'] - r['top']) < 1.5]
    return pg, greys, thin

def mark_chars(pg, greys, thin, chars):
    hs = [r for r in thin if r['x1'] - r['x0'] >= 1.5 and r['bottom'] - r['top'] < 1.5]   # horizontal
    vs = [r for r in thin if r['bottom'] - r['top'] >= 1.5 and r['x1'] - r['x0'] < 1.5]   # vertical
    boxes = []
    for l in vs:
        for r in vs:
            if r['x0'] > l['x1'] + 2 and abs(r['top'] - l['top']) < 1.5 and abs(r['bottom'] - l['bottom']) < 1.5:
                tops = [h for h in hs if h['x0'] <= l['x1'] + 1.5 and h['x1'] >= r['x0'] - 1.5 and abs(h['top'] - l['top']) < 2]
                bots = [h for h in hs if h['x0'] <= l['x1'] + 1.5 and h['x1'] >= r['x0'] - 1.5 and abs(h['top'] - l['bottom']) < 2]
                if tops and bots: boxes.append((l['x1'], r['x0'], l['top'], l['bottom']))
    # keep the tightest box for each left rule
    boxes = sorted(set(boxes), key=lambda b: b[1] - b[0])
    tight = []
    for b in boxes:
        if not any(t[0] == b[0] and t[2] == b[2] for t in tight): tight.append(b)
    boxes = tight
    # strikeout rules must not be box edges
    edge = {id(h) for h in hs for b in boxes if abs(h['top'] - b[2]) < 2 or abs(h['top'] - b[3]) < 2}
    hs = [h for h in hs if id(h) not in edge]
    for c in chars:
        c['t'] = c['text']
        if not c['text'].strip(): continue
        cx = (c['x0'] + c['x1']) / 2; cy = (c['top'] + c['bottom']) / 2
        if any(r['x0'] - 0.3 <= cx <= r['x1'] + 0.3 and r['top'] - 0.5 <= cy <= r['bottom'] + 0.5 for r in greys):
            c['grey'] = True
        # strikeout: horizontal rule through the middle band of the glyph
        h = c['bottom'] - c['top']
        if any(r['x0'] <= cx <= r['x1'] and c['top'] + 0.3 * h <= r['top'] <= c['top'] + 0.8 * h for r in hs):
            c['strike'] = True
        for bx_ in boxes:
            if bx_[0] <= cx <= bx_[1] and bx_[2] <= cy <= bx_[3] and not c.get('strike'):
                c['box'] = bx_; break

def block_bounds(pg, chars, first, heading):
    top, bottom = 35, pg.height - 70
    ls = cluster(chars)
    if first:
        found = False
        for L in ls:
            t = ltxt(L)
            if all('Italic' in c['fontname'] for c in L['c'] if c['text'].strip()) and t in heading:
                top = L['top'] + 6; found = True; heading = [h for h in heading if h != t]
                break
        if not found: raise ValueError('text heading not found p%d' % pg.page_number)
    for L in ls:
        if L['top'] <= top: continue
        t = ltxt(L)
        if all('Italic' in c['fontname'] for c in L['c'] if c['text'].strip()) and END.match(t):
            bottom = min(bottom, L['top'] - 2); break
        if re.match(r'^ACB \d+', t) and any('Bold' in c['fontname'] for c in L['c']):
            bottom = min(bottom, L['top'] - 2); break
    # footnote separator: short rule in the lower part of the page
    for r in pg.lines + pg.rects:
        if 100 < r['x1'] - r['x0'] < 160 and r['bottom'] - r['top'] < 1.5 and r['top'] > top and r['top'] > pg.height * 0.5:
            below = [c for c in chars if 0 < c['top'] - r['top'] < 14 and c['text'].strip()]
            if below and all(c['size'] < 11 for c in below): bottom = min(bottom, r['top'] - 2)
    return top, bottom

def numbers(chars):
    ls = cluster(chars)
    cands = []
    for L in ls:
        ws = []; cur = []
        for c in L['c']:
            if not c['text'].strip():
                if cur: ws.append(cur); cur = []
                continue
            if cur and c['x0'] - cur[-1]['x1'] > 2.0: ws.append(cur); cur = []
            cur.append(c)
        if cur: ws.append(cur)
        for w in ws:
            t = ''.join(c['text'] for c in w)
            if NUMRE.match(t) and all(abs(c['size'] - 12) < 0.6 and 'Italic' not in c['fontname'] for c in w):
                cands.append((L['top'], t, w[0]['x0'], w[-1]['x1'], w))
    xs = [(a[2] + a[3]) / 2 for a in cands if 250 < (a[2] + a[3]) / 2 < 360]
    if not xs: return [], None
    mx = statistics.median(xs)
    return [a for a in cands if abs((a[2] + a[3]) / 2 - mx) < 8], mx

def drop_overlapping_spaces(cs):
    glyphs = [c for c in cs if c['text'].strip()]
    out = []
    for c in cs:
        if not c['text'].strip():
            if any(min(c['x1'], g['x1']) - max(c['x0'], g['x0']) > 1.0 for g in glyphs): continue
        out.append(c)
    return out

def rtl_line(cs, notes, p):
    cs = drop_overlapping_spaces(cs)
    cs = sorted([c for c in cs], key=lambda c: -(c['x0'] + c['x1']) / 2)
    s = ''; prev = None; raised = False; boxed = None
    for c in cs:
        t = c['text']
        if t == ' ' or not t.strip():
            if not s.endswith(' ') and s: s += ' '
            prev = c; continue
        if prev is not None and prev['x0'] - c['x1'] > 3.0 and not s.endswith(' '): s += ' '
        small = c['size'] < 11
        if small and HEB.match(t) and not raised: s += '⸌'; raised = True
        if raised and not (small and HEB.match(t)): s += '⸍'; raised = False
        b = c.get('box')
        if b != boxed:
            if boxed is not None: s += '⟧'
            if b is not None: s += '⟦'
            boxed = b
        s += bracket(c, True, notes) if t in PAIRS else t
        if c.get('grey'): s += PART
        if c.get('strike'): s += STRIKE
        prev = c
    if raised: s += '⸍'
    if boxed is not None: s += '⟧'
    s = re.sub(r' +', ' ', s).strip()
    # Latin runs inside RTL text were collected right-to-left; restore their order
    s = re.sub(r'[A-Za-z0-9ʾʿ̀-ͯ][A-Za-z0-9ʾʿ̀-ͯ.,;:()?! -]*[A-Za-z0-9ʾʿ.)̀-ͯ]',
               lambda m: m.group(0)[::-1] if not HEB.search(m.group(0)) else m.group(0), s)
    s = s.replace('⟦ ', ' ⟦').replace(' ⟧', '⟧ ')
    return re.sub(r' +', ' ', s).strip()

def ltr_line(cs, notes, p):
    cs = drop_overlapping_spaces(cs)
    s = ''; prev = None; boxed = None
    for c in sorted(cs, key=lambda c: c['x0']):
        t = c['text']
        if t.strip():
            b = c.get('box')
            if b != boxed:
                if boxed is not None: s += '⟧'
                if b is not None: s += ('' if s.endswith(' ') or not s else '') + '⟦'
                boxed = b
        if c['size'] < 11 and t.isdigit():
            notes.append(('fnref', p, t)); continue
        if not t.strip():
            if s and not s.endswith(' '): s += ' '
            prev = c; continue
        if prev is not None and c['x0'] - prev['x1'] > 3.0 and not s.endswith(' '): s += ' '
        s += (bracket(c, False, notes) if t in PAIRS else t) + (STRIKE if c.get('strike') else '')
        prev = c
    if boxed is not None: s += '⟧'
    s = s.replace('⟦ ', ' ⟦').replace(' ⟧', '⟧ ')
    return re.sub(r' +', ' ', s).strip()

def entry_rows(pages, heading, vocab=None):
    heb, eng, notes, used = [], [], [], []
    for k, p in enumerate(pages):
        pg, greys, thin = page_objs(p)
        chars = [dict(c) for c in pg.chars]
        top, bottom = block_bounds(pg, chars, k == 0, heading)
        body = [c for c in chars if top < c['top'] < bottom]
        nums, mx = numbers(body)
        if not nums and k > 0:
            # a continuation page may carry only unnumbered English/Hebrew lines; accept if a previous page set the split
            if not used: continue
            mx = last_mx
        if mx is None: notes.append(('no-numbers', p)); continue
        last_mx = mx
        used.append(p)
        mark_chars(pg, greys, thin, body)
        numids = {id(c) for a in nums for c in a[4]}
        nx0 = min((a[2] for a in nums), default=mx - 4); nx1 = max((a[3] for a in nums), default=mx + 4)
        rest = [c for c in body if id(c) not in numids]
        left = [c for c in rest if c['x1'] <= nx0 - 1]
        right = [c for c in rest if c['x0'] >= nx1 + 1]
        mid = [c for c in rest if c not in left and c not in right and c['text'].strip()]
        if mid: notes.append(('mid-chars', p, ''.join(c['text'] for c in mid)))
        header = f"[PDF page {p}; printed p. {p}]"
        heb.append(header); eng.append(header)
        starts = sorted((a[0], a[1]) for a in nums)
        # italic headings inside the block (full-width or left column), e.g. "Inside", "Rim"
        heads = []
        for L in cluster(rest):
            t = ltxt(L)
            gl = [c for c in L['c'] if c['text'].strip()]
            if t and gl and all('Italic' in c['fontname'] for c in gl) and not any(abs(a[0] - L['top']) < 3 for a in nums) \
               and max(c['x1'] for c in gl) <= nx0 and min(c['x0'] for c in gl) < 120 and not any(HEB.match(c['text']) for c in gl):
                heads.append((L['top'], t, {id(c) for c in L['c']}))
        hid = set().union(*[h[2] for h in heads]) if heads else set()
        left = [c for c in left if id(c) not in hid]; right = [c for c in right if id(c) not in hid]
        marks = sorted([(t0, 'num', lab) for t0, lab in starts] + [(h[0], 'head', h[1]) for h in heads])
        def assign(chars):
            sec = {}
            for L in cluster(chars):
                key = None
                for t0, kind, lab in marks:
                    if L['top'] >= t0 - 3: key = (t0, kind, lab)
                sec.setdefault(key, []).append(L)
            return sec
        ls, rs = assign(left), assign(right)
        def join_eng(lines):
            s = ''
            for x in lines:
                if not s: s = x; continue
                if re.search(r'[-\[]-$', s): s += x; continue
                if re.search(r'[^\W\d_][\u0300-\u036f]*-$', s) and x[:1].isupper():
                    s += x; continue
                if re.search(r'[^\W\d_][\u0300-\u036f]*-$', s) and x[:1].islower():
                    w = (re.search(r'(\S+)-$', s).group(1) + re.match(r'(\S+)', x).group(1)).lower()
                    w = re.sub(r'[^\w]', '', w)
                    if vocab is not None and w in vocab: s = s[:-1] + x
                    else: s += x; notes.append(('kept-hyphen', p, w))
                else: s += ' ' + x
            return s
        def cont(sec, out, fn, joiner):
            if None in sec:
                lines = [fn(L['c'], notes, p) for L in sec[None]]
                idx = max((i for i, v in enumerate(out) if re.match(r'^\S+\. ', v) and not v.startswith('[PDF')), default=None)
                if idx is None: notes.append(('unattached', p, lines))
                else: out[idx] = joiner([out[idx]] + lines); notes.append(('continued', p))
        def join_heb(xs):
            out = ''
            for x in xs:
                out = x if not out else (out + x if re.search(r'[-\[]-$', out) else out + ' ' + x)
            return out
        cont(ls, heb, rtl_line, join_heb)
        cont(rs, eng, ltr_line, join_eng)
        for key in marks:
            t0, kind, lab = key
            if kind == 'head':
                heb.append(lab); eng.append(lab); continue
            hl = [rtl_line(L['c'], notes, p) for L in ls.get(key, [])]
            hl = [join_heb(hl)] if hl else hl
            el = [ltr_line(L['c'], notes, p) for L in rs.get(key, [])]
            heb.append(lab + '. ' + ' '.join(hl) if hl else lab + '.')
            eng.append(lab + '. ' + join_eng(el) if el else lab + '.')
            if not hl or not el: notes.append(('empty-side', p, lab, bool(hl), bool(el)))
    def fix(s):
        s = re.sub(r'⸍ ⸌', ' ', s); s = re.sub(r' ⸍', '⸍ ', s); s = re.sub(r'⸌ ', ' ⸌', s)
        s = re.sub(r'(?<=-) +(?=-)', '', s); s = re.sub(r' +', ' ', s)
        return unicodedata.normalize('NFC', '\n'.join(l.strip() for l in s.split('\n')))
    return fix('\n'.join(heb)), fix('\n'.join(eng)), notes, used


SHA256 = '63637559c176da93f3d20e346f9db17533573988f749f5cfabaf88e453119fbe'


def stage(rows, root='.'):
    from pathlib import Path
    setup(str(Path(root) / 'data/private/archive/sha256' / SHA256[:2] / SHA256))
    voc = set()
    for pg in pdf.pages: voc.update(w.lower() for w in re.findall(r"[A-Za-z]+", pg.extract_text() or ''))
    ent = {}
    for r in rows:
        m = re.match(r'ACB (\d+), printed (?:(Fragment [AB]), )?pp?\. (\d+)(?:–(\d+))?$', r['locator'])
        key = (int(m.group(1)), m.group(2) or ''); a = int(m.group(3)); b = int(m.group(4) or a)
        e = ent.setdefault(key, {'pages': set(), 'rows': {}}); e['pages'].update(range(a, b + 1)); e['rows'][r['text_type']] = r['id']
    out = {}
    for key in sorted(ent):
        k = f"{key[0]}{key[1][-1:] if key[1] else ''}"
        h, e, notes, used = entry_rows(sorted(ent[key]['pages']), ['Text'], voc)
        out[k] = {'pages': used, 'rows': ent[key]['rows'], 'transcription': h, 'translation': e, 'notes': notes}
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('output')
    a = ap.parse_args()
    if not str(a.output).startswith('data/private/'):
        sys.exit('Staged edition text is protected; write it under data/private/.')
    json.dump(stage(json.load(open(a.rows))), open(a.output, 'w'), ensure_ascii=False, indent=1)
