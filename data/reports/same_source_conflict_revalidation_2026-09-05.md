# Same-source conflict revalidation batch

Reviewed: `2026-09-05T19:35:44+00:00`

Twenty older conflict decisions were revalidated against their exact current claim evidence. Every case involved one source and one physical-object record. All twenty are compatible; no source claim, identity, or canonical value changed.

The batch covers:

- Three equivalent descriptions for Museo Sefardí de Toledo AC-MSEF: qualified sixth-century dating, identical dimensions in different order, and an institution name with or without country.
- One Kelsey Museum provenance pair in which excavation context and findspot are complementary.
- Eleven British Museum dating pairs in which a numeric century range and a period label are separate chronological facets.
- Five British Museum provenance pairs in which find/acquisition place and production place remain separate fields.

Compatibility here means that the cited statements can coexist. It does not independently verify their historical accuracy or collapse distinct fields. The checked manifest is `research/reviews/same_source_facets_batch_2026-09-05.json`; replay is a no-op. After this batch, **53/337** conflict instances have current evidence-bound decisions and **284** remain in the revalidation queue.
