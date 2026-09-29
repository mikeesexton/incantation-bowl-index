"""Stage Bhayro et al. 2018 (Aramaic Magic Bowls in the Vorderasiatisches Museum) selected-text editions.

Staging aid for proofreading, not a review. Output is protected source text and
must be written only under data/private/. Each edition prints a numbered
transliteration block and a numbered TRANSLATION block (fragmentary editions
repeat the pair per fragment). The script starts at the first line numbered 1,
keeps the part heading printed just before it, joins wraps, keeps position and
part headings, drops footnotes, footnote reference numerals and overlaid space
glyphs, encloses grey-shaded "unclear letters" (drawn as translucent 10 pt
strokes) in U+2E22/U+2E23, and small raised/lowered insertions in U+2E0C/U+2E0D
and U+2E1C/U+2E1D. Every staged row must still be compared with rendered pages.

Usage: PYTHONPATH=src python3 scripts/stage_berlin2018_editions.py ROWS.json OUT.json
"""
import pdfplumber, re, statistics, unicodedata
pdf = None
OFF = 14
def setup(path):
    global pdf
    pdf = pdfplumber.open(path)

def cluster(chars, tol=2.5):
    lines = []
    for c in sorted(chars, key=lambda c: c['top']):
        if lines and abs(c['top'] - lines[-1]['top']) <= tol: lines[-1]['c'].append(c)
        else: lines.append({'top': c['top'], 'c': [c]})
    for L in lines: L['c'].sort(key=lambda c: c['x0'])
    return lines

def footnote_top(pg):
    tops = [r['top'] for r in pg.lines + pg.rects if 40 < r['x1'] - r['x0'] < 60 and r['bottom'] - r['top'] < 1.5 and r['top'] > 200 and (r.get('linewidth') or 0) < 2]
    return min(tops) if tops else pg.height

def drop_overlapping_spaces(cs):
    glyphs = [c for c in cs if c['text'].strip()]
    return [c for c in cs if c['text'].strip() or not any(min(c['x1'], g['x1']) - max(c['x0'], g['x0']) > 0.7 * max(c['x1'] - c['x0'], 0.1) for g in glyphs)]

def is_fnref(c):
    return c['text'].isdigit() and 'Bold' not in c['fontname'] and (c['x1'] - c['x0']) < 0.42 * c['size']

def line_text(cs, notes, p, skip_first=None):
    cs = drop_overlapping_spaces(cs)
    OPEN = {'raised': '⸌', 'lowered': '⸜', 'small': '⸌'}; CLOSE = {'raised': '⸍', 'lowered': '⸝', 'small': '⸍'}
    toks = []   # (text, unclear, pos) with ' ' for word spaces
    prev = None
    for c in cs:
        if skip_first is not None and id(c) in skip_first: continue
        if is_fnref(c):
            notes.append(('fnref', p, c['text'])); prev = c; continue
        t = c['text']
        if not t.strip():
            if toks and toks[-1][0] != ' ': toks.append((' ', None, None))
            prev = c; continue
        if prev is not None and c['x0'] - prev['x1'] > 1.6 and toks and toks[-1][0] != ' ': toks.append((' ', None, None))
        toks.append((t, bool(c.get('unclear')), c.get('pos'))); prev = c
    while toks and toks[-1][0] == ' ': toks.pop()
    while toks and toks[0][0] == ' ': toks.pop(0)
    s = ''; u = False; pos = None
    for i, (t, uc, ps) in enumerate(toks):
        if t == ' ':
            nxt = toks[i + 1] if i + 1 < len(toks) else (None, None, None)
            if u and not (nxt[1] and nxt[2] == pos): s += '⸣'; u = False
            if pos and nxt[2] != pos: s += CLOSE[pos]; pos = None
            s += ' '; continue
        if ps != pos:
            if u: s += '⸣'; u = False
            if pos: s += CLOSE[pos]
            if ps: s += OPEN[ps]
            pos = ps
        if uc and not u: s += '⸢'; u = True
        if not uc and u: s += '⸣'; u = False
        s += t
    if u: s += '⸣'
    if pos: s += CLOSE[pos]
    return re.sub(r' +', ' ', s).strip()

