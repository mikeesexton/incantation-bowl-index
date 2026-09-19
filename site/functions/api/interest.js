/**
 * POST /api/interest — store an email address from the landing page.
 *
 * This endpoint touches the interest list and nothing else. It has no
 * connection to the corpus: the research console is localhost-only and is
 * never deployed, and the landing page ships as flat HTML with its counts
 * baked in at build time (ACCESS-008).
 *
 * Responses are deliberately uniform. A caller cannot tell a new address from
 * one already on the list, so the endpoint cannot be used to test whether a
 * given person has signed up.
 */

const MAX_BODY = 2048;
// Deliberately permissive: the confirmation email is what proves an address
// works. A stricter pattern mostly rejects valid, unusual addresses.
const EMAIL = /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/;

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
    },
  });

/** Truncated SHA-256 of IP + daily salt: enough to rate-limit, not to identify. */
async function rateKey(request) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const day = new Date().toISOString().slice(0, 10);
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(`${ip}:${day}`)
  );
  return [...new Uint8Array(digest)].slice(0, 8)
    .map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Single entry point. Exporting only `onRequestPost` leaves other methods
 * unrouted, and Pages then falls through to the static assets and answers a
 * GET /api/interest with the landing page. One `onRequest` that dispatches on
 * method keeps the API path an API path.
 */
export async function onRequest(context) {
  if (context.request.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed." }), {
      status: 405,
      headers: { "Content-Type": "application/json; charset=utf-8", Allow: "POST" },
    });
  }
  return handleSignup(context);
}

async function handleSignup({ request, env }) {
  if (!env.DB) return json(503, { error: "The signup list is not configured yet." });

  const type = request.headers.get("Content-Type") || "";
  if (!type.includes("application/json")) {
    return json(415, { error: "Expected JSON." });
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY) return json(413, { error: "That request was too large." });

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return json(400, { error: "We could not read that request." });
  }

  // Honeypot: a real person never fills a field they cannot see. Answer as if
  // it worked, so a bot gets no signal that it was caught.
  if (typeof payload.website === "string" && payload.website.trim() !== "") {
    return json(200, { ok: true });
  }

  const email = String(payload.email ?? "").trim().toLowerCase();
  if (!email || email.length > 254 || !EMAIL.test(email)) {
    return json(400, { error: "Please enter an email address we can reach you at." });
  }

  const key = await rateKey(request);
  try {
    const recent = await env.DB.prepare(
      "SELECT COUNT(*) AS n FROM interest_signups WHERE ip_day_hash = ?1 " +
      "AND created_at > datetime('now', '-1 day')"
    ).bind(key).first();

    if (recent && recent.n >= 10) {
      return json(429, { error: "Too many signups from here today. Please try later." });
    }

    // INSERT OR IGNORE against the UNIQUE index: a repeat address is a no-op
    // and still reports success, so the endpoint reveals no membership.
    await env.DB.prepare(
      "INSERT OR IGNORE INTO interest_signups (email, created_at, source, ip_day_hash) " +
      "VALUES (?1, datetime('now'), ?2, ?3)"
    ).bind(email, String(payload.source ?? "bowlam.com").slice(0, 64), key).run();

    return json(200, { ok: true });
  } catch (error) {
    console.error("interest signup failed", error);
    return json(500, { error: "We could not save that address. Please try again." });
  }
}
