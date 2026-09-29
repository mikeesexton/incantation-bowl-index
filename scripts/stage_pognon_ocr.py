"""Stage Pognon 1898 (Khouabir) French translations from page OCR. Staging aid only: its output is a
draft that must be checked line by line against the page images before any review is recorded.

OCR (run in a scratch directory holding the PDF as pog.pdf):
    pdftoppm -f P -l P -r 300 -gray -png pog.pdf hi        # -> hi-PPP.png
    tesseract hi-PPP.png hi-PPP -l fra --psm 4             # -> hi-PPP.txt (vocabulary for dehyphenation)
    tesseract hi-PPP.png hi-PPP -l fra --psm 4 tsv         # -> hi-PPP.tsv (line boxes)

Specs and verified corrections contain protected text and live only under data/private/:
    python3 scripts/stage_pognon_ocr.py SCRATCH_DIR data/private/proofreading/pognon_claude_2026-09-29/specs.py N...
A spec is a list of items: ('h', heading) | ('x', page, line) exterior legend, «…» part only |
(page, first, last) TSV line range. specs.FIX[n] is a list of (ocr_text, corrected_text) pairs, each of which
must occur in the draft. The PDF page is the printed page + 11.
"""
import csv, os, re, sys, importlib.util
from PIL import Image
def tsv_lines(p):
    rows=list(csv.DictReader(open(f'hi-{p:03d}.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE))
    L={}
    for r in rows:
        if r['level']!='5' or not r['text'].strip(): continue
        k=(int(r['block_num']),int(r['par_num']),int(r['line_num']))
        d=L.setdefault(k,{'w':[],'x0':1e9,'y0':1e9,'x1':0,'y1':0})
        x,y,w,h=int(r['left']),int(r['top']),int(r['width']),int(r['height'])
        d['w'].append(r['text']); d['x0']=min(d['x0'],x); d['y0']=min(d['y0'],y); d['x1']=max(d['x1'],x+w); d['y1']=max(d['y1'],y+h)
    out=sorted(L.values(),key=lambda d:(d['y0'],d['x0']))
    for d in out: d['t']=' '.join(d['w'])
    return out
OFF=11
VOC=None
def vocab():
    global VOC
    if VOC is None:
        VOC=set()
        for f in os.listdir('.'):
            if f.endswith('.txt') and f.startswith('hi-'):
                VOC.update(w.lower() for w in re.findall(r"[A-Za-zÀ-ÿœŒ]+", open(f).read()))
    return VOC
def clean(t):
    t=t.replace("'",'’').replace('`','’')
    t=re.sub(r'\s*\(\s*[0-9lI]\s*[)}]\s*|\s*[0-9]\)\s*(?=[,.;: ])|\s*®\s*',' ',t)
    return t
def join(lines):
    s=''
    for l in lines:
        l=clean(l).strip()
        if not s: s=l; continue
        if re.search(r'[A-Za-zÀ-ÿœ]-$',s):
            w1=re.search(r'([A-Za-zÀ-ÿœ]+)-$',s).group(1); w2=re.match(r'([A-Za-zÀ-ÿœ]+)',l)
            if w2 and (w1+w2.group(1)).lower() in vocab() and not w2.group(1)[0].isupper() and w2.group(1).lower() not in ('les','le','la','lui','elle','elles','moi','toi','nous','vous','eux','y','en'):
                s=s[:-1]+l
            else: s=s+l
        else: s=s+' '+l
    s=re.sub(r'\s+([,.;:!?)»])',r'\1',s); s=re.sub(r'([(«])\s+',r'\1',s)
    s=re.sub(r'\s*(?:\.\s?){3,}\s*|\s*…\s*',' … ',s); s=re.sub(r' … ([,;:!?])',r' …\1',s); s=re.sub(r' +',' ',s)
    return s.strip()
def build(spec):
    """spec: list of items: ('h', text) heading | (page, a, b) line range inclusive (TSV indices)"""
    out=[]; imgs=[]; cur=[]; lastp=None; heads=[]; carry=''
    def flush():
        nonlocal cur
        if cur: out.append(join(cur)); cur=[]
    for it in spec:
        if it[0]=='h': flush(); heads.append(it[1]); continue
        if it[0]=='para': flush(); continue
        if it[0]=='x':
            # exterior legend: take only the quoted French translation «…» from that line
            _,p,a=it; L=tsv_lines(p); d=L[a]
            m=re.search(r'«[^»]*»',d['t']); q=m.group(0) if m else d['t']
            if p!=lastp: flush(); out.append(f'[PDF page {p}; printed p. {p-OFF}]'); lastp=p
            if heads: flush(); out.extend(heads); heads=[]
            flush(); out.append(clean(re.sub(r'«\s*','«',re.sub(r'\s*»','»',q))).strip())
            im=Image.open(f'hi-{p:03d}.png'); imgs.append(im.crop((d['x0']-10,d['y0']-8,d['x1']+10,d['y1']+8)))
            continue
        p,a,b=it
        L=tsv_lines(p)
        if p!=lastp:
            if cur and re.search(r'[A-Za-zÀ-ÿœ]-\s*$',cur[-1]) and not heads:
                nxt=L[a]['t']; m=re.match(r'(\S+)\s*(.*)$',nxt)
                cur[-1]=cur[-1].rstrip()
                w1=re.search(r'([A-Za-zÀ-ÿœ]+)-$',cur[-1]).group(1)
                if (w1+m.group(1)).lower().strip('.,;:!?') in vocab() or m.group(1)[:1].islower():
                    cur[-1]=cur[-1][:-1]+m.group(1); L=list(L); L[a]=dict(L[a],t=m.group(2))
            flush(); out.append(f'[PDF page {p}; printed p. {p-OFF}]'); lastp=p
        if heads: flush(); out.extend(heads); heads=[]
        seg=L[a:b+1]; texts=[d['t'] for d in seg]
        if carry: texts[0]=carry+texts[0]; carry=''
        cur+= texts
        im=Image.open(f'hi-{p:03d}.png'); y0=min(d['y0'] for d in seg)-8; y1=max(d['y1'] for d in seg)+8
        x0=min(d['x0'] for d in seg)-10; x1=max(d['x1'] for d in seg)+10
        imgs.append(im.crop((x0,y0,x1,y1)))
    flush()
    txt=re.sub(r'\n+','\n','\n'.join(out))
    txt=re.sub(r'(?m)^\.?\s*Tradu[a-z]+\s*[.,]?\s*[—–-]+\s*','',txt)
    return txt, imgs
def sheet(imgs,fn,scale=0.5):
    ims=[i.resize((int(i.width*scale),int(i.height*scale))) for i in imgs]
    W=max(i.width for i in ims); H=sum(i.height+8 for i in ims)
    m=Image.new('L',(W,H),255); y=0
    for i in ims: m.paste(i,(0,y)); y+=i.height+8
    m.save(fn)


def draft(n, specs):
    txt, imgs = build(specs.S[n])
    for k, v in specs.FIX.get(n, []):
        assert k in txt, (n, k); txt = txt.replace(k, v)
    return txt, imgs

if __name__ == '__main__':
    wd, spec_path = sys.argv[1], os.path.abspath(sys.argv[2])
    sp = importlib.util.spec_from_file_location('pognon_specs', spec_path); specs = importlib.util.module_from_spec(sp); sp.loader.exec_module(specs)
    os.chdir(wd)
    for a in sys.argv[3:]:
        n = int(a); txt, imgs = draft(n, specs)
        print(f'===== No. {n}'); print(txt)
        sheet(imgs, f'rv{n}.png', 0.5)
