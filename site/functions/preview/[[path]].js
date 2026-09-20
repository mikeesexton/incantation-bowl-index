/**
 * Host lock for the gated scholar preview (ACCESS-009).
 *
 * The Cloudflare Access policy is attached to a hostname, and a Pages project
 * answers on more than one: bowlam.com, bowlam.pages.dev, and a
 * <hash>.bowlam.pages.dev alias for every deployment. A policy on the custom
 * domain leaves the others serving the same bytes with no gate in front — which
 * is exactly what happened on 20 September 2026, when a promoted build was
 * downloadable at bowlam.pages.dev/preview/data/texts.json while bowlam.com
 * correctly redirected to Access.
 *
 * So the gate is not trusted to be the only thing standing there. Anything
 * under /preview is served on the one host Access covers and answers 404
 * everywhere else, in code, where it cannot be undone by a dashboard edit.
 */

const GATED_HOST = "bowlam.com";

export async function onRequest(context) {
  const host = (context.request.headers.get("Host") || "").toLowerCase().split(":")[0];
  if (host !== GATED_HOST) {
    // 404, not 403: a preview deployment should look like it has no such path
    // rather than advertise that something is here and worth attacking.
    return new Response("Not found", {
      status: 404,
      headers: {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"},
    });
  }
  // On the gated host, Access has already run at the edge; serve the asset.
  const response = await context.env.ASSETS.fetch(context.request);
  const headers = new Headers(response.headers);
  // Never let an intermediary hold a copy of gated data.
  headers.set("Cache-Control", "private, no-store");
  headers.set("X-Robots-Tag", "noindex, nofollow");
  return new Response(response.body, {status: response.status, headers});
}
