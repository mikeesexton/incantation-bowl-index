/* The reading room's card line. reading.js is an IIFE, so take the slice from
   the top of its body down to the first renderer and evaluate that alone,
   exporting the helpers. Same spirit as test_catalogue_unit.cjs, which slices
   app.js; the wrapper is the only difference. */
const assert = require("node:assert");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("web/reading.js", "utf8");
const body = source.slice(source.indexOf('const TABLES'), source.indexOf("function card(cluster)"));
const context = vm.createContext({});
vm.runInContext(body + "\nglobalThis.T = {summarise, mark, data};", context);
const {summarise, mark, data} = context.T;

const ID = "IDENT-TEST";
const cluster = {identity_id: ID};
function given({facts = [], texts = [], media = []}) {
  data.factsBy = {[ID]: facts};
  data.textsBy = {[ID]: texts};
  data.mediaBy = {[ID]: media};
}
const fact = (field, field_group, value) => ({field, field_group, value});

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
