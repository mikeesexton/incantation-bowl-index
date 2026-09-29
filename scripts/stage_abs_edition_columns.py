"""Stage Shaked, Ford and Bhayro, Aramaic Bowl Spells vols. 1-2, edition columns from PDF glyph positions.

Staging aid for proofreading, not a review. Output is protected source text and
must be written only under data/private/. It reads the facing Hebrew-script and
English columns of each JBA entry, orders Hebrew glyphs right to left (bracket
orientation read from the rendered glyph), joins each printed line number's
wraps, attaches continuation lines at the head of a following page, keeps printed
headings ("Outside:", "Inside the drawing:" ...) and embedded Latin labels such as
"(magic characters)", marks small/raised type with U+2E0C/U+2E0D, printed
strikeout with U+0336, printed underline with U+0332 and printed boxes with
U+27E6/U+27E7, restores English small capitals (YHWH, YYYY ...) as capitals,
drops footnote reference numerals and stops at footnote rules and
"Notes"/"Previous readings" headings. Line numbers are accepted only at the
page's median column x. Every staged row must still be compared with rendered
pages before a proofreading manifest may claim reading_text_checked.

Usage:
  PYTHONPATH=src python3 scripts/stage_abs_edition_columns.py ROWS.json SOURCE_ID OUT.json
where ROWS.json is a private list of the source's text rows (id, source_id,
text_type, locator "JBA n, printed pp. a-b").
"""
import pdfplumber,re,sys,json
CFG={'pdf':None,'offset':0,'heb':9.1,'lat':10.0,'lo':240,'hi':370,'mark':'\u05af','gap':1.2}
pdf=None
def setup(path,offset,heb,lat,mark):
    global pdf
    pdf=pdfplumber.open(path); CFG.update(offset=offset,heb=heb,lat=lat,mark=mark); _img.clear()
    import collections
    W=collections.defaultdict(collections.Counter); K=collections.defaultdict(collections.Counter)
    for pg in pdf.pages[40:min(len(pdf.pages),200)]:
        for c in pg.chars:
            if c['text'].isascii() and c['text'].isalpha() and c['text'].islower() and 'Roman' in c['fontname'] and c['size']>0:
                W[c['text']][round((c['x1']-c['x0'])/c['size'],4)]+=1
            if c['text'].strip() and c['size']>0 and not RTL.match(c['text']):
                K[(c['text'],fontkind(c))][round((c['x1']-c['x0'])/c['size'],4)]+=1
    NORM.clear(); NORM.update({k:v.most_common(1)[0][0] for k,v in K.items() if sum(v.values())>=5})
    MODE.clear(); MODE.update({k:v.most_common(1)[0][0] for k,v in W.items()})
GREY=(0.53,0.535,0.545)
DOTB='̣'; STRIKE='̶'
MIRROR={"(":")",")":"(","[":"]","]":"[","{":"}","}":"{","⟨":"⟩","⟩":"⟨","<":">",">":"<"}
LTRC='0-9A-Za-zÀ-ɏḀ-ỿʾʿ'
RTL=re.compile(r'[֐-׿܀-ݏ]')
import numpy as np
_img={}
MODE={}
NORM={}
def fontkind(c):
    f=c['fontname']
    return ('B' if 'Bold' in f else '')+('I' if 'Italic' in f else '')
def width_ratio(c):
    n=NORM.get((c['text'],fontkind(c)))
    return (c['x1']-c['x0'])/c['size']/n if n and c['size'] else None
BR={'(':'p',')':'p','[':'s',']':'s','{':'c','}':'c','⟨':'a','⟩':'a','<':'a','>':'a'}
OPEN={'p':'(','s':'[','c':'{','a':'⟨'}; CLOSE={'p':')','s':']','c':'}','a':'⟩'}
def shape(c):
    p=c['page_number']
    if p not in _img:
        _img.clear()
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
    return c['size']<0.85*CFG['lat']
def is_grey(c): 
    col=c.get('non_stroking_color')
    return isinstance(col,(tuple,list)) and len(col) in (1,3) and 0.3<col[0]<0.7
