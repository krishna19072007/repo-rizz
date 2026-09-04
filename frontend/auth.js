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

  async function ensureClient() {
    if (client) return client;
    cfg = await configPromise;
    if (!cfg.enabled || typeof window.supabase === "undefined") return null;
    client = window.supabase.createClient(cfg.url, cfg.anonKey);
    return client;
  }

  // ---- helpers used by the /login page -----------------------
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
  };

  window.RR_AUTH = RR_AUTH;

  // ---- navbar chip: shows on every page once a user is signed in ---
  // The chip links to /login, which is the account page (profile +
  // logout). It is only rendered for a real session — never on the
  // login page itself, where the account panel takes its place.
  function renderNavChip(user) {
    if (window.location.pathname === "/login") return;
    const old = document.getElementById("rr-user-chip");
    if (old) old.remove();
    if (!user) return;

    // Right cluster of the navbar (same slot GitHub link lives in).
    const slot = document.querySelector("nav .flex.items-center.gap-3");
    if (!slot) return;

    const meta = user.user_metadata || {};
    const name = meta.user_name || meta.name || (user.email || "").split("@")[0] || "Account";
    const avatarUrl = meta.avatar_url || "";

    const chip = document.createElement("a");
    chip.id = "rr-user-chip";
    chip.href = "/login";
    chip.className = "flex items-center gap-2 pl-2 pr-1 py-1 rounded-lg border border-border bg-surface hover:border-lime/40 hover:bg-surface-elevated transition-colors";
    chip.title = "Signed in — open your account";
    if (avatarUrl) {
      const img = document.createElement("img");
      img.src = avatarUrl;
      img.alt = "";
      img.className = "w-7 h-7 rounded-full border border-border object-cover";
      img.addEventListener("error", () => { img.remove(); chip.prepend(RR_AUTH.initialBadge(name, "w-7 h-7 text-[11px]")); }, { once: true });
      chip.appendChild(img);
    } else {
      chip.appendChild(RR_AUTH.initialBadge(name, "w-7 h-7 text-[11px]"));
    }
    const label = document.createElement("span");
    label.className = "hidden sm:inline text-xs font-mono text-gray-300 max-w-[110px] truncate";
    label.textContent = "@" + name;
    chip.appendChild(label);

    slot.insertBefore(chip, slot.firstChild);
  }

  function makeInitialBadge(name, extraClass) {
    const badge = document.createElement("span");
    badge.className = "rounded-full flex items-center justify-center font-bold text-black bg-lime shrink-0 " + (extraClass || "");
    badge.textContent = (name[0] || "?").toUpperCase();
    return badge;
  }

  // Boot: chip appears/updates as soon as the session is known,
  // and stays in sync on sign-in/sign-out/refresh.
  RR_AUTH.onAuthChange(renderNavChip);
})();
