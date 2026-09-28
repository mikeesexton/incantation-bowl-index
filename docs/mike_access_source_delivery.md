# Mike Access source delivery roadmap

Status: 28 September 2026. This is a Mike-only access plan, not a public reuse
decision. The corpus state contains 59 registered captures from 56 linked
sources, with two captures lacking a source assignment. The records total
762,231,658 bytes; 55 content hashes are distinct. Forty-five captures are PDFs
and fourteen are HTML. Nine PDFs (503,095,337 bytes together) exceed the
current 25 MiB Cloudflare Pages per-asset limit. The largest is 144,458,750
bytes. These are retained files, separate from the 380 recorded media rows;
only 33 media rows currently have local image derivatives.

| Surface | Capture delivery | State |
|---|---|---|
| Local research console | Registered files stream from the private archive by opaque capture ID; the private reader lists every capture | Complete for 59/59 retained captures |
| Local static Mike snapshot | Build copies every retained file into its ignored directory, links it by opaque ID, and checks length and SHA-256 | Complete for 59/59 retained captures; never place this build under `site/public` |
| Remote Mike Access | No capture is deployed; Mike-only identity policy and private large-file delivery are not yet verified | Open |
| Shared preview and public site | Private captures are absent | Correct release boundary |

## Remaining work

1. **Private remote storage.** Provision a nonpublic Cloudflare R2 bucket and
   bind it to the Mike-only Pages Function or Worker. Upload the 55 distinct
   archive blobs by hash; map all 59 capture IDs to those blobs with a private
   manifest. Check bytes and SHA-256 after upload. Do not enable an R2 public
   bucket, a public object URL, or Git-tracked capture bytes. Pages cannot hold
   the nine oversized PDFs as static assets. [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
   and [R2 Worker bindings](https://developers.cloudflare.com/r2/api/workers/workers-api-usage/)
   describe the platform constraints.
2. **Authenticated delivery.** Add a `/mike/captures/<capture-id>` handler that
   resolves only registered IDs, reads the private R2 binding, streams large PDFs
   (including byte ranges), and serves saved HTML as a download. Apply the
   exact `bowlam.com` host lock before storage access and return private
   `no-store`, `nosniff`, and `noindex` headers. Verify that Cloudflare Access
   admits Mike alone to `/mike*`, and that project/deployment aliases and direct
   object endpoints cannot bypass it.
3. **Remote build mode.** Build the same `PrivateResearchProjection` and source
   inventory with capture URLs pointing at that handler, while excluding the
   archive bytes from the Pages asset bundle. Keep the local complete snapshot
   mode for offline use. Fail the remote build if any registered capture lacks
   a storage mapping or if a private local path enters JSON or HTML.
4. **End-to-end parity and operations.** From Mike's authenticated session, open
   representative small and large PDFs, an HTML capture, every source-list link,
   and all 59 capture IDs. Compare the remote manifest's IDs, hashes and lengths
   with the local archive. Test denial on the public host aliases, a non-Mike
   identity, missing IDs, and cache/indexing routes. Include new captures in
   repeatable sync and backup/restore checks before deploying the private
   surface.

The local steps are implemented. Remote completion is an integration and
verification project: private object storage, one authenticated delivery route,
one remote build mode, and a full gate/parity test. The 59 held captures can be
made available without waiting for text extraction from the other held editions;
that extraction remains a separate `TEXT-004` backlog. Remote deployment should
follow review of the complete build and identity policy.
