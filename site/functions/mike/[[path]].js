/**
 * Host lock for Mike's single-user private research surface.
 *
 * Cloudflare Access must separately restrict bowlam.com/mike* to Mike's identity.
 * This lock prevents the same private files from being served through the Pages
 * project and per-deployment aliases, which are not covered by that policy.
 */

const GATED_HOST = "bowlam.com";

export async function onRequest(context) {
  const host = (context.request.headers.get("Host") || "").toLowerCase().split(":")[0];
  if (host !== GATED_HOST) {
    return new Response("Not found", {
      status: 404,
      headers: {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"},
    });
  }
  const response = await context.env.ASSETS.fetch(context.request);
  const headers = new Headers(response.headers);
  headers.set("Cache-Control", "private, no-store");
  headers.set("X-Robots-Tag", "noindex, nofollow");
  return new Response(response.body, {status: response.status, headers});
}
