"""Stage Moriggi 2014 (A Corpus of Syriac Incantation Bowls) edition columns from PDF glyph positions.

Staging aid for proofreading, not a review. Output is protected source text and
must be written only under data/private/. The edition prints a Latin-script
transliteration, a line-number column and an English translation side by side.
This script takes the number column's median x on each page, splits the two text
columns around it, joins each numbered line's wraps, attaches page-top
continuation lines, keeps headings and number-column labels ("External
surface"), drops footnote reference numerals, stops at "Notes to the text" and
footnote rules (a 48 pt rule followed by small type; shorter-context rules are
underlines and are shown with U+0332), and attaches combining marks (seyame etc.)
to the glyph under which they are drawn: centre = mark x0 - 0.15 * size. Every
staged row must still be compared with rendered pages.

Usage: PYTHONPATH=src python3 scripts/stage_moriggi_edition_columns.py ROWS.json OUT.json
"""
import pdfplumber, re, json, sys, unicodedata, statistics
pdf = None
OFF = 18
def setup(path):
    global pdf
    pdf = pdfplumber.open(path)

def is_mark(t): return len(t) == 1 and unicodedata.category(t) in ('Mn', 'Me')
NUMRE = re.compile(r'^\d+(?:[–-]\d+)?[a-z]?$')

def words(chars, gap=1.2):
    """chars already on one line, marks attached. return text with spaces by gap."""
    out = ''; prev = None
    for c in chars:
        if prev is not None and c['x0'] - prev['x1'] > gap: out += ' '
        out += c['t']; prev = c
    return out

def page_chars(p):
    pg = pdf.pages[p - 1]
    chs = pg.chars
    notes = []
    base = [dict(c, t=c['text']) for c in chs if not is_mark(c['text'])]
    marks = [c for c in chs if is_mark(c['text'])]
    for m in marks:
        ctr = m['x0'] - 0.15 * m['size']
        cands = [b for b in base if abs(b['top'] - m['top']) < 4 and abs(b['size'] - m['size']) < 0.6 and b['text'].strip()]
        if not cands: notes.append(('orphan-mark', p, round(m['x0'], 1), round(m['top'], 1))); continue
        inside = [b for b in cands if b['x0'] <= ctr <= b['x1']]
        pick = min(inside or cands, key=lambda b: abs((b['x0'] + b['x1']) / 2 - ctr))
        if not inside:
            d = min(abs(pick['x0'] - ctr), abs(pick['x1'] - ctr))
            if d > 1: notes.append(('mark-far', p, round(m['x0'], 1), pick['text'], round(d, 1)))
        pick['t'] += m['text']
    return pg, base, notes

def cluster(chars, tol=2.5):
    lines = []
    for c in sorted(chars, key=lambda c: c['top']):
        if lines and abs(c['top'] - lines[-1]['top']) <= tol:
            lines[-1]['c'].append(c)
        else:
            lines.append({'top': c['top'], 'c': [c]})
    for L in lines: L['c'].sort(key=lambda c: c['x0'])
    return lines

def block_bounds(pg, base, first, entry_no):
    top, bottom = 50, pg.height - 40
    # running head
    top = 75
    ls = cluster([c for c in base])
    if first:
        found = False
        for L in ls:
            t = ''.join(c['t'] for c in L['c'] if c['size'] > 9.5)
            if re.match(r'Bowlno\.%d(?!\d)' % entry_no, t.replace(' ', '')) and any('Bold' in c['fontname'] for c in L['c']):
                top = L['top'] + 8; found = True; break
        if not found: raise ValueError('heading not found p%d' % pg.page_number)
    for L in ls:
        if L['top'] <= top: continue
        t = ''.join(c['t'] for c in L['c']).replace(' ', '')
        if (t.startswith('Notestothetext') or t.startswith('Previousreadings')) and any('Bold' in c['fontname'] for c in L['c']):
            bottom = min(bottom, L['top'] - 2); break
        if re.match(r'BOWLNO\.\d+$', t) or (re.match(r'Bowlno\.\d+', t) and any('Bold' in c['fontname'] for c in L['c'])):
            bottom = min(bottom, L['top'] - 2); break
    for r in footnote_rules(pg, base):
        if r['top'] > top and r['top'] < bottom:
            bottom = r['top'] - 2
    return top, bottom

def footnote_rules(pg, base):
    out = []
    for r in pg.lines + pg.rects:
        if abs(r['x1'] - r['x0'] - 48) < 3 and r['bottom'] - r['top'] < 2:
            below = [c for c in base if 0 < c['top'] - r['top'] < 16 and c['t'].strip()]
            if below and all(c['size'] < 9.6 for c in below): out.append(r)
            elif not below: out.append(r)
    return out

