/* The reading room's card line. reading.js is an IIFE, so take the slice from
   the top of its body down to the first renderer and evaluate that alone,
   exporting the helpers. Same spirit as test_catalogue_unit.cjs, which slices
   app.js; the wrapper is the only difference. */
const assert = require("node:assert");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("web/reading.js", "utf8");
const body = source.slice(source.indexOf('const TABLES'), source.indexOf("const BROWSE"));
const context = vm.createContext({});
vm.runInContext(body + "\nglobalThis.T = {summarise, mark, mediaGallery, orderedImages, displayImageUrl, readableText, textSections, card, data};", context);
const {summarise, mark, mediaGallery, orderedImages, displayImageUrl, readableText, textSections, card, data} = context.T;

test("invalidating a loaded reader refreshes texts and their identity indexes", async () => {
  let content = "Earlier reading";
  let requests = 0;
  const loader = vm.createContext({
    window: {},
    fetch: async url => {
      requests += 1;
      const table = url.split("/").pop();
      const rows = {
        identity_clusters: [{identity_id: "IDENT-REFRESH", display_name: "Test bowl", member_ids: '["OBJ-REFRESH"]'}],
        objects: [{id: "OBJ-REFRESH"}],
        sources: [{id: "SRC-REFRESH", title: content}],
        texts: [{object_id: "OBJ-REFRESH", content_status: "private_research", content}],
      };
      return {json: async () => table === "manifest"
        ? {access_tier: "private_research"} : {rows: rows[table] || []}};
    },
  });
  const loadBody = source.slice(source.indexOf("const READER"), source.indexOf("const factsOf"));
  vm.runInContext(loadBody + "\nglobalThis.T = {load, invalidate};", loader);
  let loaded = await loader.T.load();
  assert.equal(loaded.textsBy["IDENT-REFRESH"][0].content, content);
  const firstRequests = requests;
  content = "New original incantation";
  loaded = await loader.T.load();
  assert.equal(requests, firstRequests);
  assert.equal(loaded.textsBy["IDENT-REFRESH"][0].content, "Earlier reading");
  loader.T.invalidate();
  loaded = await loader.T.load();
  assert.equal(requests, firstRequests * 2);
  assert.equal(loaded.textsBy["IDENT-REFRESH"][0].content, content);
  assert.equal(loaded.sourceById["SRC-REFRESH"].title, content);
  assert.match(loaded.clusterById["IDENT-REFRESH"].haystack, /new original incantation/);
});

const ID = "IDENT-TEST";
const cluster = {identity_id: ID};
function given({facts = [], texts = [], media = [], accessTier = "release"}) {
  data.factsBy = {[ID]: facts};
  data.textsBy = {[ID]: texts};
  data.mediaBy = {[ID]: media};
  data.sourceById = {};
  data.manifest = {access_tier: accessTier};
}
const fact = (field, field_group, value) => ({field, field_group, value});

test("a partially proofread private original carries its working-text warning", () => {
  given({accessTier: "private_research"});
  const html = textSections([{text_type: "transcription", content: "א", script: "Hebrew",
    editorial_status: "partial_review"}]);
  assert.match(html, /Working text · partly proofread/);
  assert.match(html, /Full source-page proofreading remains open/);
  given({accessTier: "release"});
  assert.doesNotMatch(textSections([{text_type: "transcription", content: "א", script: "Hebrew",
    editorial_status: "partial_review"}]), /Working text · partly proofread/);
});

test("a written card line is preferred to anything composed from claims", () => {
  given({
    facts: [fact("text_purpose", "ritual", "Protection of a household"),
            fact("client", "client", "Dadbeh bar Asmanduch")],
    texts: [{editor: "Incantation Bowl Index card line", content_status: "included",
             content: "Divorce dismissing Lilith of the Desert, for Komes bath Mahlaphta"}],
  });
  assert.strictEqual(summarise(cluster, 96),
    "Divorce dismissing Lilith of the Desert, for Komes bath Mahlaphta");
});

test("a withheld card line is ignored rather than rendered blank", () => {
  given({
    facts: [fact("text_purpose", "ritual", "Protection of a household")],
    texts: [{editor: "Incantation Bowl Index card line",
             content_status: "withheld_consult_the_edition", content: null}],
  });
  assert.strictEqual(summarise(cluster, 96), "Protection of a household");
});