def split_number(L):
    """Return (label, ids of number glyphs, text-start x) if the line starts with a line number."""
    cs = [c for c in L['c'] if c['text'].strip()]
    if not cs or not cs[0]['text'].isdigit(): return None
    k = 0
    while k < len(cs) and re.match(r'[0-9a-z–-]', cs[k]['text']) and (k == 0 or cs[k]['x0'] - cs[k - 1]['x1'] < 1.0): k += 1
    lab = ''.join(c['text'] for c in cs[:k])
    if k >= len(cs) or not re.fullmatch(r'\d+[a-z]?(?:[–-]\d+[a-z]?)?', lab): return None
    if cs[k]['x0'] - cs[k - 1]['x1'] < 5: return None
    return lab, {id(c) for c in cs[:k]}, cs[k]['x0']

FIELD = re.compile(r'^[A-Z][A-Za-z ]+: ?\S')

def edition_rows(pages, vocab=None):
    notes = []; used = set()
    items = []   # (page, kind, payload)
    for p in pages:
        pg = pdf.pages[p - 1]; ft = footnote_top(pg)
        chars = [dict(c) for c in pg.chars if 50 < c['top'] < ft - 2 and c['size'] > 10.5]
        small = [dict(c) for c in pg.chars if 50 < c['top'] < ft - 2 and 5.5 < c['size'] <= 10.5]
        shades = [l for l in pg.lines if (l.get('linewidth') or 0) >= 5]
        for c in chars + small:
            cx = (c['x0'] + c['x1']) / 2; cy = (c['top'] + c['bottom']) / 2
            if c['text'].strip() and any(l['x0'] - 0.3 <= cx <= l['x1'] + 0.3 and abs(cy - l['top']) <= l['linewidth'] / 2 + 0.5 for l in shades):
                c['unclear'] = True
        ls = cluster(chars)
        for c in small:
            best = min(ls, key=lambda L: abs(L['top'] - c['top']), default=None)
            if best is None or abs(best['top'] - c['top']) > 9: notes.append(('small-unplaced', p, c['text'])); continue
            c['pos'] = 'raised' if c['top'] < best['top'] - 1 else ('lowered' if c['top'] > best['top'] + 1 else 'small')
            best['c'].append(c)
        for L in ls: L['c'].sort(key=lambda c: c['x0'])
        starts = [sn[2] for sn in (split_number(L) for L in ls) if sn]
        indent = statistics.median(starts) if starts else None
        for L in ls:
            raw = ''.join(c['text'] for c in L['c']).strip()
            if not raw: continue
            if raw == 'TRANSLATION': items.append((p, 'TR', None)); continue
            if re.fullmatch(r'[A-Z][A-Z ]{5,}', raw): items.append((p, 'END', raw)); continue
            if re.fullmatch(r'(FIGURE|Figure|Fig\.) .*', raw): continue
            sn = split_number(L)
            if sn: items.append((p, 'num', (sn[0], line_text(L['c'], notes, p, skip_first=sn[1])))); continue
            x0 = [c for c in L['c'] if c['text'].strip()][0]['x0']
            t = line_text(L['c'], notes, p)
            if indent is not None and x0 < indent - 8: items.append((p, 'head', t))
            else: items.append((p, 'cont', t))
    # start at the first line numbered 1; keep the heading printed just before it
    start = next((i for i, it in enumerate(items) if it[1] == 'num' and re.match(r'1(?:[a-z]|[–-]\d+)?$', it[2][0])), None)
    if start is None: return '', '', notes + [('no-start',)], []
    pre = None
    if start > 0 and items[start - 1][1] == 'head' and not FIELD.match(items[start - 1][2]) and len(items[start - 1][2]) < 110 \
       and re.search(r'(:$|^[a-z] \S|^[IVX]+$)', items[start - 1][2]):
        pre = start - 1
    seq = items[pre if pre is not None else start:]
    part = None
    out = {'transliteration': [], 'translation': []}; mode = 'transliteration'; lastp = {'transliteration': None, 'translation': None}
    for i, (p, kind, pay) in enumerate(seq):
        if kind == 'END':
            if mode == 'translation': break
            continue
        if kind == 'TR':
            mode = 'translation'
            nxt = next((it for it in seq[i + 1:] if it[1] != 'cont'), None)
            if False and part and not (nxt and nxt[1] == 'head'):
                if lastp[mode] != p: out[mode].append(f"[PDF page {p}; printed p. {p - OFF}]"); lastp[mode] = p; used.add(p)
                out[mode].append(part); notes.append(('part-label-copied', p, part))
            continue
        if kind == 'head' and mode == 'translation' and any(k == 'TR' for _, k, _ in seq[i + 1:]):
            mode = 'transliteration'
        if kind == 'head' and mode == 'transliteration': part = pay if re.match(r'^[a-z] \S', pay) else None
        if kind == 'head' and FIELD.match(pay):
            notes.append(('field-skipped', p, pay[:40])); continue
        dst = out[mode]
        if lastp[mode] != p:
            dst.append(f"[PDF page {p}; printed p. {p - OFF}]"); lastp[mode] = p; used.add(p)
        if kind == 'num': dst.append(pay[0] + '. ' + pay[1])
        elif kind == 'head': dst.append(pay); notes.append(('heading', p, mode, pay[:50]))
        else:
            t = pay
            idx = max((j for j, v in enumerate(dst) if re.match(r'^\S+\. ', v) and not v.startswith('[PDF')), default=None)
            if idx is None: notes.append(('unattached', p, mode, t)); continue
            s0 = dst[idx]
            if re.search(r'[^\W\d_][\u0300-\u036f]*-$', s0):
                w = re.sub(r'[^\w]', '', (re.search(r'(\S+)-$', s0).group(1) + re.match(r'(\S+)', t).group(1)).lower())
                if mode == 'translation' and vocab is not None and w in vocab and t[:1].islower(): dst[idx] = s0[:-1] + t
                elif mode == 'transliteration' and t[:1].islower(): dst[idx] = s0[:-1] + t; notes.append(('translit-hyphen-joined', p, w))
                else: dst[idx] = s0 + t; notes.append(('kept-hyphen', p, w))
            else: dst[idx] = s0 + ' ' + t
    res = {}
    for k, v in out.items():
        keep = [l for i, l in enumerate(v) if not (l.startswith('[PDF') and (i + 1 == len(v) or v[i + 1].startswith('[PDF')))]
        res[k] = unicodedata.normalize('NFC', '\n'.join(keep))
    return res['transliteration'], res['translation'], notes, sorted(used)