def underlines(pg, base):
    fr = {id(r) for r in footnote_rules(pg, base)}
    rs = [r for r in pg.lines + pg.rects if id(r) not in fr and r['bottom'] - r['top'] < 1.5 and r['x1'] - r['x0'] > 3]
    for c in base:
        cx = (c['x0'] + c['x1']) / 2
        for r in rs:
            if r['x0'] - 0.5 <= cx <= r['x1'] + 0.5 and c['bottom'] - 3 <= r['top'] <= c['bottom'] + 3:
                c['t'] = c['t'] + '\u0332' if c['t'].strip() else c['t']; break

def numbers(pg, base, top, bottom):
    ls = cluster([c for c in base if top < c['top'] < bottom])
    cands = []
    for L in ls:
        # words of the line
        ws = []; cur = []
        for c in L['c']:
            if cur and c['x0'] - cur[-1]['x1'] > 2.0: ws.append(cur); cur = []
            cur.append(c)
        if cur: ws.append(cur)
        for w in ws:
            t = ''.join(c['t'] for c in w)
            if NUMRE.match(t) and all('Roman' in c['fontname'] and abs(c['size'] - 10) < 0.6 for c in w):
                cands.append((L['top'], t, w[0]['x0'], w[-1]['x1'], w))
    xs = [ (a[2] + a[3]) / 2 for a in cands if 250 < a[2] < 340]
    if not xs: return [], None
    mx = statistics.median(xs)
    nums = [a for a in cands if abs((a[2] + a[3]) / 2 - mx) < 7]
    # word labels in the number column (e.g. "External surface")
    labs = []
    for L in ls:
        ws = []; cur = []
        for c in L['c']:
            if cur and c['x0'] - cur[-1]['x1'] > 2.0: ws.append(cur); cur = []
            cur.append(c)
        if cur: ws.append(cur)
        for w in ws:
            t = ''.join(c['t'] for c in w)
            if re.fullmatch(r'[A-Za-z]{3,}', t) and all('Italic' not in c['fontname'] and abs(c['size'] - 10) < 0.6 for c in w) \
               and abs((w[0]['x0'] + w[-1]['x1']) / 2 - mx) < 14:
                if labs and 0 < L['top'] - labs[-1][0] < 15 and not any(abs(a[0] - L['top']) < 3 for a in nums):
                    labs[-1][1] += ' ' + t; labs[-1][4].extend(w)
                else:
                    labs.append([L['top'], t, w[0]['x0'], w[-1]['x1'], list(w)])
    return nums + [tuple(l) for l in labs], mx