def numbers(pg,top,bottom,lo=None,hi=None):
    """Printed line numbers of an edition block: a number sitting between the
    original-script column and the translation, with text on both sides.  All
    line numbers on a page share one x position, so stray numbers are dropped."""
    lo=CFG['lo'] if lo is None else lo; hi=CFG['hi'] if hi is None else hi
    cand=[]
    for w in pg.extract_words(x_tolerance=1.5,y_tolerance=2,extra_attrs=['fontname']):
        if not (re.fullmatch(r"\d+[a-z]?[ʹ′'’]?",w['text']) and lo<=w['x0']<=hi and top<=w['top']<=bottom): continue
        if 'Italic' in w['fontname']: continue
        chars=[c for c in pg.chars if abs(c['top']-w['top'])<1 and w['x0']-0.5<=c['x0']<=w['x1']]
        if not chars or min(c['size'] for c in chars)<0.95*CFG['lat']: continue
        b=chars[0]['bottom']
        same=[c for c in pg.chars if abs(c['bottom']-b)<3 and c['text'].strip()]
        left=[c for c in same if w['x0']-70<c['x1']<w['x0']-3]
        touch=[c for c in same if w['x0']-3<=c['x1']<w['x0']-0.2]
        right=[c for c in same if w['x1']+3<c['x0']<w['x1']+30]
        if touch: continue
        rtl_line=any(RTL.match(c['text']) for c in same if c['x1']<w['x0'])
        lac=bool(left) and (all(c['text'] in '[]…x.() -–—' for c in left) or (bool(right) and any('Italic' in c['fontname'] for c in left)))
        near_rtl=not left and any(RTL.match(c['text']) for c in pg.chars if abs(c['top']-w['top'])<14 and c['x1']<w['x0'])
        if (rtl_line or lac or near_rtl) and (right or not left):
            cand.append((w['top'],w['text'],w['x0'],w['x1']))
    if not cand: return []
    xs=sorted(c[2] for c in cand); med=xs[len(xs)//2]
    return sorted(c for c in cand if abs(c[2]-med)<=5)
def cluster(chars,tol=2.2):
    lines=[]
    for c in sorted(chars,key=lambda c:c['bottom']):
        for L in lines:
            if abs(L['b']-c['bottom'])<=tol: L['c'].append(c); break
        else: lines.append({'b':c['bottom'],'c':[c]})
    # merge weak lines (raised small letters) into nearest
    strong=[L for L in lines if sum(1 for c in L['c'] if c['text'].strip())>=3 and not all(c['size']<0.8*min(CFG['heb'],CFG['lat']) for c in L['c'] if c['text'].strip())]
    weak=[L for L in lines if L not in strong]
    for w in weak:
        if strong:
            n=min(strong,key=lambda L:abs(L['b']-w['b']))
            if abs(n['b']-w['b'])<=8: n['c'].extend(w['c']); continue
        strong.append(w)
    return sorted(strong,key=lambda L:L['b'])
GAP=[1.2]
SYR=re.compile(r'[\u0700-\u074f]')
_strike={}
def struck(pg):
    """ids of glyphs crossed by a thin horizontal rule near their mid-height (printed strikeout)."""
    if pg.page_number in _strike: return _strike[pg.page_number]
    rules=[r for r in pg.lines+pg.rects if (r['bottom']-r['top'])<1.5 and (r['x1']-r['x0'])>1.5]
    out=set()
    for c in pg.chars:
        if not c['text'].strip(): continue
        cx=(c['x0']+c['x1'])/2; h=c['bottom']-c['top']
        for r in rules:
            y=(r['top']+r['bottom'])/2
            if r['x0']-0.3<=cx<=r['x1']+0.3 and c['top']+0.35*h<=y<=c['bottom']-0.2*h: out.add((round(c['x0'],2),round(c['top'],2),c['text'])); break
    _strike.clear(); _strike[pg.page_number]=out
    return out
_frame={}
def framed(pg):
    if pg.page_number in _frame: return _frame[pg.page_number]
    hs=[r for r in pg.lines+pg.rects if (r['bottom']-r['top'])<1.5 and (r['x1']-r['x0'])>1.5 and not (40<(r['x1']-r['x0'])<50 and r['x0']<115)]
    vs=[r for r in pg.lines+pg.rects if (r['x1']-r['x0'])<1.5 and (r['bottom']-r['top'])>3]
    def boxtop(r):
        return any(abs(v['top']-r['top'])<1.2 and (abs(v['x0']-r['x0'])<1.2 or abs(v['x0']-r['x1'])<1.2) for v in vs)
    out={}
    if hs:
        for c in pg.chars:
            if not c['text'].strip() or not RTL.match(c['text']): continue
            cx=(c['x0']+c['x1'])/2
            above=any(r['x0']-0.5<=cx<=r['x1']+0.5 and c['top']-7<=r['top']<=c['top']+1.5 for r in hs)
            below=any(r['x0']-0.5<=cx<=r['x1']+0.5 and c['bottom']-1.5<=r['top']<=c['bottom']+(7 if above else 4) and (above or not boxtop(r)) for r in hs)
            k=(round(c['x0'],2),round(c['top'],2),c['text'])
            if above and below: out[k]='box'
            elif below: out[k]='under'
    _frame.clear(); _frame[pg.page_number]=out
    return out
def _is_framed(c):
    return framed(pdf.pages[c['page_number']-1]).get((round(c['x0'],2),round(c['top'],2),c['text']))=='box'
def _is_under(c):
    return framed(pdf.pages[c['page_number']-1]).get((round(c['x0'],2),round(c['top'],2),c['text']))=='under'
def _is_struck(c):
    return (round(c['x0'],2),round(c['top'],2),c['text']) in struck(pdf.pages[c['page_number']-1])
LATIN=re.compile(r'[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u02BE\u02BF]')
def _piece(c,rtl,notes):
    t=c['text']
    p=bracket(c,rtl,notes) if t in BR else t
    p+=''.join(c.get('_marks',[]))
    if is_grey(c) and t.strip(): p+=CFG['mark']
    if _is_struck(c): p+='\u0336'
    elif RTL.match(t) and _is_under(c): p+='\u0332'
    return p
def rtl_text(cs,notes,page):
    cs=sorted(cs,key=lambda c:-(c['x0']+c['x1'])/2)
    units=[]; prev=None; raised=False; inframe=False
    for c in cs:
        t=c['text']
        if t==' ': continue
        small = c['size']<0.8*CFG['heb']
        if is_sup(c) and not raised and not any(RTL.match(x['text']) and x['size']<0.8*CFG['heb'] for x in cs if abs(x['x0']-c['x1'])<3 or abs(c['x0']-x['x1'])<3):
            notes.append(('fnref',page,t)); continue
        if prev is not None and prev['x0']-c['x1']>GAP[0] and not (units and units[-1]['t']==' '): units.append({'t':' ','c':None})
        if small and not raised:
            units.append({'t':'⸌','c':None}); raised=True
        elif raised and not small:
            if units and units[-1]['t']==' ': units.insert(len(units)-1,{'t':'⸍','c':None})
            else: units.append({'t':'⸍','c':None})
            raised=False
        fr=_is_framed(c) if RTL.match(c['text']) else inframe
        if fr and not inframe:
            if units and units[-1]['t']==' ': units.insert(len(units)-1,{'t':'⟦','c':None}) if False else units.append({'t':'⟦','c':None})
            else: units.append({'t':'⟦','c':None})
            inframe=True
        elif not fr and inframe and c['text'] not in BR and not c['text'] in '|':
            if units and units[-1]['t']==' ': units.insert(len(units)-1,{'t':'⟧','c':None})
            else: units.append({'t':'⟧','c':None})
            inframe=False
        units.append({'t':None,'c':c}); prev=c
    if inframe: units.append({'t':'⟧','c':None})
    if raised: units.append({'t':'⸍','c':None})
    # left-to-right spans (Latin words, digits and the spaces/punctuation between or around them)
    isl=[u['c'] is not None and bool(LATIN.match(u['c']['text'])) for u in units]
    n=len(units); inspan=[False]*n; i=0
    while i<n:
        if isl[i]:
            j=i
            while True:
                k=j+1
                while k<n and not isl[k] and (units[k]['c'] is None and units[k]['t']==' ' or (units[k]['c'] is not None and not RTL.match(units[k]['c']['text']) and not LATIN.match(units[k]['c']['text']))): k+=1
                if k<n and isl[k]: j=k
                else: break
            a,b=i,j
            # absorb adjacent brackets/punctuation (not spaces) on both edges
            while a-1>=0 and units[a-1]['c'] is not None and not RTL.match(units[a-1]['c']['text']) and not LATIN.match(units[a-1]['c']['text']): a-=1
            while b+1<n and units[b+1]['c'] is not None and not RTL.match(units[b+1]['c']['text']) and not LATIN.match(units[b+1]['c']['text']): b+=1
            for x in range(a,b+1): inspan[x]=True
            i=b+1
        else: i+=1
    out=''; i=0
    while i<n:
        if inspan[i]:
            j=i
            while j+1<n and inspan[j+1]: j+=1
            seg=units[i:j+1][::-1]
            out+=''.join(u['t'] if u['c'] is None else _piece(u['c'],False,notes) for u in seg)
            i=j+1
        else:
            u=units[i]; out+=u['t'] if u['c'] is None else _piece(u['c'],True,notes); i+=1
    return re.sub(' {2,}',' ',out).strip()
def ltr_text(cs,notes,page):
    cs=sorted(cs,key=lambda c:c['x0'])
    s='';prev=None;fl=[];cw=[];cz=[];raisedl=False
    # small type: glyphs set well below body size (by size, or by advance width for scaled glyphs)
    base=[]
    for c in cs:
        if not c['text'].strip(): base.append(None); continue
        r=width_ratio(c) if c['text'].isalpha() else None
        base.append(c['size']<0.85*CFG['lat'] or (r is not None and r<0.85) if (c['text'].isalpha() or c['size']<0.85*CFG['lat']) else None)
    smallf={}
    for i,c in enumerate(cs):
        v=base[i]
        if v is None:
            l=next((base[j] for j in range(i-1,-1,-1) if base[j] is not None),False)
            r=next((base[j] for j in range(i+1,len(cs)) if base[j] is not None),False)
            v=l and r
        smallf[id(c)]=v
    for c in cs:
        t=c['text']
        if is_sup(c): notes.append(('fnref',page,t)); prev=c; continue
        if t==' ':
            if s and not s.endswith(' '): s+=' '; fl.append('R'); cw.append(0); cz.append(0)
            prev=None; continue
        if prev is not None and c['x0']-prev['x1']>1.5 and not s.endswith(' '): s+=' '; fl.append('R'); cw.append(0); cz.append(0)
        piece=(bracket(c,False,notes) if t in BR else t)+''.join(c.get('_marks',[]))+('\u0336' if _is_struck(c) else '')
        small=smallf.get(id(c),False)
        if small and not raisedl: s+='⸌'; fl.append('R'); cw.append(0); cz.append(0); raisedl=True
        if not small and raisedl:
            if s.endswith(' '): s=s[:-1]+'⸍ '
            else: s+='⸍'
            fl.append('R'); cw.append(0); cz.append(0); raisedl=False
        s+=piece; fl.extend(['B' if 'Bold' in c['fontname'] else 'R']*len(piece))
        cw.extend([round(c['x1']-c['x0'],2)]+[0]*(len(piece)-1)); cz.extend([c['size'] if 'Roman' in c['fontname'] else 0]*len(piece)); prev=c
    if raisedl: s+='⸍'; fl.append('R'); cw.append(0); cz.append(0)
    # small capitals are stored as lowercase glyphs of a different width; restore them as capitals
    sc=[False]*len(s)
    for m in re.finditer(r"[a-zʾʿ\u0300-\u036f\[\]⟨⟩]+",s):
        letters=[i for i in range(m.start(),m.end()) if s[i].isalpha() and s[i].isascii()]
        if not letters: continue
        rat=[(cw[i]/cz[i])/MODE[s[i]] if cw[i] and cz[i] and s[i] in MODE else None for i in letters]
        if all(r is not None and abs(r-1)>0.004 and 0.8<r<1.3 for r in rat) and not any(fl[i]=='B' for i in letters):
            s=s[:m.start()]+s[m.start():m.end()].upper()+s[m.end():]
    # the divine name is set in small capitals, which the text layer stores as lowercase
    for m in reversed(list(re.finditer(r'(?<![A-Za-z])y[\[\]]?h[\[\]]?w[\[\]]?h(?![A-Za-z])',s))):
        if 'B' not in fl[m.start():m.end()]: s=s[:m.start()]+m.group(0).upper()+s[m.end():]
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
def block_bounds(p,cont=False):
    pg=pdf.pages[p-1]
    nums=numbers(pg,45,pg.height-40)
    if not nums: return None
    top=nums[0][0]-4
    if cont:
        tops=[c['top'] for c in pg.chars if c['text'].strip()]
        t0=min(tops) if tops else 40
        hl=[c for c in pg.chars if c['text'].strip() and c['top']<t0+3]
        head=[c['bottom'] for c in hl] if t0<80 and any(c['text'].isdigit() for c in hl) and not any(RTL.match(c['text']) for c in hl) else []
        top=min(top,(max(head) if head else t0-2)+2)
    # include short heading lines (e.g. bowl section numerals) just above the first line number
    for w in pg.extract_words():
        if nums[0][0]-32 < w['top'] < nums[0][0]-6 and 200<w['x0']<400 and not RTL.search(w['text']):
            ws=[v for v in pg.extract_words() if abs(v['top']-w['top'])<2]
            if len(ws)<=6 and min(v['x0'] for v in ws)>150 and max(v['x1'] for v in ws)<460 and not ws[0]['text'].startswith(('Fig','FIG','Figure')): top=min(top,w['top']-2)
    stops=[pg.height-45]
    for o in pg.lines:
        if 40<(o['x1']-o['x0'])<50 and o['x0']<115 and abs(o['bottom']-o['top'])<1 and o['top']>top: stops.append(o['top']-2)
    for w in pg.extract_words(extra_attrs=['size','fontname']):
        if w['top']>top+5 and ((w['text'] in ('Notes','Previous') and (w['x0']<80 or 300<w['x0']<330)) or w['size']>12.5 or ('Italic' in w['fontname'] and w['x0']<100 and re.match(r'\d',w['text']))): stops.append(w['top']-3)
    return top,min(stops)

def entry_rows(pages, hyphen_vocab=None):
    heb_out=[]; eng_out=[]; notes=[]
    for p in pages:
        pg=pdf.pages[p-1]
        b=block_bounds(p,cont=(p!=pages[0]))
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
        header=f"[PDF page {p}; printed p. {p-CFG['offset']}]"
        heb_out.append(header); eng_out.append(header)
        items=[(n[0],'sec',i) for i,n in enumerate(nums)]+[(h[0],'head',h[1]) for h in headings]
        def join_eng(s,more):
            for nxt in more:
                if re.search(r'(?:[^\W\d_]|[ʾʿ])[\u0300-\u036f]*-$',s) and nxt[:1].islower():
                    w=re.search(r'(\S+)-$',s).group(1)+re.match(r'(\S+)',nxt).group(1)
                    w=re.sub(r'[^\w]','',w)
                    if hyphen_vocab is not None and w.lower() in hyphen_vocab: s=s[:-1]+nxt
                    else: s=s+nxt; notes.append(('kept-hyphen',p,w))
                else: s=(s+" "+nxt)
            return re.sub(r'⸍([,;.:]?) ⸌',r'\1 ',re.sub(" {2,}"," ",s))
        def last_num(out):
            for i in range(len(out)-1,-1,-1):
                if re.match(r"^\d+[a-z]?[ʹ′'’]?\. ",out[i]): return i
            return None
        if None in hs or None in es:
            hl0=[rtl_text(L['c'],notes,p) for L in hs.get(None,[])]
            el0=[ltr_text(L['c'],notes,p) for L in es.get(None,[])]
            ih,ie=last_num(heb_out),last_num(eng_out)
            if hl0 and ih is not None:
                heb_out[ih]=re.sub(r'⟧ ⟦',' ',re.sub(r'⸍([,;.:]?) ⸌',r'\1 ',heb_out[ih]+' '+' '.join(hl0))); notes.append(('continued-line',p,'heb'))
            elif hl0: notes.append(('unnumbered-lines',p,hl0,[]))
            if el0 and ie is not None:
                eng_out[ie]=join_eng(eng_out[ie],el0); notes.append(('continued-line',p,'eng'))
            elif el0: notes.append(('unnumbered-lines',p,[],el0))
        for y,kind,v in sorted(items):
            if kind=='head':
                heb_out.append(v); eng_out.append(v); continue
            num=nums[v][1]
            hl=[rtl_text(L['c'],notes,p) for L in hs.get(v,[])]
            el=[ltr_text(L['c'],notes,p) for L in es.get(v,[])]
            if hl: heb_out.append(num+'. '+re.sub(r'⟧ ⟦',' ',re.sub(r'⸍([,;.:]?) ⸌',r'\1 ',' '.join(hl))))
            if el:
                s=el[0]
                for nxt in el[1:]:
                    if re.search(r'(?:[^\W\d_]|[ʾʿ])[\u0300-\u036f]*-$',s) and nxt[:1].islower():
                        w=re.search(r'(\S+)-$',s).group(1)+re.match(r'(\S+)',nxt).group(1)
                        w=re.sub(r'[^\w]','',w)
                        if hyphen_vocab is not None and w.lower() in hyphen_vocab: s=s[:-1]+nxt
                        else: s=s+nxt; notes.append(('kept-hyphen',p,w))
                    else: s=(s+" "+nxt)
                s=re.sub(" {2,}"," ",s)
                eng_out.append(num+'. '+re.sub(r'⸍([,;.:]?) ⸌',r'\1 ',s))
    # restore raised-letter marks and combining marks were handled in text fns
    return '\n'.join(heb_out),'\n'.join(eng_out),notes


VOLUMES = {
    # source_id: (capture sha256, PDF page minus printed page, Hebrew body size, Latin body size)
    'SRC-7FBBB775E502': ('39a8763373010f4703576f8917df901f4e170153c5014f5b344e60bb4775af9c', 28, 9.1, 10.0),
    'SRC-8C611BF93288': ('e15f96f25da902065ea972aacb441034f99ca08fbdcdff73be5b11cc80fc3b00', 20, 10.3, 11.0),
}


def _heading(p):
    pg = pdf.pages[p - 1]
    return ' '.join(w['text'] for w in pg.extract_words(x_tolerance=1.5) if w['top'] < 130)


def stage(rows, source_id, root='.'):
    from pathlib import Path
    sha, off, heb, lat = VOLUMES[source_id]
    setup(str(Path(root) / 'data/private/archive/sha256' / sha[:2] / sha), off, heb, lat, '\u05af')
    voc = set()
    for pg in pdf.pages:
        voc.update(w.lower() for w in re.findall(r"[A-Za-zāēīūḥṭṣšʾʿ]+", pg.extract_text(x_tolerance=1.5) or ''))
    ent = {}
    for r in rows:
        if r['source_id'] != source_id:
            continue
        m = re.match(r'JBA (\d+), printed pp?\. (\d+)(?:–(\d+))?', r['locator'])
        n, a = int(m.group(1)), int(m.group(2)); b = int(m.group(3) or a)
        ent.setdefault(n, {'pages': list(range(a + off, b + off + 1)), 'rows': {}})['rows'][r['text_type']] = r['id']
    out = {}
    for n in sorted(ent):
        pages = ent[n]['pages']
        q = pages[-1] + 1
        while q <= len(pdf.pages):
            pg = pdf.pages[q - 1]
            if re.search(r'(?i)jba\s*\d+\s*\(', _heading(q)) or not numbers(pg, 45, pg.height - 40):
                break
            pages.append(q); q += 1
        h, e, notes = entry_rows(pages, voc)
        heb_text = h.replace('<', '⟨').replace('>', '⟩')
        out[n] = {'pages': pages, 'rows': ent[n]['rows'], 'heb': heb_text, 'eng': e,
                  'notes': [x for x in notes if x[0] != 'fnref']}
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('rows'); ap.add_argument('source_id'); ap.add_argument('output')
    a = ap.parse_args()
    if not str(a.output).startswith('data/private/'):
        sys.exit('Staged edition text is protected; write it under data/private/.')
    json.dump(stage(json.load(open(a.rows)), a.source_id), open(a.output, 'w'), ensure_ascii=False, indent=1)
