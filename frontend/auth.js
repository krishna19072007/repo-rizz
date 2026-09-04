// ============================================================
// Normal-user authentication (Supabase GitHub OAuth / email).
//
// COMPLETELY SEPARATE from Rizz Master admin auth. The admin
// session is a backend HttpOnly cookie verified server-side
// (admin_auth.py); this module is Supabase-managed user auth:
// the browser talks to Supabase Auth directly with the public
// anon key. No Supabase secret ever appears in this file.
//
// Session persistence is handled by supabase-js itself (the
// library stores the session where it sees fit); we never
// hand-roll "authentication proof" into localStorage.
// ============================================================
(function () {
  "use strict";

  // Publishable config (anon key only) is served by the backend.
  const configPromise = fetch("/api/config/supabase", { credentials: "same-origin" })
    .then((r) => (r.ok ? r.json() : { enabled: false, url: "", anonKey: "" }))
    .catch(() => ({ enabled: false, url: "", anonKey: "" }));

  let client = null;
  let cfg = null;
  let clientPromise = null;

  // Single-flight: concurrent early calls (boot listener + page gate) must
  // not each create a client — GoTrue warns on duplicate instances sharing
  // the same storage key.
  function ensureClient() {
    if (client) return Promise.resolve(client);
    if (!clientPromise) {
      clientPromise = (async () => {
        cfg = await configPromise;
        if (!cfg.enabled || typeof window.supabase === "undefined") return null;
        client = window.supabase.createClient(cfg.url, cfg.anonKey);
        return client;
      })();
    }
    return clientPromise;
  }

  const RR_AUTH = {
    config: () => configPromise,
    client: ensureClient,
    // Initial-letter avatar fallback (shared with the /login account panel).
    initialBadge: makeInitialBadge,

    async getUser() {
      const c = await ensureClient();
      if (!c) return null;
      try {
        const { data } = await c.auth.getUser();
        return data.user || null;
      } catch (e) {
        return null; // no valid session — treat as logged out
      }
    },

    // Authorization header carrying the real access token, or null.
    async authHeaders() {
      const c = await ensureClient();
      if (!c) return null;
      try {
        const { data } = await c.auth.getSession();
        return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : null;
      } catch (e) {
        return null;
      }
    },

    async signInWithGitHub() {
      const c = await ensureClient();
      if (!c) return { error: { message: "Supabase auth is not configured yet." } };
      try {
        return await c.auth.signInWithOAuth({
          provider: "github",
          options: { redirectTo: window.location.origin },
        });
      } catch (e) {
        return { error: { message: e.message || "GitHub sign-in failed." } };
      }
    },

    async signInWithEmail(email, password) {
      const c = await ensureClient();
      if (!c) return { error: { message: "Supabase auth is not configured yet." } };
      try {
        return await c.auth.signInWithPassword({ email, password });
      } catch (e) {
        return { error: { message: e.message || "Sign-in failed." } };
      }
    },

    async signUpWithEmail(email, password) {
      const c = await ensureClient();
      if (!c) return { error: { message: "Supabase auth is not configured yet." } };
      try {
        return await c.auth.signUp({ email, password });
      } catch (e) {
        return { error: { message: e.message || "Sign-up failed." } };
      }
    },

    async signOut() {
      const c = await ensureClient();
      if (c) {
        try { await c.auth.signOut(); } catch (e) { /* session already gone */ }
      }
    },

    // session: the signed-in Supabase user object, or null
    async onAuthChange(callback) {
      const c = await ensureClient();
      if (!c) return;
      c.auth.onAuthStateChange(() => {
        // Re-read the user on every event (INITIAL_SESSION, SIGNED_IN,
        // TOKEN_REFRESHED, SIGNED_OUT...) so the UI always matches reality.
        RR_AUTH.getUser().then(callback);
      });
      RR_AUTH.getUser().then(callback);
    },

    // Gate for protected actions (analyze, history). Resolves true when the
    // action may proceed: the user is signed in, OR the server has no user
    // accounts configured at all (legacy anonymous mode). Otherwise shows
    // the LOGIN TO CONTINUE prompt and resolves false.
    async gate(nextPath) {
      const c = await ensureClient();
      if (!c) return true;
      const user = await RR_AUTH.getUser();
      if (user) return true;
      promptLogin(nextPath);
      return false;
    },

    // Navigate to an analysis URL only when analysis is permitted; otherwise
    // the gate prompt appears (its SIGN IN / CREATE ACCOUNT buttons carry
    // the URL as ?next= so the run resumes after login).
    async go(url) {
      if (await RR_AUTH.gate(url)) window.location.assign(url);
    },
  };

  window.RR_AUTH = RR_AUTH;

  // ---- helpers used by the /login and /signup pages --------------
  function safeNext() {
    const next = new URLSearchParams(window.location.search).get("next") || "/";
    return next.startsWith("/") && !next.startsWith("//") ? next : "/";
  }

  RR_AUTH.safeNext = safeNext;

  // ------------------------------------------------------------------
  // LOGIN TO CONTINUE prompt (analysis gate)
  // ------------------------------------------------------------------
  function promptLogin(nextPath) {
    const target = nextPath && nextPath.startsWith("/") && !nextPath.startsWith("//")
      ? encodeURIComponent(nextPath)
      : encodeURIComponent(window.location.pathname + window.location.search);
    const existing = document.getElementById("rr-auth-modal");
    if (existing) existing.remove();

    const overlay = document.createElement("div");
    overlay.id = "rr-auth-modal";
    overlay.className = "fixed inset-0 z-[300] flex items-center justify-center p-4";
    overlay.innerHTML = `
      <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" data-rr-close></div>
      <div class="relative w-full max-w-md rounded-2xl border border-border bg-surface shadow-2xl p-8 text-center z-10"
           style="background: #0f1115;">
        <button data-rr-close class="absolute top-3 right-3 p-1.5 rounded-full text-gray-500 hover:text-white hover:bg-surface-elevated transition-colors" aria-label="Close">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-lime/20 bg-lime/5 text-lime text-xs font-mono tracking-wider uppercase mb-5">
          <span class="w-1.5 h-1.5 rounded-full bg-lime animate-pulse"></span> Access Required
        </div>
        <h2 class="text-2xl font-extrabold tracking-tight text-white mb-2">LOGIN TO <span class="text-lime">CONTINUE</span></h2>
        <p class="text-sm text-gray-400 leading-relaxed mb-8">Create an account or sign in to analyze repositories.</p>
        <div class="space-y-3">
          <a href="/login?next=${target}"
             class="block w-full px-4 py-3 rounded-xl bg-lime text-black text-xs font-mono font-bold tracking-widest hover:scale-[1.01] transition-transform">SIGN IN</a>
          <a href="/signup?next=${target}"
             class="block w-full px-4 py-3 rounded-xl border border-border text-gray-300 text-xs font-mono font-bold tracking-widest hover:border-lime/40 hover:text-white transition-colors">CREATE ACCOUNT</a>
        </div>
      </div>`;
    overlay.querySelectorAll("[data-rr-close]").forEach((el) => {
      el.addEventListener("click", () => overlay.remove());
    });
    document.addEventListener("keydown", function onEsc(e) {
      if (e.key === "Escape" && document.getElementById("rr-auth-modal")) {
        overlay.remove();
        document.removeEventListener("keydown", onEsc);
      }
    });
    document.body.appendChild(overlay);
  }

  // ------------------------------------------------------------------
  // Navbar auth zone: SIGN IN / SIGN UP (logged out) or account menu
  // ------------------------------------------------------------------
  function displayName(user) {
    const meta = user.user_metadata || {};
    return meta.user_name || meta.name || (user.email || "").split("@")[0] || "Account";
  }

  function renderNavAuth(user) {
    // /login and /signup render their own account/forms UI in the page.
    const path = window.location.pathname;
    if (path === "/login" || path === "/signup") return;

    const old = document.getElementById("rr-nav-auth");
    if (old) old.remove();

    // The right-side cluster is the LAST .flex.items-center.gap-3 in the
    // navbar (the brand cluster on the left uses the same classes).
    const slots = document.querySelectorAll("nav .flex.items-center.gap-3");
    const slot = slots.length ? slots[slots.length - 1] : null;
    if (!slot) return;

    const zone = document.createElement("div");
    zone.id = "rr-nav-auth";
    zone.className = "flex items-center gap-1.5 ml-1";

    if (!user) {
      const signIn = document.createElement("a");
      signIn.href = "/login";
      signIn.className = "px-2.5 py-1.5 rounded-lg border border-border text-[10px] font-mono font-bold tracking-widest text-gray-300 hover:text-lime hover:border-lime/40 transition-colors";
      signIn.textContent = "SIGN IN";
      const signUp = document.createElement("a");
      signUp.href = "/signup";
      signUp.className = "px-2.5 py-1.5 rounded-lg bg-lime text-black text-[10px] font-mono font-bold tracking-widest hover:brightness-110 transition-all";
      signUp.textContent = "SIGN UP";
      zone.appendChild(signIn);
      zone.appendChild(signUp);
    } else {
      const meta = user.user_metadata || {};
      const name = displayName(user);
      const avatarUrl = meta.avatar_url || "";

      const control = document.createElement("div");
      control.id = "rr-user-chip";
      control.className = "relative";
      const button = document.createElement("button");
      button.className = "flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-lg border border-border bg-surface hover:border-lime/40 hover:bg-surface-elevated transition-colors cursor-pointer";
      button.setAttribute("aria-haspopup", "true");
      button.title = "Account";
      if (avatarUrl) {
        const img = document.createElement("img");
        img.src = avatarUrl;
        img.alt = "";
        img.className = "w-6 h-6 rounded-full border border-border object-cover";
        img.addEventListener("error", () => { img.replaceWith(RR_AUTH.initialBadge(name, "w-6 h-6 text-[11px]")); }, { once: true });
        button.appendChild(img);
      } else {
        button.appendChild(RR_AUTH.initialBadge(name, "w-6 h-6 text-[11px]"));
      }
      const label = document.createElement("span");
      label.className = "hidden md:inline text-[11px] font-mono text-gray-300 max-w-[110px] truncate";
      label.textContent = name;
      button.appendChild(label);
      button.appendChild(chevronSvg());

      const menu = document.createElement("div");
      menu.className = "hidden absolute right-0 top-[calc(100%+6px)] w-60 rounded-xl border border-border bg-surface shadow-2xl p-2 z-[120]";
      menu.style.background = "#0f1115";
      menu.innerHTML = `
        <div class="px-3 py-2.5 border-b border-border mb-1.5">
          <p class="text-xs font-semibold text-white truncate">${escapeHtml(name)}</p>
          <p class="text-[10px] font-mono text-gray-500 truncate mt-0.5">${escapeHtml(user.email || "")}</p>
        </div>
        <button data-rr-logout class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs font-mono text-coral hover:bg-coral/10 transition-colors cursor-pointer">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>
          LOG OUT
        </button>`;
      menu.addEventListener("click", (e) => {
        if (e.target.closest("[data-rr-logout]")) {
          menu.classList.add("hidden");
          RR_AUTH.signOut();
        }
      });
      button.addEventListener("click", (e) => {
        e.stopPropagation();
        document.querySelectorAll("#rr-user-menu-open").forEach((m) => m.classList.add("hidden"));
        menu.classList.toggle("hidden");
      });
      menu.id = "rr-user-menu-open";
      control.appendChild(button);
      control.appendChild(menu);
      zone.appendChild(control);
    }

    slot.appendChild(zone);
  }

  function chevronSvg() {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "12");
    svg.setAttribute("height", "12");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("class", "text-gray-500");
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", "m6 9 6 6 6-6");
    svg.appendChild(p);
    return svg;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function makeInitialBadge(name, extraClass) {
    const badge = document.createElement("span");
    badge.className = "rounded-full flex items-center justify-center font-bold text-black bg-lime shrink-0 " + (extraClass || "");
    badge.textContent = (name[0] || "?").toUpperCase();
    return badge;
  }

  // Close the account menu on outside click / Escape.
  document.addEventListener("click", (e) => {
    const open = document.getElementById("rr-user-menu-open");
    if (open && !open.parentElement.contains(e.target)) open.classList.add("hidden");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const open = document.getElementById("rr-user-menu-open");
      if (open) open.classList.add("hidden");
    }
  });

  // Boot: the nav zone follows the session on every auth event.
  RR_AUTH.onAuthChange(renderNavAuth);
})();