SHA256 = '7a25b7b89f8160aaec249988f47a5fb08b654c8ca9506b44fcc48ee60cde6aac'


def stage(rows, root='.'):
    from pathlib import Path
    setup(str(Path(root) / 'data/private/archive/sha256' / SHA256[:2] / SHA256))
    voc = set()
    for pg in pdf.pages[:120]: voc.update(w.lower() for w in re.findall(r"[A-Za-z]+", pg.extract_text() or ''))
    ent = {}
    for r in rows:
        m = re.match(r'Edition (\d+) \(Roman section\), printed pp\. (\d+)–(\d+)', r['locator'])
        if not m: continue
        n = int(m.group(1)); e = ent.setdefault(n, {'pages': list(range(int(m.group(2)) + OFF, int(m.group(3)) + OFF + 1)), 'rows': {}})
        e['rows'][r['text_type']] = r['id']
    out = {}
    for n in sorted(ent):
        h, e, notes, used = edition_rows(ent[n]['pages'], voc)
        out[n] = {'pages': used, 'rows': ent[n]['rows'], 'transliteration': h, 'translation': e, 'notes': notes}
    return out


if __name__ == '__main__':
    import argparse, json, sys
    ap = argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('output')
    a = ap.parse_args()
    if not str(a.output).startswith('data/private/'):
        sys.exit('Staged edition text is protected; write it under data/private/.')
    json.dump(stage(json.load(open(a.rows))), open(a.output, 'w'), ensure_ascii=False, indent=1)