def entry_rows(entry_no, pages, vocab=None):
    heb, eng, notes = [], [], []
    used = []
    for k, p in enumerate(pages):
        pg, base, n0 = page_chars(p); notes += n0
        top, bottom = block_bounds(pg, base, k == 0, entry_no)
        underlines(pg, base)
        nums, mx = numbers(pg, base, top, bottom)
        if not nums:
            notes.append(('no-numbers', p)); continue
        used.append(p)
        numids = {id(c) for a in nums for c in a[4]}
        body = [c for c in base if top < c['top'] < bottom and id(c) not in numids and abs(c['size'] - 10) < 0.6]
        dropped = [c for c in base if top < c['top'] < bottom and id(c) not in numids and abs(c['size'] - 10) >= 0.6 and c['t'].strip()]
        if dropped: notes.append(('dropped-nonbody', p, ''.join(c['t'] for c in dropped)[:60]))
        dn = [a for a in nums if NUMRE.match(a[1])]
        nx0 = min(a[2] for a in dn); nx1 = max(a[3] for a in dn)
        left = [c for c in body if c['x1'] <= nx0 - 1]
        right = [c for c in body if c['x0'] >= nx1 + 1]
        mid = [c for c in body if c not in left and c not in right]
        if mid: notes.append(('mid-chars', p, ''.join(c['t'] for c in mid)))
        header = f"[PDF page {p}; printed p. {p - OFF}]"
        heb.append(header); eng.append(header)
        starts = sorted((a[0], a[1]) for a in nums)
        def assign(chars):
            sec = {}
            for L in cluster(chars):
                key = None; last = None
                for t0, lab in starts_all:
                    if L['top'] >= t0 - 3: last = (t0, lab)
                if last is not None and last[1] is None:
                    key = ('h', last[0])
                else:
                    for i, (t0, lab) in enumerate(starts):
                        if L['top'] >= t0 - 3: key = i
                sec.setdefault(key, []).append(L)
            return sec
        rlines = cluster(right)
        heads = []
        def roman_start(L):
            letters = [c for c in L['c'] if c['t'].strip() and c['t'][0].isalpha()]
            return letters and 'Italic' not in letters[0]['fontname'] and sum('Italic' not in c['fontname'] for c in letters[:4]) >= min(3, len(letters))
        for L in cluster(left):
            if any(abs(a[0] - L['top']) < 3 for a in nums): continue
            letters = [c for c in L['c'] if c['t'].strip() and c['t'][0].isalpha()]
            if not roman_start(L): continue
            rl = [R for R in rlines if abs(R['top'] - L['top']) < 3]
            if rl and not roman_start(rl[0]): continue
            heads.append((L['top'], words(L['c']), {id(c) for c in L['c']}, words(rl[0]['c']) if rl else None, {id(c) for c in rl[0]['c']} if rl else set()))
        hid = set().union(*[h[2] | h[4] for h in heads]) if heads else set()
        left = [c for c in left if id(c) not in hid]
        right = [c for c in right if id(c) not in hid]
        starts_all = sorted([(a[0], a[1]) for a in nums] + [(h[0], None) for h in heads])
        ls, rs = assign(left), assign(right)
        def txt(L): return words(L['c'])
        def join(lines):
            s = ''
            for x in lines:
                if not s: s = x; continue
                if re.search(r'[^\W\d_][̀-ͯ]*-$', s) and x[:1].islower():
                    w = re.search(r'(\S+)-$', s).group(1) + re.match(r'(\S+)', x).group(1)
                    w = re.sub(r'[^\w]', '', w).lower()
                    if vocab is not None and w in vocab: s = s[:-1] + x
                    else: s = s + x; notes.append(('kept-hyphen', p, w))
                else: s = s + ' ' + x
            return re.sub(' {2,}', ' ', s)
        # continuation (lines before first number)
        for sec, out, tag in ((ls, heb, 'left'), (rs, eng, 'right')):
            if None in sec:
                cont = [txt(L) for L in sec[None]]
                idx = max((i for i, v in enumerate(out) if re.match(r'^\S+\. ', v) and not v.startswith('[PDF')), default=None)
                if idx is None: notes.append(('unattached', p, tag, cont))
                else:
                    out[idx] = join([out[idx]] + cont); notes.append(('continued', p, tag))
        items = [(t0, 'num', i) for i, (t0, lab) in enumerate(starts)] + [(h[0], 'head', h) for h in heads]
        for t0, kind, v in sorted(items, key=lambda x: x[0]):
            if kind == 'head':
                hl = join([v[1]] + [txt(L) for L in ls.get(('h', v[0]), [])])
                hr = join([v[3] if v[3] is not None else v[1]] + [txt(L) for L in rs.get(('h', v[0]), [])])
                heb.append(hl); eng.append(hr); continue
            i = v; lab = starts[i][1]
            for sec, out, tag in ((ls, heb, 'left'), (rs, eng, 'right')):
                lines = [txt(L) for L in sec.get(i, [])]
                if lines: out.append(lab + '. ' + join(lines))
                else: notes.append(('empty-number', p, tag, lab))
    return unicodedata.normalize('NFC','\n'.join(heb)), unicodedata.normalize('NFC','\n'.join(eng)), notes, used


SHA256 = 'ce32170d182d4282a9610d42c2c6449b0435eba77851b18aa919544ddb4e5035'


def stage(rows, root='.'):
    from pathlib import Path
    setup(str(Path(root) / 'data/private/archive/sha256' / SHA256[:2] / SHA256))
    voc = set()
    for pg in pdf.pages:
        voc.update(w.lower() for w in re.findall(r"[A-Za-z]+", pg.extract_text(x_tolerance=1.5) or ''))
    ent = {}
    for r in rows:
        m = re.match(r'Bowl no\. (\d+), printed pp?\. (\d+)(?:–(\d+))?$', r['locator'])
        n, a = int(m.group(1)), int(m.group(2)); b = int(m.group(3) or a)
        ent.setdefault(n, {'pages': list(range(a + OFF, b + OFF + 1)), 'rows': {}})['rows'][r['text_type']] = r['id']
    def has_notes(p):
        pg, base, _ = page_chars(p)
        for L in cluster(base):
            t = ''.join(c['t'] for c in L['c']).replace(' ', '')
            if t.startswith('Notestothetext') or re.match(r'BOWLNO\.\d+$', t): return True
        return False
    out = {}
    for n in sorted(ent):
        pages = ent[n]['pages']
        while not has_notes(pages[-1]) and len(pages) < 6: pages.append(pages[-1] + 1)
        h, e, notes, used = entry_rows(n, pages, voc)
        out[n] = {'pages': used, 'rows': ent[n]['rows'], 'transliteration': h, 'translation': e, 'notes': notes}
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('output')
    a = ap.parse_args()
    if not str(a.output).startswith('data/private/'):
        sys.exit('Staged edition text is protected; write it under data/private/.')
    json.dump(stage(json.load(open(a.rows))), open(a.output, 'w'), ensure_ascii=False, indent=1)
