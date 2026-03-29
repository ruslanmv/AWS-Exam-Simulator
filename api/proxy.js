/**
 * Vercel Serverless Proxy for OllaBridge Cloud
 *
 * Endpoint:
 *   POST /api/proxy
 * Body:
 *   { url, method, headers, body }
 *
 * Security:
 * - HTTPS only (except localhost for dev)
 * - Allowlist upstream domains (prevents open relay)
 * - Supports PROXY_ALLOWLIST env var for additional domains
 */

const ALLOW = [
    'https://ruslanmv-ollabridge.hf.space',
    'https://ollabridge.com',
    'https://cloud.ollabridge.com',
];

const TRUSTED_PATTERNS = [
    /^https:\/\/[a-zA-Z0-9_-]+-[a-zA-Z0-9_-]+\.hf\.space/,
    /^https:\/\/([a-zA-Z0-9_-]+\.)*ollabridge\.com/,
];

function isAllowedUrl(url) {
    const u = String(url || '');
    // Allow localhost for development
    if (/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(u)) return true;
    if (!/^https:\/\//i.test(u)) return false;

    const extra = (process.env.PROXY_ALLOWLIST || '')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
    const list = [...ALLOW, ...extra];
    if (list.some((base) => u.startsWith(base))) return true;
    if (TRUSTED_PATTERNS.some((re) => re.test(u))) return true;
    return false;
}

function sanitizeRequestHeaders(headersObj) {
    const unsafe = new Set([
        'host', 'connection', 'content-length', 'transfer-encoding',
        'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailer', 'upgrade', 'origin', 'referer',
    ]);
    const out = {};
    const h = headersObj && typeof headersObj === 'object' ? headersObj : {};
    for (const [k, v] of Object.entries(h)) {
        const key = String(k || '').toLowerCase();
        if (!key || unsafe.has(key)) continue;
        out[k] = v;
    }
    return out;
}

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization,X-Requested-With,Accept'
    );

    if (req.method === 'OPTIONS') return res.status(204).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method Not Allowed' });

    try {
        const { url, method, headers, body } = req.body || {};

        if (!url || typeof url !== 'string') {
            return res.status(400).json({ error: 'Missing "url" in request body.' });
        }
        if (!isAllowedUrl(url)) {
            return res.status(403).json({ error: 'Target URL not in allowlist.' });
        }

        const m = String(method || 'POST').toUpperCase();
        const upstreamHeaders = new Headers(sanitizeRequestHeaders(headers));
        const hasBody = body !== undefined && body !== null;

        if (hasBody && !upstreamHeaders.has('content-type')) {
            upstreamHeaders.set('content-type', 'application/json');
        }

        const upstreamBody = !hasBody ? undefined : typeof body === 'string' ? body : JSON.stringify(body);

        const upstream = await fetch(url, {
            method: m,
            headers: upstreamHeaders,
            body: upstreamBody,
        });

        const text = await upstream.text();
        res.status(upstream.status);

        const ct = upstream.headers.get('content-type');
        if (ct) res.setHeader('content-type', ct);

        return res.send(text);
    } catch (err) {
        console.error('[api/proxy] error:', err);
        return res.status(500).json({ error: err?.message || String(err) });
    }
}
