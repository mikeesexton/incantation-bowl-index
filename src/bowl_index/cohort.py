"""Reproducible main Montgomery cohort accounting with evidence-bound review status."""
import json
from pathlib import Path
from .identity import identity_rows
from .proofreading import current_text_reviews
from .concordance import current_concordance_reviews


def write_montgomery_cohort(conn, register_path, destination):
    register=json.loads(Path(register_path).read_text())
    source=register['source_id']
    identities=identity_rows(conn)
    by_member={member:row for row in identities for member in json.loads(row['member_ids_json'])}
    checked=current_text_reviews(conn)
    museum_reviews=current_concordance_reviews(conn)
    rows=[]
    for entry in register['entries']:
        n=entry['text_number'];obj=entry['object_id'];identity=by_member[obj]
        texts=[dict(r) for r in conn.execute("SELECT * FROM texts WHERE object_id=? AND source_id=? AND text_type='translation'",(obj,source))]
        absent=[cl for cl in entry['claims'] if cl['field']=='translation_availability']
        if texts:
            translation='reading_text_checked' if any(t['id'] in checked and checked[t['id']]['status']=='reading_text_checked' for t in texts) else 'ocr_pending_proofreading'
        elif absent:
            translation='no_separate_translation_in_this_edition'
        else:
            translation='unassessed'
        ids=json.loads(identity['identifiers_json'])
        penn=[value.split(': ',1)[1] for value in ids if value.startswith('Penn web object ID: ')]
        reviews=[museum_reviews[(obj,p)] for p in penn if (obj,p) in museum_reviews]
        confirmed=bool(penn) and len(reviews)==len(penn) and all(r['status']=='confirmed' for r in reviews)
        dimension=next(cl for cl in entry['claims'] if cl['field']=='dimensions')
        number=next(cl for cl in entry['claims'] if cl['field']=='publication_register_identifier')
        rows.append({'text_number':n,'object_id':obj,'identity_id':identity['identity_id'],
                     'register_identifier':number['value_text'],'register_locator':number['locator'],
                     'height_cm':dimension['value_json']['height_cm'],'diameter_cm':dimension['value_json']['diameter_cm'],
                     'penn_web_ids':penn,'penn_mapping_status':'confirmed_from_dated_museum_page' if confirmed else ('existing_link_not_freshly_verified' if penn else 'unresolved'),
                     'penn_concordance_reviews':[{'review_id':r['id'],'reviewed_at':r['reviewed_at'],
                         'status':r['status'],'observation':json.loads(r['review_json'])['entry']['observation']} for r in reviews],
                     'translation_status':translation,'translation_text_ids':[t['id'] for t in texts],
                     'translation_absence_evidence':[cl['locator']+': '+cl['value_text'] for cl in absent],
                     'transcription_status':'not_captured_from_scan'})
    if [r['text_number'] for r in rows] != list(range(1,41)):
        raise ValueError('Main Montgomery cohort must enumerate texts 1-40 exactly once')
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    json_path=destination.with_suffix('.json')
    json_path.write_text(json.dumps({'source_id':source,'source_pdf_sha256':register['source_pdf_sha256'],'rows':rows},ensure_ascii=False,indent=2)+'\n')
    counts={key:sum(r['translation_status']==key for r in rows) for key in {r['translation_status'] for r in rows}}
    lines=['# Montgomery/Penn reference cohort','',
           'The main cohort contains forty numbered bowls. All forty catalogue-register rows were visually checked against printed pp. 321–326 (PDF pp. 327–332). Museum checks below are dated observations, valid against the current local identity evidence; they do not assert that a website has remained unchanged since review.','',
           'Penn concordances: **%s/40** supported by current evidence-bound museum-page reviews.'%sum(r['penn_mapping_status']=='confirmed_from_dated_museum_page' for r in rows),'',
           'English translations: **%s** scan-checked normalized reading texts, **%s** OCR drafts pending proofreading, and **%s** documented cases where this edition supplies no separate translation.'%(counts.get('reading_text_checked',0),counts.get('ocr_pending_proofreading',0),counts.get('no_separate_translation_in_this_edition',0)),'',
           'Reading texts normalize typography and Latin-name diacritics and preserve loss/uncertainty markers; they are not diplomatic transcriptions or new translations. No proofreading decision grants public reuse.','',
           '| Text | Register number | Height × diameter (cm) | Penn web ID(s) | Museum review | Translation |',
           '|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | %s | %g × %g | %s | %s | %s |'%(r['text_number'],r['register_identifier'],r['height_cm'],r['diameter_cm'],', '.join(r['penn_web_ids']) or 'Unresolved',r['penn_mapping_status'].replace('_',' '),r['translation_status'].replace('_',' ')))
    lines += ['', '## Explicit exceptions','',
              '- Text 14: heading CBS 16917 versus register CBS 16017; both source readings remain recorded.',
              '- Text 19: register number is blank; heading supplies CBS 16018.',
              '- Text 40: register prints CBS 2972, while the heading and previously checked Penn correction identify CBS/B2971; no merge with text 28 is inferred.',
              '- Texts 18, 21, 23, 27 and 33 have source-located explanations for the absence of separate translations. These are not assertions that no translation exists in later scholarship.',
              '- All forty still require checked original-script transcription or transliteration; OCR is not a reliable substitute.',
              '- Appendix 41 is explicitly a skull, excluded from the main bowl cohort. Appendix 42 is now separately recorded as a candidate for an unlocated possible bowl; its material carrier and date are unconfirmed. Neither is silently counted as one of the forty.',
              '', '## Evidence','',
              '- Checked register: `research/enrichment/montgomery_register_checked_2026-09-04.json`.',
              '- Text proofreading: `research/reviews/montgomery_reading_texts_2026-09-04.json`.',
              '- Remaining 24 translations: `research/reviews/montgomery_reading_texts_completion_2026-09-05.json` (formula diacritics retained under the recorded policy).',
              '- Dated museum observations: `research/reviews/penn_montgomery_concordance_2026-09-05.json`; confirmation applies to the numbered concordance, not every catalogue field.',
              '- The JSON beside this report contains exact object, identity, text and source locators.']
    destination.write_text('\n'.join(lines)+'\n')
    return {'main_cohort':len(rows),'existing_penn_links':sum(bool(r['penn_web_ids']) for r in rows),
            'confirmed_penn_concordances':sum(r['penn_mapping_status']=='confirmed_from_dated_museum_page' for r in rows),'translations':counts}