test("an installation instruction never outranks the purpose, however short", () => {
  given({facts: [
    fact("installation_instruction", "ritual", "Exterior directs placement"),
    fact("text_purpose", "ritual",
         "Protection of a family, household, and possessions from demons, curses and liliths"),
  ]});
  assert.match(summarise(cluster), /^Protection of a family/);
});

test("within a field the shortest value wins, so hedged discussion loses", () => {
  given({facts: [
    fact("text_purpose", "ritual", "Popularity and economic success"),
    fact("text_purpose", "ritual",
         "Popularity and social influence; Ford infers likely economic success, but notes that it is not explicit"),
  ]});
  assert.strictEqual(summarise(cluster), "Popularity and economic success");
});

test("the client survives truncation of a long purpose", () => {
  given({facts: [
    fact("text_purpose", "ritual",
         "Protection of a family, household, and possessions from demons, curses, liliths and other harms"),
    fact("client", "client", "Dadbeh son of Asmanduk"),
  ]});
  const line = summarise(cluster, 96);
  assert.ok(line.length <= 96, `line was ${line.length} characters`);
  assert.match(line, /for Dadbeh son of Asmanduk$/);
});

test("a list of clients keeps the first name whole", () => {
  given({facts: [
    fact("text_purpose", "ritual", "Protection of a household"),
    fact("clients", "client",
         "Dadbeh son of Asmanduk; Sharqoi daughter of Dada; their named children and household"),
  ]});
  assert.strictEqual(summarise(cluster),
    "Protection of a household — for Dadbeh son of Asmanduk and others");
});

test("an approved image prints its attribution and reviewed rights status", () => {
  given({media: [{media_type: "image", url: "https://example.org/bowl.jpg",
    attribution: "Test Museum", rights_status: "open_license", license_url: ""}]});
  const html = mark({...cluster, display_name: "Test bowl"});
  assert.match(html, /Test Museum · open licence/);
});

test("the catalogue thumbnail stays primary and every approved view appears in the dossier gallery", () => {
  given({media: [
    {media_type: "image", url: "https://example.org/second_1600.jpg", attribution: "Museum"},
    {media_type: "image", url: "https://example.org/primary_800.jpg", attribution: "Museum"},
    {media_type: "image", url: "https://example.org/third_1600.jpg", attribution: "Museum"},
  ]});
  const named = {...cluster, display_name: "Test bowl"};
  assert.match(orderedImages(named)[0].url, /primary_800\.jpg$/);
  assert.match(mark(named), /primary_800\.jpg/);
  const gallery = mediaGallery(named);
  assert.equal((gallery.match(/class="gallery-image"/g) || []).length, 3);
  assert.match(gallery, /3 views recorded for this object/);
  assert.match(gallery, /Test bowl — view 3/);
});

test("legacy Penn asset URLs use the current Collections image host", () => {
  const legacy = "https://www.penn.museum//collections/assets/065T/658k/658212_800.jpg";
  assert.strictEqual(displayImageUrl(legacy),
    "https://collections.penn.museum/collections/assets/065T/658k/658212_1600.jpg");
  given({media: [{media_type: "image", url: legacy, attribution: "Penn Museum"}]});
  assert.match(mark({...cluster, display_name: "Penn bowl"}),
    /https:\/\/collections\.penn\.museum\/collections\/assets\/065T\/658k\/658212_1600\.jpg/);
});

test("a private text is readable only in the Mike-only research tier", () => {
  const row = {content_status: "private_research", content: "PRIVATE TRANSLATION"};
  given({texts: [row]});
  assert.strictEqual(readableText(row), false);
  given({texts: [row], accessTier: "private_research"});
  assert.strictEqual(readableText(row), true);
});

test("an unapproved local image is labelled private research, not reviewed reuse", () => {
  given({accessTier: "private_research", media: [{media_type: "image",
    url: "https://example.org/private.jpg", attribution: "Test catalogue",
    rights_status: "copyrighted",
    rights_statement: "Private research view only; no public reuse permission recorded."}]});
  const html = mark({...cluster, display_name: "Private bowl"});
  assert.match(html, /private research view/);
  assert.doesNotMatch(html, /reviewed reuse/);
});

