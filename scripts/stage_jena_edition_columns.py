"""Stage Ford and Morgenstern 2020 (Jena) edition columns from PDF glyph positions.

Staging aid for proofreading, not a review. Output is protected source text and
must be written only under data/private/. It orders original-script glyphs right
to left, joins each printed line number's wraps, keeps the editors' brackets
(orientation read from the rendered glyph, because the text layer does not mirror
them), marks grey "partially preserved" letters with U+0323, encloses small raised
letters in U+2E0C/U+2E0D, attaches Syriac combining marks by position, drops
footnote reference numerals and stops at footnote rules and "Notes"/"Previous
readings" headings. Every staged row must still be compared with rendered pages.

Usage: PYTHONPATH=src python3 scripts/stage_jena_edition_columns.py ROWS.json OUT.json
where ROWS.json is a private list of the source's text rows (id, text_type, locator).
"""
import pdfplumber,re,sys,json
import hashlib
from pathlib import Path
SHA256='23431f46510c5cf729ca35282413e0bedd21be44dbc80e56dcde7c709b9a99d4'
PDF=Path('data/private/archive/sha256')/SHA256[:2]/SHA256
pdf=pdfplumber.open(str(PDF))
GREY=(0.53,0.535,0.545)
DOTB='̣'; STRIKE='̶'
MIRROR={"(":")",")":"(","[":"]","]":"[","{":"}","}":"{","⟨":"⟩","⟩":"⟨","<":">",">":"<"}
LTRC='0-9A-Za-zÀ-ɏḀ-ỿʾʿ'
RTL=re.compile(r'[֐-׿܀-ݏ]')
import numpy as np
_img={}
BR={'(':'p',')':'p','[':'s',']':'s','{':'c','}':'c','⟨':'a','⟩':'a','<':'a','>':'a'}
OPEN={'p':'(','s':'[','c':'{','a':'⟨'}; CLOSE={'p':')','s':']','c':'}','a':'⟩'}
def shape(c):
    p=c['page_number']
    if p not in _img:
        _img[p]=np.array(pdf.pages[p-1].to_image(resolution=600).original.convert('L'))
    a=_img[p]; s=600/72
    sub=a[int(c['top']*s):int(c['bottom']*s)+1, int(c['x0']*s):int(c['x1']*s)+1]<128
    if c['text'] in '[]':
        cols=sub.sum(0); 
        if cols.max()<10: return None
        k=int(cols.argmax()); tall=cols>=0.8*cols.max()
        # contiguous stroke
        l=k
        while l>0 and tall[l-1]: l-=1
        r=k
        while r<len(cols)-1 and tall[r+1]: r+=1
        # serif: contiguous nonzero low columns adjacent to the stroke
        def run(i,step):
            n=0
            while 0<=i<len(cols) and 0<cols[i]<0.5*cols.max(): n+=1; i+=step
            return n
        left,right=run(l-1,-1),run(r+1,1)
        if right>left+1: return 'open'
        if left>right+1: return 'close'
        return None
    rows=np.where(sub.any(1))[0]
    if len(rows)<3: return None
    top=np.where(sub[rows[0]])[0].mean(); mid=np.where(sub[rows[len(rows)//2]])[0].mean(); bot=np.where(sub[rows[-1]])[0].mean()
    return 'open' if mid < (top+bot)/2 - 0.5 else ('close' if mid > (top+bot)/2 + 0.5 else None)
def bracket(c,rtl,notes):
    k=BR[c['text']]; sh=shape(c)
    if sh is None:
        notes.append(('bracket-shape-unknown',c['page_number'],c['text'])); return MIRROR.get(c['text'],c['text']) if rtl else c['text']
    if rtl: sh={'open':'close','close':'open'}[sh]
    if c['text'] in '<>': return '<' if sh=='open' else '>'
    return OPEN[k] if sh=='open' else CLOSE[k]
NORMW={'0':4.98,'1':3.22,'2':4.75,'3':4.66,'4':5.03,'5':4.73,'6':5.2,'7':4.73,'8':5.03,'9':5.1}
SUPW={'0':4.2,'1':2.69,'2':3.82,'3':3.84,'4':3.99,'5':3.76,'6':4.0,'7':3.59,'8':3.95,'9':4.0}
def is_sup(c):
    t=c['text']
    if not (len(t)==1 and t.isdigit()): return False
    if c['size']<9.5: return True
    w=(c['x1']-c['x0'])*11/c['size']
    return w < (NORMW[t]+SUPW[t])/2
def is_grey(c): 
    col=c.get('non_stroking_color')
    return isinstance(col,(tuple,list)) and len(col)==3 and abs(col[0]-0.53)<0.05
def numbers(pg,top,bottom,lo=290,hi=316):
    out=[]
    for w in pg.extract_words(x_tolerance=1.5,y_tolerance=2):
        if re.fullmatch(r"\d+[a-z]?[ʹ′'’]?",w['text']) and lo<=w['x0']<=hi and top<=w['top']<=bottom:
            chars=[c for c in pg.chars if abs(c['top']-w['top'])<1 and w['x0']-0.5<=c['x0']<=w['x1']]
            if chars and min(c['size'] for c in chars)>=9.5:
                # a real line number has original-script text immediately to its left on the same line
                left=[c for c in pg.chars if abs(c['bottom']-chars[0]['bottom'])<3 and w['x0']-40<c['x1']<w['x0']-0.5]
                gapl=[c for c in pg.chars if abs(c['bottom']-chars[0]['bottom'])<3 and w['x0']-2<c['x1']<w['x0']-0.2 and c['text'].strip()]
                if (any(RTL.match(c['text']) for c in left) or (left and all(c['text'] in '[]…x.() 0123456789' for c in left))) and not gapl or (not left and any(RTL.match(c['text']) for c in pg.chars if abs(c['top']-w['top'])<14 and c['x1']<w['x0'])):
                    out.append((w['top'],w['text'],w['x0'],w['x1']))
    return sorted(out)
def cluster(chars,tol=2.2):
    lines=[]
    for c in sorted(chars,key=lambda c:c['bottom']):
        for L in lines:
            if abs(L['b']-c['bottom'])<=tol: L['c'].append(c); break
        else: lines.append({'b':c['bottom'],'c':[c]})
    # merge weak lines (raised small letters) into nearest
    strong=[L for L in lines if sum(1 for c in L['c'] if c['text'].strip())>=3 and not all(c['size']<9.5 for c in L['c'] if c['text'].strip())]
    weak=[L for L in lines if L not in strong]
    for w in weak:
        if strong:
            n=min(strong,key=lambda L:abs(L['b']-w['b']))
            if abs(n['b']-w['b'])<=8: n['c'].extend(w['c']); continue
        strong.append(w)
    return sorted(strong,key=lambda L:L['b'])
GAP=[1.6]
SYR=re.compile(r'[\u0700-\u074f]')
def rtl_text(cs,notes,page):
    syr_line=any(SYR.match(c['text']) for c in cs)
    body=[c for c in cs if c['size']>=9.5]
    base=max((c['bottom'] for c in body),default=0)
    cs=sorted(cs,key=lambda c:-(c['x0']+c['x1'])/2)
    s=''; prev=None; raised=False
    for c in cs:
        t=c['text']
        small = c['size']<9.5
        if is_sup(c):   # footnote reference
            notes.append(('fnref',page,t)); continue
        if t==' ': continue
        if prev is not None and prev['x0']-c['x1']>GAP[0] and not s.endswith(' '): s+=' '
        if small and RTL.match(t) and not raised: s+='⸌'; raised=True
        if raised and not (small and RTL.match(t)): s+='⸍'; raised=False
        s+=bracket(c,True,notes) if t in BR else t
        s+=''.join(c.get('_marks',[]))
        if is_grey(c) and t.strip(): s+=DOTB
        prev=c
    if raised: s+='⸍'
    s=re.sub('['+LTRC+'](?:[̣]?[,./–\\-'+LTRC+']*['+LTRC+'][̣]?)?',lambda m:''.join(re.findall('.̣?',m.group(0))[::-1]),s)
    return s.strip()
def ltr_text(cs,notes,page):
    cs=sorted(cs,key=lambda c:c['x0'])
    s='';prev=None
    for c in cs:
        t=c['text']
        if is_sup(c): notes.append(('fnref',page,t)); prev=c; continue
        if t==' ':
            if s and not s.endswith(' '): s+=' '
            prev=None; continue
        if prev is not None and c['x0']-prev['x1']>1.5 and not s.endswith(' '): s+=' '
        s+=(bracket(c,False,notes) if t in BR else t)+''.join(c.get('_marks',[])); prev=c
    return s.strip()
def page_block(p,top,bottom,split=None):
    """returns list of (num, heb_lines, eng_lines) for sections on page p"""
    pg=pdf.pages[p-1]; notes=[]
    nums=numbers(pg,top,bottom)
    if split is None:
        split=(min(n[2] for n in nums) if nums else 300)
    nx0=min(n[2] for n in nums) if nums else split; nx1=max(n[3] for n in nums) if nums else split+8
    chars=[c for c in pg.chars if top<=c['top']<=bottom]
    heb=[c for c in chars if c['x1']<=nx0-1]
    eng=[c for c in chars if c['x0']>=nx1+1]
    hl=cluster(heb); el=cluster(eng)
    starts=[n[0] for n in nums]
    def assign(lines):
        sec={}
        for L in lines:
            top_=min(c['top'] for c in L['c'])
            k=None
            for i,s0 in enumerate(starts):
                if top_>=s0-4: k=i
            sec.setdefault(k,[]).append(L)
        return sec
    hs=assign(hl); es=assign(el)
    out=[]
    for k in sorted(set(hs)|set(es),key=lambda k:-1 if k is None else k):
        num=None if k is None else nums[k][1]
        out.append((num,[rtl_text(L['c'],notes,p) for L in hs.get(k,[])],[ltr_text(L['c'],notes,p) for L in es.get(k,[])]))
    return out,notes

import unicodedata
def is_mark(t): return len(t)==1 and unicodedata.category(t) in ('Mn','Me')
def attach_marks(cs):
    base=[c for c in cs if not is_mark(c['text'])]; marks=[c for c in cs if is_mark(c['text'])]
    for m in marks:
        mx=(m['x0']+m['x1'])/2
        my=(m['top']+m['bottom'])/2
        cand=[b for b in base if b['text'].strip() and b['top']-8<=my<=b['bottom']+8 and b['x0']-3<=mx<=b['x1']+3]
        if not cand:
            base.append(m); continue
        b=min(cand,key=lambda b: (0 if b['x0']-0.3<=mx<=b['x1']+0.3 else min(abs(mx-b['x0']),abs(mx-b['x1'])))*3 + abs(b['top']-m['top']-4.5))
        b.setdefault('_marks',[]).append(m['text'])
    return base
def block_bounds(p):
    pg=pdf.pages[p-1]
    nums=numbers(pg,45,pg.height-40)
    if not nums: return None
    top=nums[0][0]-4
    # include short heading lines (e.g. bowl section numerals) just above the first line number
    for w in pg.extract_words():
        if nums[0][0]-32 < w['top'] < nums[0][0]-6 and 200<w['x0']<400 and not RTL.search(w['text']):
            ws=[v for v in pg.extract_words() if abs(v['top']-w['top'])<2]
            if len(ws)<=6 and min(v['x0'] for v in ws)>150 and max(v['x1'] for v in ws)<460: top=min(top,w['top']-2)
    stops=[pg.height-45]
    for o in pg.lines:
        if 40<(o['x1']-o['x0'])<50 and o['top']>top: stops.append(o['top']-2)
    for w in pg.extract_words(extra_attrs=['size']):
        if w['top']>top+5 and ((w['text'] in ('Notes','Previous') and (w['x0']<80 or 300<w['x0']<330)) or (w['size']>12 and re.fullmatch(r'\d+\.',w['text']))): stops.append(w['top']-3)
    return top,min(stops)

def entry_rows(pages, hyphen_vocab=None):
    heb_out=[]; eng_out=[]; notes=[]
    for p in pages:
        pg=pdf.pages[p-1]
        b=block_bounds(p)
        if not b: notes.append(('no-block',p)); continue
        top,bottom=b
        nums=numbers(pg,top,bottom)
        nx0=min(n[2] for n in nums); nx1=max(n[3] for n in nums)
        chars=[c for c in pg.chars if top<=c['top']<=bottom and c['text']!='']
        chars=attach_marks(chars)
        # heading detection: clusters (full width) with no RTL char and no number, containing Latin letters and crossing nx0
        allL=cluster(chars)
        headings=[]; skip=set()
        for L in allL:
            cs=[c for c in L['c'] if c['text'].strip()]
            if not cs: continue
            hasR=any(RTL.match(c['text']) for c in cs)
            hasnum=any(abs(n[0]-min(c['top'] for c in cs))<3 for n in nums)
            xs0=min(c['x0'] for c in cs); xs1=max(c['x1'] for c in cs)
            spans=any(c['x0']<nx1 and c['x1']>nx0 for c in cs)
            roman=re.fullmatch(r'[IVX]+',''.join(c['text'] for c in cs).strip()) is not None
            italic_left=all(c['x1']<=nx0 for c in cs) and any('Italic' in c['fontname'] for c in cs)
            if not hasR and not hasnum and (spans or roman or italic_left) and any(c['text'].isalpha() for c in cs):
                headings.append((min(c['top'] for c in cs),ltr_text(L['c'],notes,p)))
                for c in L['c']: skip.add(id(c))
        chars=[c for c in chars if id(c) not in skip]
        heb=[c for c in chars if c['x1']<=nx0-1]; eng=[c for c in chars if c['x0']>=nx1+1]
        starts=[n[0] for n in nums]
        def assign(lines):
            sec={}
            for L in lines:
                t0=min(c['top'] for c in L['c'])
                k=None
                for i,s0 in enumerate(starts):
                    if t0>=s0-4: k=i
                sec.setdefault(k,[]).append(L)
            return sec
        hs=assign(cluster(heb)); es=assign(cluster(eng))
        header=f'[PDF page {p}; printed p. {p-24}]'
        heb_out.append(header); eng_out.append(header)
        items=[(n[0],'sec',i) for i,n in enumerate(nums)]+[(h[0],'head',h[1]) for h in headings]
        if None in hs or None in es: notes.append(('unnumbered-lines',p,[rtl_text(L['c'],notes,p) for L in hs.get(None,[])],[ltr_text(L['c'],notes,p) for L in es.get(None,[])]))
        for y,kind,v in sorted(items):
            if kind=='head':
                heb_out.append(v); eng_out.append(v); continue
            num=nums[v][1]
            hl=[rtl_text(L['c'],notes,p) for L in hs.get(v,[])]
            el=[ltr_text(L['c'],notes,p) for L in es.get(v,[])]
            if hl: heb_out.append(num+'. '+' '.join(hl))
            if el:
                s=el[0]
                for nxt in el[1:]:
                    if re.search(r'[a-zA-Zāēīūḥṭṣšʾʿ]-$',s) and nxt[:1].islower():
                        w=re.search(r'(\S+)-$',s).group(1)+re.match(r'(\S+)',nxt).group(1)
                        w=re.sub(r'[^\w]','',w)
                        if hyphen_vocab is not None and w.lower() in hyphen_vocab: s=s[:-1]+nxt
                        else: s=s+nxt; notes.append(('kept-hyphen',p,w))
                    else: s=(s+" "+nxt)
                s=re.sub(" {2,}"," ",s)
                eng_out.append(num+'. '+s)
    # restore raised-letter marks and combining marks were handled in text fns
    return '\n'.join(heb_out),'\n'.join(eng_out),notes


def stage(rows, extra_pages=None):
    import collections
    voc=set()
    for pg in pdf.pages:
        voc.update(w.lower() for w in re.findall(r"[A-Za-zāēīūḥṭṣšʾʿ]+", pg.extract_text() or ''))
    ed=[r for r in rows if r['text_type'] in('translation','transcription')]
    ent={}
    for r in ed:
        m=re.search(r'Entry (\d+)',r['locator']); n=int(m.group(1))
        pm=re.search(r'PDF pp\. (\d+)–(\d+)',r['locator'])
        if pm: pages=list(range(int(pm.group(1)),int(pm.group(2))+1))
        else:
            pp=re.search(r'printed pp?\. (\d+)(?:–(\d+))?',r['locator'])
            a=int(pp.group(1)); b=int(pp.group(2) or a); pages=list(range(a+24,b+25))
        ent.setdefault(n,{'pages':pages,'rows':{}})['rows'][r['text_type']]=r['id']
    for k,v in (extra_pages or {}).items(): ent[k]['pages']=v
    out={}
    for n in sorted(ent):
        h,e,notes=entry_rows(ent[n]['pages'],voc)
        out[n]={'pages':ent[n]['pages'],'rows':ent[n]['rows'],'heb':h,'eng':e,'notes':[x for x in notes if x[0]!='fnref'],'fn':len([x for x in notes if x[0]=='fnref'])}
        print(n,ent[n]['pages'],list(ent[n]['rows']),out[n]['notes'][:5])
    return out


if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('output')
    a=ap.parse_args()
    if not a.output.startswith('data/private/'): raise ValueError('protected output must stay in data/private/')
    if hashlib.sha256(PDF.read_bytes()).hexdigest()!=SHA256: raise ValueError('Jena capture hash mismatch')
    # pages the working locators omit (printed continuation pages confirmed on rendered pages)
    out=stage(json.load(open(a.rows)), {25:[155,156],28:[166,167],40:[228,229]})
    json.dump(out,open(a.output,'w'),ensure_ascii=False,indent=1)