def apply_montgomery_register(conn, register_path):
    """Append checked register claims; require exact existing appearance links."""
    from .ids import new_id
    register = json.loads(Path(register_path).read_text())
    entries = register['entries']
    if sorted(e['text_number'] for e in entries) != list(range(1, 41)):
        raise ValueError('Montgomery register must enumerate texts 1-40 exactly once')
    source_id = register['source_id']
    inserted = 0
    with conn:
        if not conn.in_transaction:
            conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM captures WHERE source_id=? AND sha256=?',
                            (source_id, register['source_pdf_sha256'])).fetchone():
            raise ValueError('Register scan must be registered to its source')
        for entry in entries:
            if not conn.execute('SELECT 1 FROM appearances a JOIN appearance_object_links l '
                                'ON l.appearance_id=a.id WHERE a.id=? AND a.source_id=? AND l.object_id=?',
                                (entry['appearance_id'], source_id, entry['object_id'])).fetchone():
                raise ValueError('Register appearance/source/object link mismatch')
            for claim in entry['claims']:
                if not claim.get('locator', '').strip() or not claim.get('notes', '').strip():
                    raise ValueError('Checked register claims require locator and notes')
                structured = json.dumps(claim['value_json'], ensure_ascii=False, sort_keys=True) if 'value_json' in claim else None
                values = (entry['object_id'], entry['appearance_id'], source_id, claim['field'],
                          claim['value_text'], structured, claim.get('certainty', 'reported'), claim['locator'], claim['notes'])
                columns = ('object_id','appearance_id','source_id','field','value_text','value_json','certainty','locator','notes')
                if conn.execute('SELECT 1 FROM claims WHERE ' + ' AND '.join(k+' IS ?' for k in columns), values).fetchone():
                    continue
                conn.execute('INSERT INTO claims (id,'+','.join(columns)+') VALUES ('+','.join('?' for _ in range(10))+')',
                             ('IBI-'+new_id('claim'),)+values)
                inserted += 1
    return {'main_entries': 40, 'claims_added': inserted}