test("a PDF or catalogue page is a source link, never a broken image", () => {
  given({accessTier: "private_research", media: [{media_type: "image",
    url: "https://example.org/edition.pdf", source_id: "SRC-TEST",
    attribution: "Test edition", rights_status: "copyrighted",
    rights_statement: "Private research view only; no public reuse permission recorded."}]});
  data.sourceById["SRC-TEST"] = {url: "https://example.org/source-record"};
  const html = mark({...cluster, display_name: "Referenced bowl"});
  assert.doesNotMatch(html, /<img/);
  assert.match(html, /Open image source/);
  assert.match(html, /href="https:\/\/example.org\/source-record"/);
  const cardMark = mark({...cluster, display_name: "Referenced bowl"}, false);
  assert.doesNotMatch(cardMark, /<a\b/);
  assert.doesNotMatch(cardMark, /Open image source/);
  const cardHtml = card({...cluster, display_name: "Referenced bowl",
    display_collection: "Test collection", display_language: "Aramaic",
    display_date: "Date not recorded"});
  assert.strictEqual((cardHtml.match(/<a\b/g) || []).length, 1,
    "a card must contain only its single outer link");
});

test("a translation leads and the Aramaic transcription is expandable", () => {
  const html = textSections([
    {text_type: "summary", content: "A short research summary.", language: "English"},
    {text_type: "transcription", content: "בשמך אנא", language: "Jewish Babylonian Aramaic",
      script: "Jewish square script", content_status: "private_research"},
    {text_type: "translation", content: "In your name, I...", language: "English",
      content_status: "private_research"},
  ]);
  assert.ok(html.indexOf("Translation") < html.indexOf("Show original incantation"));
  assert.match(html, /Show original incantation/);
  assert.match(html, /dir="rtl"/);
  assert.match(html, /בשמך אנא/);
  assert.match(html, /Research summary/);
});

test("English leads while source-language translations stay available separately", () => {
  const html = textSections([
    {text_type: "translation", language: "French", content: "Au nom de la Vie"},
    {text_type: "translation", language: "English", content: "In the name of Life",
      editor: "Incantation Bowl Index — English rendering of Henri Pognon’s French translation (draft)"},
  ]);
  assert.ok(html.indexOf("In the name of Life") < html.indexOf("Source-language translations"));
  assert.ok(html.indexOf("Au nom de la Vie") > html.indexOf("Source-language translations"));
  assert.match(html, /Draft; not an independent translation from the inscription/);
  assert.match(textSections([{text_type: "translation", language: "German", content: "In deinem Namen"}]),
    /No English translation is available/);
});

test("original-script facsimiles are shown before whole source pages and labelled accurately", () => {
  const html = textSections([], [
    {media_type: "scan", url: "/api/private-media/FULL.png"},
    {media_type: "inscription_facsimile", url: "/api/private-media/NATIVE.png"},
  ]);
  assert.ok(html.indexOf("NATIVE.png") < html.indexOf("FULL.png"));
  assert.match(html, /Original-script edition text · facsimile/);
  assert.match(html, /Not a searchable transcription/);
});

test("commentary never substitutes for the translation and empty originals are explicit", () => {
  const html = textSections([{text_type: "summary", content: "A catalogue description."}]);
  const translation = html.slice(0, html.indexOf("Research summary and commentary"));
  assert.match(translation, /What it says/);
  assert.match(translation, /No translation is available/);
  assert.match(translation, /No transcription or transliteration is stored/);
  assert.doesNotMatch(translation, /A catalogue description/);
  assert.match(html, /<details[^>]*><summary>Research summary and commentary/);
  assert.doesNotMatch(html, /<details[^>]* open/);
});

test("Latin transliterations stay readable and original markup is escaped", () => {
  const html = textSections([{text_type: "transliteration", script: "Latin",
    language: "Mandaic", content: "<script>bad()</script>"}]);
  assert.match(html, /dir="auto"/);
  assert.doesNotMatch(html, /dir="rtl"/);
  assert.match(html, /&lt;script&gt;/);
});

test("a retained original page is expandable and distinguished from a transcription", () => {
  given({accessTier: "private_research"});
  const html = textSections([], [{media_type: "scan", url: "/api/private-media/MED-TEST.png",
    attribution: "Montgomery 1913", rights_statement: "Private research view only;"}]);
  assert.match(html, /No transcription or transliteration is stored/);
  assert.match(html, /Recorded source pages are available/);
  assert.match(html, /Published source page · facsimile/);
  assert.match(html, /private research view/);
  assert.match(html, /alt="Published source page"/);
  assert.ok(html.indexOf("<details") < html.indexOf("<img"));
});
