var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// index.js
var index_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    function safeJSON(s) {
      try {
        return s ? JSON.parse(s) : null;
      } catch {
        return null;
      }
    }
    __name(safeJSON, "safeJSON");
    function json(o, init = {}) {
      return new Response(JSON.stringify(o), {
        headers: { "Content-Type": "application/json" },
        ...init
      });
    }
    __name(json, "json");
    function obfJson(o, init = {}) {
      const entries = Object.entries(o);
      for (let i = entries.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [entries[i], entries[j]] = [entries[j], entries[i]];
      }
      const out = {};
      for (const [k, v] of entries) out[k] = v;
      const padChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
      const padLen = 12 + Math.floor(Math.random() * 13);
      let pad = "";
      for (let i = 0; i < padLen; i++) {
        pad += padChars[Math.floor(Math.random() * padChars.length)];
      }
      out.pad = pad;
      return new Response(JSON.stringify(out), {
        headers: { "Content-Type": "application/json" },
        ...init
      });
    }
    __name(obfJson, "obfJson");
    const ALLOWED_TIERS = ["Basic", "Basic+", "Pro", "Premium"];
    function genKey() {
      const c = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
      const part = /* @__PURE__ */ __name(() => Array.from({ length: 6 }, () => c[Math.floor(Math.random() * c.length)]).join(""), "part");
      return Array(6).fill(0).map(part).join("-");
    }
    __name(genKey, "genKey");
    function absRedirect(path, code = 302) {
      const absolute = path.startsWith("http") ? path : `${url.origin}${path.startsWith("/") ? path : `/${path}`}`;
      return Response.redirect(absolute, code);
    }
    __name(absRedirect, "absRedirect");
    function escapeHTML(s) {
      return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#39;");
    }
    __name(escapeHTML, "escapeHTML");
    async function getRec(user) {
      return safeJSON(await env.LICENSES_KV.get(user));
    }
    __name(getRec, "getRec");
    async function findLicenseByKeyOrUser(maybeKeyOrUser) {
      try {
        const direct = await env.LICENSES_KV.get(maybeKeyOrUser);
        if (direct !== null) {
          return { username: maybeKeyOrUser, record: safeJSON(direct) || {} };
        }
      } catch {
      }
      try {
        let cursor;
        do {
          const page = await env.LICENSES_KV.list({ cursor });
          for (const k of page.keys) {
            const val = await env.LICENSES_KV.get(k.name);
            if (!val) continue;
            const parsed = safeJSON(val) || {};
            if (parsed.key === maybeKeyOrUser) {
              return { username: k.name, record: parsed };
            }
          }
          cursor = page.cursor;
        } while (cursor);
      } catch (e) {
      }
      return null;
    }
    __name(findLicenseByKeyOrUser, "findLicenseByKeyOrUser");
    function bytesToBase64(bytes) {
      let binary = "";
      const view = new Uint8Array(bytes);
      for (let i = 0; i < view.length; i++) {
        binary += String.fromCharCode(view[i]);
      }
      return btoa(binary);
    }
    __name(bytesToBase64, "bytesToBase64");
    function base64ToBytes(b64) {
      try {
        const bin = atob(b64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        return arr.buffer;
      } catch {
        return null;
      }
    }
    __name(base64ToBytes, "base64ToBytes");
    function hexToBytes(hex) {
      try {
        if (hex.length % 2 !== 0) return null;
        const arr = new Uint8Array(hex.length / 2);
        for (let i = 0; i < hex.length; i += 2) {
          arr[i / 2] = parseInt(hex.substr(i, 2), 16);
        }
        return arr.buffer;
      } catch {
        return null;
      }
    }
    __name(hexToBytes, "hexToBytes");
    function bytesEqual(a, b) {
      if (!(a instanceof Uint8Array)) a = new Uint8Array(a);
      if (!(b instanceof Uint8Array)) b = new Uint8Array(b);
      if (a.length !== b.length) return false;
      let res = 0;
      for (let i = 0; i < a.length; i++) res |= a[i] ^ b[i];
      return res === 0;
    }
    __name(bytesEqual, "bytesEqual");
    async function computeHMAC(keyStr, message) {
      const enc = new TextEncoder();
      const keyData = enc.encode(keyStr);
      const cryptoKey = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign", "verify"]
      );
      const sig = await crypto.subtle.sign("HMAC", cryptoKey, message);
      return new Uint8Array(sig);
    }
    __name(computeHMAC, "computeHMAC");
    function parseSignature(sigStr) {
      if (!sigStr) return null;
      const b = base64ToBytes(sigStr);
      if (b) return new Uint8Array(b);
      const h = hexToBytes(sigStr);
      if (h) return new Uint8Array(h);
      return null;
    }
    __name(parseSignature, "parseSignature");
    async function kvIncrement(kv, key, ttl = 60) {
      try {
        const cur = await kv.get(key);
        let count = 0;
        if (cur !== null) {
          const parsed = parseInt(cur, 10);
          if (Number.isFinite(parsed)) count = parsed;
        }
        count += 1;
        await kv.put(key, String(count), { expirationTtl: ttl });
        return count;
      } catch (e) {
        try {
          await kv.put(key, "1", { expirationTtl: ttl });
        } catch {
        }
        return 1;
      }
    }
    __name(kvIncrement, "kvIncrement");
    async function kvGetInt(kv, key) {
      try {
        const cur = await kv.get(key);
        if (cur === null) return 0;
        const parsed = parseInt(cur, 10);
        return Number.isFinite(parsed) ? parsed : 0;
      } catch {
        return 0;
      }
    }
    __name(kvGetInt, "kvGetInt");
    async function storeNonce(nonce, user, ttl = 300) {
      try {
        if (!env.NONCES_KV) return;
        await env.NONCES_KV.put(`nonce:${nonce}`, user, { expirationTtl: ttl });
      } catch (e) {
      }
    }
    __name(storeNonce, "storeNonce");
    async function lookupNonce(nonce) {
      try {
        if (!env.NONCES_KV) return null;
        const u = await env.NONCES_KV.get(`nonce:${nonce}`);
        return u;
      } catch {
        return null;
      }
    }
    __name(lookupNonce, "lookupNonce");
    function genRandomBase64(len = 32) {
      const arr = new Uint8Array(len);
      crypto.getRandomValues(arr);
      return bytesToBase64(arr);
    }
    __name(genRandomBase64, "genRandomBase64");
    async function trialGet(user) {
      try {
        if (env.TRIALS_KV) {
          return safeJSON(await env.TRIALS_KV.get(`trial:${user}`));
        } else {
          return safeJSON(await env.LICENSES_KV.get(`trial:${user}`));
        }
      } catch {
        return null;
      }
    }
    __name(trialGet, "trialGet");
    async function trialPut(user, obj, ttlSeconds = null) {
      try {
        const s = JSON.stringify(obj);
        if (env.TRIALS_KV) {
          if (ttlSeconds)
            await env.TRIALS_KV.put(`trial:${user}`, s, {
              expirationTtl: ttlSeconds
            });
          else await env.TRIALS_KV.put(`trial:${user}`, s);
        } else {
          if (ttlSeconds)
            await env.LICENSES_KV.put(`trial:${user}`, s, {
              expirationTtl: ttlSeconds
            });
          else await env.LICENSES_KV.put(`trial:${user}`, s);
        }
      } catch {
      }
    }
    __name(trialPut, "trialPut");
    async function trialDelete(user) {
      try {
        if (env.TRIALS_KV) await env.TRIALS_KV.delete(`trial:${user}`);
        else await env.LICENSES_KV.delete(`trial:${user}`);
      } catch {
      }
    }
    __name(trialDelete, "trialDelete");
    async function logTamper(user) {
      try {
        if (env.RATE_KV) {
          await kvIncrement(env.RATE_KV, `tamper:${user}`, 24 * 3600);
        } else {
          const key = `tamper:${user}`;
          if (env.TRIALS_KV) {
            const cur = await env.TRIALS_KV.get(key);
            let n = 0;
            if (cur !== null) n = parseInt(cur, 10) || 0;
            n++;
            await env.TRIALS_KV.put(key, String(n), {
              expirationTtl: 24 * 3600
            });
          } else {
            const cur = await env.LICENSES_KV.get(key);
            let n = 0;
            if (cur !== null) n = parseInt(cur, 10) || 0;
            n++;
            await env.LICENSES_KV.put(key, String(n), {
              expirationTtl: 24 * 3600
            });
          }
        }
      } catch {
      }
    }
    __name(logTamper, "logTamper");
    async function listAll() {
      const out = [];
      let cursor;
      do {
        const page = await env.LICENSES_KV.list({ cursor });
        for (const k of page.keys) {
          const d = await getRec(k.name) || {};
          out.push({
            user: k.name,
            key: d.key ?? "\u2014",
            revoked: !!d.revoked,
            reason: d.reason ?? "",
            hwid: d.hwid ?? "",
            expires: d.expires ?? null,
            tier: d.tier ?? null
          });
        }
        cursor = page.cursor;
      } while (cursor);
      return out;
    }
    __name(listAll, "listAll");
    function parseCookies(request2) {
      const header = request2.headers.get("cookie") || "";
      const obj = {};
      header.split(";").map((c) => c.trim()).filter(Boolean).forEach((c) => {
        const idx = c.indexOf("=");
        if (idx === -1) return;
        const k = c.slice(0, idx).trim();
        const v = c.slice(idx + 1).trim();
        obj[k] = v;
      });
      return obj;
    }
    __name(parseCookies, "parseCookies");
    function getClientIP(request2) {
      const cf = request2.headers.get("CF-Connecting-IP");
      if (cf) return cf;
      const xff = request2.headers.get("X-Forwarded-For");
      if (xff) return xff.split(",")[0].trim();
      return null;
    }
    __name(getClientIP, "getClientIP");
    function maskKey(k) {
      if (!k) return "\u2014";
      if (k.length <= 8) return k.replace(/.(?=.{2})/g, "*");
      return k.substring(0, 4) + k.substring(4, k.length - 4).replace(/./g, "*") + k.substring(k.length - 4);
    }
    __name(maskKey, "maskKey");
    async function isAdminRequest(request2, env2) {
      if (!env2.ADMIN_SESSIONS_KV) return false;
      const cookies = parseCookies(request2);
      const token = cookies["admin_session"];
      if (!token) return false;
      try {
        const val = await env2.ADMIN_SESSIONS_KV.get(`sess:${token}`);
        return !!val;
      } catch {
        return false;
      }
    }
    __name(isAdminRequest, "isAdminRequest");
    async function requireAdmin(request2, env2) {
      if (!await isAdminRequest(request2, env2)) {
        return new Response("Forbidden", { status: 403 });
      }
      return null;
    }
    __name(requireAdmin, "requireAdmin");
    async function createAdminSession(env2) {
      if (!env2.ADMIN_SESSIONS_KV) {
        throw new Error("ADMIN_SESSIONS_KV not bound");
      }
      const arr = new Uint8Array(32);
      crypto.getRandomValues(arr);
      let token = bytesToBase64(arr);
      token = token.replace(/=+$/g, "").replace(/\+/g, "-").replace(/\//g, "_");
      await env2.ADMIN_SESSIONS_KV.put(`sess:${token}`, "1", {
        expirationTtl: 3600
      });
      return token;
    }
    __name(createAdminSession, "createAdminSession");
    async function destroyAdminSession(request2, env2) {
      if (!env2.ADMIN_SESSIONS_KV) return;
      const cookies = parseCookies(request2);
      const token = cookies["admin_session"];
      if (!token) return;
      try {
        await env2.ADMIN_SESSIONS_KV.delete(`sess:${token}`);
      } catch {
      }
    }
    __name(destroyAdminSession, "destroyAdminSession");
    const CLAILA = {
      BASE: "https://app.claila.com/api/v2",
      SESSION_ID: "1764868266",
      // adjust if needed
      COOKIES: "dmcfkjn3cdc=57t5c1snh9jceg0t59llkkoebc; theme=dark; auh=5e04b542",
      REFERER: "https://app.claila.com/chat?uid=b7fe260b&lang=en",
      UA: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0"
    };
    async function clailaGetCsrfToken() {
      const res = await fetch(`${CLAILA.BASE}/getcsrftoken`, {
        method: "GET",
        headers: {
          "User-Agent": CLAILA.UA,
          Accept: "*/*",
          "Accept-Language": "en-US",
          "Accept-Encoding": "gzip, deflate, br, zstd",
          "X-Requested-With": "XMLHttpRequest",
          Referer: CLAILA.REFERER,
          Cookie: CLAILA.COOKIES,
          Pragma: "no-cache",
          "Cache-Control": "no-cache",
          "Sec-Fetch-Dest": "empty",
          "Sec-Fetch-Mode": "cors",
          "Sec-Fetch-Site": "same-origin"
        }
      });
      const txt = await res.text().catch(() => "");
      return (txt || "").trim();
    }
    __name(clailaGetCsrfToken, "clailaGetCsrfToken");
    async function clailaPostForm(path, paramsObj, extraHeaders = {}) {
      const token = await clailaGetCsrfToken();
      const body = new URLSearchParams();
      for (const k of Object.keys(paramsObj)) {
        body.append(k, paramsObj[k]);
      }
      const headers = {
        "User-Agent": CLAILA.UA,
        Accept: "*/*",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-CSRF-Token": token || "",
        "X-Requested-With": "XMLHttpRequest",
        Origin: "https://app.claila.com",
        Referer: CLAILA.REFERER,
        Cookie: CLAILA.COOKIES,
        Connection: "keep-alive",
        Pragma: "no-cache",
        "Cache-Control": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        ...extraHeaders
      };
      const res = await fetch(`${CLAILA.BASE}/${path}`, {
        method: "POST",
        headers,
        body
      });
      const text = await res.text().catch(() => "");
      return { ok: res.ok, status: res.status, headers: res.headers, text };
    }
    __name(clailaPostForm, "clailaPostForm");
    async function clailaChatText(userMessage) {
      const params = {
        model: "gpt-5-mini",
        calltype: "completion",
        message: userMessage,
        sessionId: CLAILA.SESSION_ID,
        chat_mode: "chat",
        websearch: "false",
        tmp_enabled: "1"
      };
      const { ok, status, text } = await clailaPostForm("unichat4", params);
      if (!ok) throw new Error(`Claila text chat failed: HTTP ${status}`);
      return text || "(no text)";
    }
    __name(clailaChatText, "clailaChatText");
    async function clailaUploadImageFromBase64(b64, filename = "image.jpg", mime = "image/jpeg") {
      const buf = base64ToBytes(b64);
      if (!buf) throw new Error("Invalid base64 image");
      const blob = new Blob([buf], { type: mime });
      const form = new FormData();
      form.append("file", blob, filename);
      const headers = {
        "User-Agent": CLAILA.UA,
        Accept: "application/json",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "X-Requested-With": "XMLHttpRequest",
        Origin: "https://app.claila.com",
        Referer: CLAILA.REFERER,
        Cookie: CLAILA.COOKIES,
        Connection: "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
      };
      const res = await fetch(
        `${CLAILA.BASE}/fileupload/${CLAILA.SESSION_ID}`,
        {
          method: "POST",
          headers,
          body: form
        }
      );
      const txt = await res.text().catch(() => "");
      let parsed;
      try {
        parsed = JSON.parse(txt);
      } catch {
        parsed = null;
      }
      if (!res.ok) {
        throw new Error(`Claila fileupload failed: HTTP ${res.status} - ${txt}`);
      }
      const fileId = parsed && (parsed.file || parsed.fileId || parsed.id || null);
      if (!fileId)
        throw new Error(
          "Claila fileupload succeeded but no file id in response"
        );
      return { fileId, raw: parsed ?? txt };
    }
    __name(clailaUploadImageFromBase64, "clailaUploadImageFromBase64");
    async function clailaVisionFromFileId(fileId, prompt = "Explain this image") {
      const params = {
        message: prompt,
        sessionId: CLAILA.SESSION_ID,
        action: "image-vision",
        file: fileId,
        chat_mode: "images",
        websearch: "false",
        tmp_enabled: "0"
      };
      const { ok, status, text } = await clailaPostForm("setchatbot2", params);
      if (!ok) throw new Error(`Claila vision failed: HTTP ${status}`);
      try {
        const parsed = JSON.parse(text);
        if (typeof parsed === "string") return parsed;
        if (parsed.reply) return parsed.reply;
        if (parsed.message) return parsed.message;
        if (parsed.updated_prompt) return parsed.updated_prompt;
        return text;
      } catch {
        return text || "(no text)";
      }
    }
    __name(clailaVisionFromFileId, "clailaVisionFromFileId");
    async function clailaFallbackChat(userMessage, reason, imageFileId = null) {
      try {
        if (imageFileId) {
          const reply = await clailaVisionFromFileId(
            imageFileId,
            userMessage || "Explain this image"
          );
          return {
            provider: "claila",
            model: "gpt-4.1-mini",
            reply: reply || "(no text)",
            raw: reply,
            reason
          };
        } else {
          const reply = await clailaChatText(userMessage);
          return {
            provider: "claila",
            model: "gpt-5-mini",
            reply: reply || "(no text)",
            raw: reply,
            reason
          };
        }
      } catch (e) {
        return {
          error: {
            message: "Claila fallback failed",
            error: String(e)
          },
          reason
        };
      }
    }
    __name(clailaFallbackChat, "clailaFallbackChat");
    try {
      if (url.pathname === "/favicon.ico") {
        return new Response("", { status: 204 });
      }
      if (url.pathname === "/login" && request.method === "GET") {
        const html = `<!doctype html>
<html>
  <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin login</title></head>
  <body style="font-family:Arial,Helvetica,sans-serif;padding:24px;background:#0b0f14;color:#e6eef6">
    <h2>Admin login</h2>
    <form method="POST" action="/login">
      <label>Admin password</label><br>
      <input name="password" type="password" required style="padding:8px;margin:8px 0;display:block;width:320px">
      <button type="submit" style="padding:8px 12px">Login</button>
    </form>
    <p style="color:#97a0b3">Note: set the password in your Worker environment variable GUI_PASSWORD.</p>
  </body>
</html>`;
        return new Response(html, { headers: { "Content-Type": "text/html" } });
      }
      if (url.pathname === "/login" && request.method === "POST") {
        const clientIP = getClientIP(request);
        const form = await request.formData();
        const pass = form.get("password") || "";
        const configured = env.GUI_PASSWORD || "";
        if (!configured) {
          return new Response(
            "Admin password not configured in environment (GUI_PASSWORD).",
            { status: 500 }
          );
        }
        if (pass === configured) {
          let sessionToken;
          try {
            sessionToken = await createAdminSession(env);
          } catch (e) {
            return new Response(
              "Failed to create admin session: " + String(e),
              { status: 500 }
            );
          }
          return new Response(null, {
            status: 302,
            headers: {
              Location: "/guiaddinfo",
              "Set-Cookie": `admin_session=${sessionToken}; Path=/; Max-Age=3600; HttpOnly; Secure; SameSite=Strict`
            }
          });
        }
        return new Response("Invalid password", { status: 403 });
      }
      if (url.pathname === "/logout" && request.method === "POST") {
        await destroyAdminSession(request, env);
        return new Response(null, {
          status: 302,
          headers: {
            Location: "/login",
            "Set-Cookie": "admin_session=deleted; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"
          }
        });
      }
      if (url.pathname === "/" && request.method === "GET") {
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/guiaddinfo" && request.method === "GET") {
        const clientIP = getClientIP(request);
        if (clientIP && clientIP !== "80.233.252.90") {
          return new Response("Forbidden", { status: 403 });
        }
        const users = await listAll();
        const rows = users.length === 0 ? "<i>V\u0113l nav licen\u010Du.</i>" : users.map((u) => {
          const uname = escapeHTML(u.user);
          const key = escapeHTML(u.key);
          const reason = escapeHTML(u.reason);
          const hwid = escapeHTML(u.hwid || "\u2014");
          const tier = escapeHTML(u.tier || "Basic");
          const expText = u.expires ? (() => {
            const d = new Date(u.expires * 1e3);
            const iso = d.toISOString().replace("T", " ");
            return iso.substring(0, 16);
          })() : "Bez termi\u0146a";
          const expEsc = escapeHTML(expText);
          return `
<li class="row">
  <div class="left">
    <div class="name">${uname}</div>
    <div class="meta">
      ${key}
      ${u.revoked ? `<span class="revoked">[ATCELTA: ${reason}]</span>` : ""}
      <span class="expiry">[Der\u012Bga l\u012Bdz: ${expEsc}]</span>
      <span class="expiry">[Tier: ${tier}]</span>
    </div>
  </div>
  <div class="right">
    <div class="hwid">(HWID: ${hwid})</div>

    <form method="POST" action="/wtier" class="inline" onsubmit="return confirmAction('Set tier for: ${uname}?')">
      <input type="hidden" name="key" value="${uname}">
      <select name="tier" aria-label="Tier for ${uname}">
        <option value="Basic" ${tier === "Basic" ? "selected" : ""}>Basic</option>
        <option value="Basic+" ${tier === "Basic+" ? "selected" : ""}>Basic+</option>
        <option value="Pro" ${tier === "Pro" ? "selected" : ""}>Pro</option>
        <option value="Premium" ${tier === "Premium" ? "selected" : ""}>Premium</option>
      </select>
      <button class="btn" type="submit">Set Tier</button>
    </form>

    <form method="POST" action="/revoke" class="inline" onsubmit="return confirmAction('Atcelt licenci: ${uname}?')">
      <input type="hidden" name="username" value="${uname}">
      <input name="reason" placeholder="Iemesls" required>
      <button class="btn">Atcelt</button>
    </form>
    <form method="POST" action="/unrevoke" class="inline" onsubmit="return confirmAction('Atjaunot licenci: ${uname}?')">
      <input type="hidden" name="username" value="${uname}">
      <button class="btn">Atjaunot</button>
    </form>
    <form method="POST" action="/setexpire" class="inline" onsubmit="return confirmAction('Main\u012Bt termi\u0146u: ${uname}?')">
      <input type="hidden" name="username" value="${uname}">
      <input name="days" placeholder="Dienas (0 = lifetime)" style="width:110px">
      <button class="btn">Termi\u0146\u0161</button>
    </form>
    <form method="POST" action="/delete" class="inline" onsubmit="return confirmAction('Dz\u0113st licenci: ${uname}? Tas nevar tikt atsaukts!')">
      <input type="hidden" name="username" value="${uname}">
      <button class="btn danger">Dz\u0113st</button>
    </form>
  </div>
</li>`;
        }).join("");
        let storedOpenAI = env.OPENAI_API_KEY || null;
        try {
          if (!storedOpenAI && env.CONFIG_KV) {
            const maybe = await env.CONFIG_KV.get("OPENAI_API_KEY");
            if (maybe) storedOpenAI = maybe;
          }
        } catch (e) {
        }
        const maskedKey = maskKey(storedOpenAI);
        const html = `<!doctype html>
<html lang="lv">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Licences p\u0101rvaldnieks</title>
  <style>
    :root{
      --bg:#0b0f14;
      --panel:#0f1720;
      --muted:#97a0b3;
      --text:#e6eef6;
      --accent:#6ee7b7;
      --danger:#ff6161;
      --glass: rgba(255,255,255,0.03);
      --radius:14px;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      min-height:100vh;
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      color:var(--text);
      background:
        radial-gradient(1200px 600px at 10% 10%, rgba(110,231,183,0.06), transparent 10%),
        radial-gradient(900px 400px at 90% 80%, rgba(99,102,241,0.04), transparent 10%),
        var(--bg);
      padding:32px;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
    }
    .container{max-width:1000px;margin:0 auto;}
    header{display:flex;align-items:center;gap:12px;margin-bottom:20px;}
    h1{margin:0;font-size:20px}
    p.lead{margin:0;color:var(--muted);font-size:13px}
    .card{
      background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border-radius:var(--radius);
      padding:18px;
      box-shadow: 0 6px 20px rgba(2,6,23,0.6);
      border:1px solid rgba(255,255,255,0.03);
      margin-bottom:18px;
    }
    form.grid{display:grid;grid-template-columns:150px 1fr;gap:10px;align-items:center;}
    label{color:var(--muted);font-size:13px}
    input[type="text"], input[type="search"], input[name="key"], input[name="username"], input[name="reason"], input[name="days"], input[name="custom_days"]{
      background:var(--glass);
      border:1px solid rgba(255,255,255,0.04);
      padding:8px 10px;
      border-radius:8px;
      color:var(--text);
      width:100%;
      outline:none;
    }
    select{
      background:var(--glass);
      border:1px solid rgba(255,255,255,0.04);
      padding:8px 10px;
      border-radius:8px;
      color:var(--text);
      outline:none;
    }
    .actions{display:flex;gap:8px;align-items:center}
    button{
      background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
      border:1px solid rgba(255,255,255,0.06);
      padding:8px 12px;
      border-radius:10px;
      color:var(--text);
      cursor:pointer;
      font-weight:600;
    }
    button.btn{padding:7px 10px}
    button.danger{background:transparent;color:var(--danger);border:1px solid rgba(255,97,97,0.12)}
    .generate{display:inline-flex;gap:8px;align-items:center}
    hr{border:none;border-top:1px solid rgba(255,255,255,0.03);margin:18px 0}
    h3{margin:0 0 8px 0}
    ul{list-style:none;padding:0;margin:0}
    .row{display:flex;justify-content:space-between;align-items:center;padding:10px;border-radius:8px;margin-bottom:8px;background:transparent}
    .row .left{display:flex;flex-direction:column}
    .name{font-weight:700}
    .meta{color:var(--muted);font-size:13px;margin-top:4px}
    .revoked{color:var(--danger);font-weight:700;margin-left:8px}
    .expiry{margin-left:8px;color:var(--muted);}
    .right{display:flex;align-items:center;gap:8px}
    .inline{display:inline-flex;gap:8px;align-items:center;margin:0}
    .hwid{color:var(--muted);font-size:13px;margin-right:6px}
    .big-danger{background:linear-gradient(180deg, rgba(255,97,97,0.12), rgba(255,97,97,0.05));color:#fff;border:none;padding:10px 14px;border-radius:10px}
    footer{color:var(--muted);font-size:12px;margin-top:8px}
    @media (max-width:720px){
      form.grid{grid-template-columns:1fr;gap:8px}
      .right{flex-direction:column;align-items:flex-end}
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Licences p\u0101rvaldnieks (Admin)</h1>
        <p class="lead"></p>
      </div>
    </header>

    <div class="card">
      <form method="POST" action="/guiaddinfo" class="grid" onsubmit="return validateAdd()">
        <label>Lietot\u0101jv\u0101rds</label>
        <input name="username" id="username" required>

        <label>Licences atsl\u0113ga</label>
        <div class="generate">
          <input name="key" id="key" required>
          <button type="button" onclick="document.getElementById('key').value = gen()">\u0122ener\u0113t</button>
        </div>

        <label>Der\u012Bguma termi\u0146\u0161</label>
        <div class="generate">
          <select name="duration" id="duration">
            <option value="1d">1 diena</option>
            <option value="3d">3 dienas</option>
            <option value="5d">5 dienas</option>
            <option value="custom">Custom</option>
            <option value="lifetime">Lifetime</option>
          </select>
          <input name="custom_days" id="custom_days" placeholder="Dienas (custom)" style="max-width:140px">
        </div>

        <div></div>
        <div class="actions">
          <button type="submit">Pievienot</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h3>Eso\u0161\u0101s licences</h3>
      <ul id="list">${rows}</ul>
    </div>

    <div class="card">
      <h3>OpenAI API key</h3>
      <p style="color:#97a0b3">Currently: <strong>${escapeHTML(
          maskedKey
        )}</strong></p>
      <form method="POST" action="/set_openai_key" onsubmit="return confirm('Store/replace OpenAI API key?')">
        <input name="openai_key" placeholder="sk-... (enter to set/replace)" style="width:320px;padding:8px">
        <button type="submit" style="margin-left:8px">Save</button>
      </form>
    </div>

    <div class="card">
      <form method="POST" action="/deleteall" onsubmit="return confirmAction('Dz\u0113st VISAS licences? Tas nevar tikt atsaukts!')">
        <button class="big-danger">Dz\u0113st visas licences</button>
      </form>
    </div>

    <footer>2025</footer>
  </div>

  <script>
    function gen(){
      const c="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
      const p=()=>Array.from({length:6},()=>c[Math.floor(Math.random()*c.length)]).join("");
      return Array(6).fill(0).map(p).join("-");
    }

    function confirmAction(msg){return confirm(msg);}
    function validateAdd(){
      const u = document.getElementById('username').value.trim();
      const k = document.getElementById('key').value.trim();
      if(!u || !k){
        alert('L\u016Bdzu ievadiet lietot\u0101jv\u0101rdu un licences atsl\u0113gu.');
        return false;
      }
      return true;
    }
  <\/script>
</body>
</html>`;
        return new Response(html, { headers: { "Content-Type": "text/html" } });
      }
      if (url.pathname === "/guiaddinfo" && request.method === "POST") {
        const clientIP = getClientIP(request);
        if (clientIP !== "80.233.252.90")
          return new Response("Forbidden", { status: 403 });
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const u = f.get("username");
        const k = f.get("key");
        const duration = f.get("duration");
        const customDays = f.get("custom_days");
        let expires = null;
        if (duration && duration !== "lifetime") {
          let days = 0;
          if (duration === "1d") days = 1;
          else if (duration === "3d") days = 3;
          else if (duration === "5d") days = 5;
          else if (duration === "custom") {
            const parsed = parseInt(customDays || "0", 10);
            if (Number.isFinite(parsed) && parsed > 0) days = parsed;
          }
          if (days > 0) {
            expires = Math.floor(Date.now() / 1e3) + days * 24 * 3600;
          }
        }
        if (u && k) {
          await env.LICENSES_KV.put(
            u,
            JSON.stringify({
              key: k,
              revoked: false,
              reason: null,
              hwid: null,
              expires,
              tier: "Basic"
            })
          );
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/set_openai_key" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const key = f.get("openai_key");
        if (!env.CONFIG_KV) {
          return new Response(
            "CONFIG_KV binding missing. Cannot store OpenAI key.",
            { status: 500 }
          );
        }
        try {
          if (!key) {
            await env.CONFIG_KV.delete("OPENAI_API_KEY");
          } else {
            await env.CONFIG_KV.put("OPENAI_API_KEY", key);
          }
        } catch (e) {
          return new Response(
            "Failed to persist OpenAI key: " + String(e),
            { status: 500 }
          );
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/setexpire" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const u = f.get("username");
        const daysStr = f.get("days");
        if (u) {
          const d = await getRec(u) || {};
          let days = parseInt(daysStr || "0", 10);
          if (!Number.isFinite(days)) days = 0;
          if (days <= 0) d.expires = null;
          else
            d.expires = Math.floor(Date.now() / 1e3) + days * 24 * 3600;
          await env.LICENSES_KV.put(u, JSON.stringify(d));
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/revoke" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const u = f.get("username");
        const r = f.get("reason");
        if (u) {
          const d = await getRec(u) || {};
          d.revoked = true;
          d.reason = r || "Nav nor\u0101d\u012Bts iemesls";
          await env.LICENSES_KV.put(u, JSON.stringify(d));
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/unrevoke" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const u = f.get("username");
        if (u) {
          const d = await getRec(u) || {};
          d.revoked = false;
          d.reason = null;
          await env.LICENSES_KV.put(u, JSON.stringify(d));
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/delete" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        const f = await request.formData();
        const u = f.get("username");
        if (u) {
          try {
            const exists = await env.LICENSES_KV.get(u);
            if (exists !== null) {
              await env.LICENSES_KV.delete(u);
            }
          } catch (e) {
          }
        }
        return absRedirect("/guiaddinfo");
      }
      if (url.pathname === "/deleteall" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        let cursor;
        try {
          do {
            const page = await env.LICENSES_KV.list({ cursor });
            for (const k of page.keys) {
              try {
                await env.LICENSES_KV.delete(k.name);
              } catch (e) {
              }
            }
            cursor = page.cursor;
          } while (cursor);
        } catch (e) {
        }
        return absRedirect("/guiaddinfo");
      }
      if (request.method === "GET" && url.pathname === "/challenge") {
        const user = url.searchParams.get("user") || url.searchParams.get("username");
        const key = url.searchParams.get("key");
        if (!user || !key)
          return json(
            { error: "Tr\u016Bkst lietot\u0101jv\u0101rda vai atsl\u0113gas" },
            { status: 400 }
          );
        const d = await getRec(user);
        if (!d)
          return obfJson(
            { valid: false, message: "Nepaz\u012Bstams lietot\u0101js" },
            { status: 404 }
          );
        if (d.key !== key)
          return obfJson(
            { valid: false, message: "Neder\u012Bga licences atsl\u0113ga" },
            { status: 403 }
          );
        if (d.revoked)
          return obfJson(
            {
              valid: false,
              revoked: true,
              reason: d.reason,
              message: `Licence atcelta: ${d.reason}`
            },
            { status: 403 }
          );
        if (d.expires && Date.now() / 1e3 > d.expires)
          return obfJson(
            { valid: false, expired: true, message: "Licence beigusies." },
            { status: 403 }
          );
        const nonce = genRandomBase64(32);
        await storeNonce(nonce, user, 300);
        return obfJson({ nonce });
      }
      if (url.pathname === "/trial" && request.method === "GET") {
        const user = url.searchParams.get("user") || url.searchParams.get("username");
        if (!user)
          return obfJson({ error: "missing_user" }, { status: 400 });
        const rec = await getRec(user);
        if (!rec)
          return obfJson(
            { valid: false, message: "unknown_user" },
            { status: 404 }
          );
        const now = Math.floor(Date.now() / 1e3);
        let trial = await trialGet(user);
        if (!trial) {
          trial = {
            start: now,
            expires: now + 120 * 60
            // 120 minutes
          };
          await trialPut(user, trial);
        }
        const remaining = trial.expires - now;
        if (remaining <= 0) {
          return obfJson(
            {
              valid: false,
              trial: "expired",
              message: "Your free trial has ended."
            },
            { status: 200 }
          );
        }
        return obfJson(
          {
            valid: true,
            trial: "active",
            remaining_seconds: remaining
          },
          { status: 200 }
        );
      }
      if (url.pathname === "/trial" && request.method === "POST") {
        let body = {};
        try {
          body = await request.json();
        } catch (_) {
        }
        const user = body.user || body.username;
        if (!user)
          return obfJson({ error: "missing_user" }, { status: 400 });
        const rec = await getRec(user);
        if (!rec)
          return obfJson(
            { valid: false, message: "unknown_user" },
            { status: 404 }
          );
        const now = Math.floor(Date.now() / 1e3);
        let trial = await trialGet(user);
        if (!trial) {
          return obfJson(
            {
              warning: "Trial_Not_Started",
              message: "Trial not started. Use GET /trial to initialize your free trial."
            },
            { status: 400 }
          );
        }
        const remaining = trial.expires - now;
        if (remaining <= 0) {
          await logTamper(user);
          return obfJson(
            {
              alert: true,
              message: "Suspicious attempt to reset/extend an expired trial detected. This action is denied and logged."
            },
            { status: 403 }
          );
        }
        if (body.requested_minutes) {
          const requestedSeconds = parseInt(
            body.requested_minutes,
            10
          ) * 60;
          if (!Number.isFinite(requestedSeconds)) {
            return obfJson(
              { error: "invalid_requested_minutes" },
              { status: 400 }
            );
          }
          const requestedExpiry = now + requestedSeconds;
          if (requestedExpiry > trial.expires) {
            await logTamper(user);
            return obfJson(
              {
                alert: true,
                message: "Suspicious attempt to extend the trial detected. Extension denied and logged."
              },
              { status: 403 }
            );
          }
          return obfJson(
            {
              ok: false,
              message: "Manual trial modification is not allowed."
            },
            { status: 403 }
          );
        }
        return obfJson(
          {
            valid: true,
            trial: remaining > 0 ? "active" : "expired",
            remaining_seconds: remaining > 0 ? remaining : 0,
            message: "No modification performed."
          },
          { status: 200 }
        );
      }
      if (url.pathname === "/wtier" && request.method === "POST") {
        const err = await requireAdmin(request, env);
        if (err) return err;
        let body = {};
        const ct = (request.headers.get("content-type") || "").toLowerCase();
        if (ct.includes("application/json")) {
          try {
            body = await request.json();
          } catch (e) {
            body = {};
          }
        } else {
          try {
            const f = await request.formData();
            body.key = f.get("key") || f.get("license") || null;
            body.tier = f.get("tier") || null;
          } catch (e) {
            body = {};
          }
        }
        const maybeKeyOrUser = body.key;
        const tier = body.tier;
        if (!maybeKeyOrUser || !tier) {
          return obfJson(
            { success: false, message: "Missing required fields: key, tier" },
            { status: 400 }
          );
        }
        if (!ALLOWED_TIERS.includes(tier)) {
          return obfJson(
            {
              success: false,
              message: "Invalid tier. Allowed: Basic, Basic+, Pro, Premium"
            },
            { status: 400 }
          );
        }
        const found = await findLicenseByKeyOrUser(maybeKeyOrUser);
        if (!found) {
          return obfJson(
            { success: false, message: "Unknown license key or username." },
            { status: 404 }
          );
        }
        const { username, record } = found;
        record.tier = tier;
        try {
          await env.LICENSES_KV.put(username, JSON.stringify(record));
        } catch (e) {
          return obfJson(
            { success: false, message: "Failed to persist tier update." },
            { status: 500 }
          );
        }
        return obfJson(
          {
            success: true,
            username,
            key: record.key ?? null,
            tier,
            message: "Tier updated successfully."
          },
          { status: 200 }
        );
      }
      if (url.pathname === "/tier" && request.method === "GET") {
        const maybeKeyOrUser = url.searchParams.get("key") || url.searchParams.get("license") || url.searchParams.get("user") || url.searchParams.get("username");
        if (!maybeKeyOrUser) {
          return obfJson(
            { success: false, message: "Missing required fields: key or user" },
            { status: 400 }
          );
        }
        const found = await findLicenseByKeyOrUser(maybeKeyOrUser);
        if (!found) {
          return obfJson(
            { success: false, message: "Unknown license key or username." },
            { status: 404 }
          );
        }
        const { username, record } = found;
        return obfJson(
          { success: true, username, tier: record.tier || "Basic" },
          { status: 200 }
        );
      }
      if (url.pathname === "/msg" && request.method === "POST") {
        let body = {};
        try {
          body = await request.json();
        } catch (e) {
          return obfJson(
            { success: false, message: "Invalid JSON body" },
            { status: 400 }
          );
        }
        const maybeKeyOrUser = body.key;
        const message = body.message;
        const imageBase64 = body.image_base64 || body.image_b64 || null;
        const imageFileIdFromClient = body.fileId || body.file_id || null;
        if (!maybeKeyOrUser || !message) {
          return obfJson(
            { success: false, message: "Missing required fields: key, message" },
            { status: 400 }
          );
        }
        const found = await findLicenseByKeyOrUser(maybeKeyOrUser);
        if (!found) {
          return obfJson(
            { success: false, message: "Unknown license key or username." },
            { status: 404 }
          );
        }
        const { username, record: lic } = found;
        if (lic.revoked) {
          return obfJson(
            {
              success: false,
              message: `License revoked: ${lic.reason || "No reason"}`
            },
            { status: 403 }
          );
        }
        const now = Math.floor(Date.now() / 1e3);
        if (lic.expires && now > lic.expires) {
          return obfJson(
            { success: false, message: "License expired" },
            { status: 403 }
          );
        }
        const tier = lic.tier || "Basic";
        const model = tier === "Basic+" ? "gpt-4o-mini" : tier === "Pro" ? "gpt-5-nano" : tier === "Premium" ? "gpt-5.1-nano" : null;
        let openaiError = null;
        let result = null;
        let clailaImageFileId = imageFileIdFromClient;
        if (!clailaImageFileId && imageBase64) {
          try {
            const up = await clailaUploadImageFromBase64(
              imageBase64,
              body.filename || "image.jpg",
              body.mimetype || "image/jpeg"
            );
            clailaImageFileId = up.fileId;
          } catch (e) {
            openaiError = {
              message: "Claila image upload failed",
              error: String(e)
            };
          }
        }
        let OPENAI_API_KEY = env.OPENAI_API_KEY || null;
        try {
          if (!OPENAI_API_KEY && env.CONFIG_KV) {
            const maybe = await env.CONFIG_KV.get("OPENAI_API_KEY");
            if (maybe) OPENAI_API_KEY = maybe;
          }
        } catch (e) {
        }
        if (!model) {
          openaiError = { message: "Tier does not allow OpenAI chat" };
        } else if (!OPENAI_API_KEY) {
          openaiError = { message: "Server missing OpenAI API key" };
        } else {
          try {
            const r = await fetch(
              "https://api.openai.com/v1/chat/completions",
              {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${OPENAI_API_KEY}`,
                  "Content-Type": "application/json"
                },
                body: JSON.stringify({
                  model,
                  messages: [{ role: "user", content: message }],
                  max_tokens: 800
                })
              }
            );
            const text = await r.text();
            let responseAI;
            try {
              responseAI = JSON.parse(text);
            } catch {
              responseAI = { raw: text };
            }
            if (!r.ok) {
              openaiError = {
                message: "OpenAI returned an error",
                status: r.status,
                statusText: r.statusText,
                headers: Object.fromEntries(r.headers.entries()),
                body: responseAI,
                raw: text
              };
            } else {
              const reply = responseAI?.choices?.[0]?.message?.content ?? responseAI?.choices?.[0]?.text ?? responseAI?.output ?? null;
              result = {
                provider: "openai",
                model,
                reply: reply ?? "(no text)",
                raw: responseAI,
                reason: null
              };
            }
          } catch (e) {
            openaiError = {
              message: "Failed to reach OpenAI",
              error: String(e)
            };
          }
        }
        if (!result) {
          const fallback = await clailaFallbackChat(
            message,
            openaiError ? "openai_unavailable" : "tier_not_allowed",
            clailaImageFileId
          );
          if (fallback.error) {
            return obfJson(
              {
                success: false,
                message: "Claila fallback provider failed",
                openai_error: openaiError,
                fallback_error: fallback.error
              },
              { status: 502 }
            );
          }
          result = fallback;
        }
        return obfJson(
          {
            success: true,
            username,
            tier,
            provider: result.provider,
            model_used: result.model,
            reply: result.reply,
            raw: result.raw,
            openai_error: openaiError,
            fallback_reason: result.reason
          },
          { status: 200 }
        );
      }
      if (request.method === "GET" && url.pathname === "/validate") {
        const user = url.searchParams.get("user") || url.searchParams.get("username");
        const key = url.searchParams.get("key");
        const qHWID = url.searchParams.get("hwid") || null;
        const nonce = url.searchParams.get("nonce");
        const signature = url.searchParams.get("signature");
        if (!user || !key)
          return json(
            { error: "Tr\u016Bkst lietot\u0101jv\u0101rda vai atsl\u0113gas" },
            { status: 400 }
          );
        const d = await getRec(user);
        if (!d)
          return obfJson(
            { valid: false, message: "Nepaz\u012Bstams lietot\u0101js" },
            { status: 404 }
          );
        if (d.key !== key)
          return obfJson(
            { valid: false, message: "Neder\u012Bga licences atsl\u0113ga" },
            { status: 403 }
          );
        if (d.revoked)
          return obfJson(
            {
              valid: false,
              revoked: true,
              reason: d.reason,
              message: `Licence atcelta: ${d.reason}`
            },
            { status: 403 }
          );
        if (d.expires && Date.now() / 1e3 > d.expires) {
          return obfJson(
            { valid: false, expired: true, message: "Licence beigusies." },
            { status: 403 }
          );
        }
        if (!nonce || !signature || !qHWID) {
          return obfJson(
            { valid: false, message: "Nepiecie\u0161ams nonce, signature un hwid." },
            { status: 400 }
          );
        }
        const nonceOwner = await lookupNonce(nonce);
        if (!nonceOwner || nonceOwner !== user) {
          return obfJson(
            { valid: false, message: "Neder\u012Bgs vai beidzies nonce." },
            { status: 403 }
          );
        }
        const provided = parseSignature(signature);
        if (!provided)
          return obfJson(
            { valid: false, message: "Nepareizs paraksta form\u0101ts." },
            { status: 400 }
          );
        const enc = new TextEncoder();
        const messageBytes = enc.encode(`${nonce}${qHWID}`);
        const serverSig = await computeHMAC(d.key, messageBytes);
        if (!bytesEqual(serverSig, provided)) {
          return obfJson(
            { valid: false, message: "Paraksts neder." },
            { status: 403 }
          );
        }
        try {
          if (env.RATE_KV) {
            const hv = `validate:${qHWID}`;
            const count = await kvIncrement(env.RATE_KV, hv, 60);
            if (count > 10) {
              return obfJson(
                {
                  valid: false,
                  message: "P\u0101rsniegts validate piepras\u012Bjumu limits \u0161im HWID (10/min)."
                },
                { status: 429 }
              );
            }
          }
        } catch (e) {
        }
        if (!d.hwid)
          return obfJson(
            {
              valid: false,
              message: "HWID nav saist\u012Bts. Pirmajai reizei nos\u016Btiet POST { user,key,hwid,nonce,signature }."
            },
            { status: 400 }
          );
        if (qHWID && d.hwid !== qHWID)
          return obfJson(
            { valid: false, message: "HWID nesakr\u012Bt" },
            { status: 403 }
          );
        return obfJson({
          valid: true,
          user,
          hwid: d.hwid,
          expires: d.expires ?? null,
          message: "Licence der\u012Bga."
        });
      }
      if (request.method === "POST" && (url.pathname === "/validate" || url.pathname === "/")) {
        let body = {};
        try {
          body = await request.json();
        } catch (_) {
        }
        const user = body.user || body.username;
        const key = body.key;
        const hwid = body.hwid || null;
        const nonce = body.nonce;
        const signature = body.signature;
        if (!user || !key)
          return json(
            { error: "Tr\u016Bkst lietot\u0101jv\u0101rda vai atsl\u0113gas" },
            { status: 400 }
          );
        const d = await getRec(user);
        if (!d)
          return obfJson(
            { valid: false, message: "Nepaz\u012Bstams lietot\u0101js" },
            { status: 404 }
          );
        if (d.key !== key)
          return obfJson(
            { valid: false, message: "Neder\u012Bga licences atsl\u0113ga" },
            { status: 403 }
          );
        if (d.revoked)
          return obfJson(
            {
              valid: false,
              revoked: true,
              reason: d.reason,
              message: `Licence atcelta: ${d.reason}`
            },
            { status: 403 }
          );
        if (d.expires && Date.now() / 1e3 > d.expires) {
          return obfJson(
            { valid: false, expired: true, message: "Licence beigusies." },
            { status: 403 }
          );
        }
        if (!nonce || !signature || !hwid) {
          return obfJson(
            { valid: false, message: "Nepiecie\u0161ams nonce, signature un hwid." },
            { status: 400 }
          );
        }
        const nonceOwner = await lookupNonce(nonce);
        if (!nonceOwner || nonceOwner !== user) {
          return obfJson(
            { valid: false, message: "Neder\u012Bgs vai beidzies nonce." },
            { status: 403 }
          );
        }
        const provided = parseSignature(signature);
        if (!provided)
          return obfJson(
            { valid: false, message: "Nepareizs paraksta form\u0101ts." },
            { status: 400 }
          );
        const enc = new TextEncoder();
        const messageBytes = enc.encode(`${nonce}${hwid}`);
        const serverSig = await computeHMAC(d.key, messageBytes);
        if (!bytesEqual(serverSig, provided)) {
          return obfJson(
            { valid: false, message: "Paraksts neder." },
            { status: 403 }
          );
        }
        try {
          if (env.RATE_KV) {
            const hv = `validate:${hwid}`;
            const count = await kvIncrement(env.RATE_KV, hv, 60);
            if (count > 10) {
              return obfJson(
                {
                  valid: false,
                  message: "P\u0101rsniegts validate piepras\u012Bjumu limits \u0161im HWID (10/min)."
                },
                { status: 429 }
              );
            }
          }
        } catch (e) {
        }
        if (!d.hwid) {
          try {
            if (env.RATE_KV) {
              const bindKey = `bind:${user}`;
              const attempts = await kvIncrement(
                env.RATE_KV,
                bindKey,
                24 * 3600
              );
              if (attempts > 3) {
                return obfJson(
                  {
                    valid: false,
                    message: "P\u0101rsniegts HWID sasaistes m\u0113\u0123in\u0101jumu limits (3/24h)."
                  },
                  { status: 429 }
                );
              }
            }
          } catch (e) {
          }
          d.hwid = hwid;
          await env.LICENSES_KV.put(user, JSON.stringify(d));
        } else if (hwid && hwid !== d.hwid) {
          return obfJson(
            { valid: false, message: "HWID nesakr\u012Bt" },
            { status: 403 }
          );
        }
        return obfJson({
          valid: true,
          user,
          hwid: d.hwid,
          expires: d.expires ?? null,
          message: "Licence der\u012Bga."
        });
      }
      return new Response("Nav atrasts", { status: 404 });
    } catch (err) {
      console.error("Worker exception:", err?.stack || err);
      return new Response("Iek\u0161\u0113ja k\u013C\u016Bda", { status: 500 });
    }
  }
};
export {
  index_default as default
};
//# sourceMappingURL=index.js.map
