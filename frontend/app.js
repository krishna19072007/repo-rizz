// ============================================================
// Shared Frontend Script for Repo Rizz
// Handles: icons, shared components, navigation, modals, parsing
// ============================================================

// Global GitHub URL parser (usable by inline scripts)
function parseGitHubUrlHelper(input) {
  const trimmed = input.trim();
  const urlRegex = /^(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)(?:\/.*)?$/;
  const shortRegex = /^([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)$/;
  const match = trimmed.match(urlRegex) || trimmed.match(shortRegex);
  if (match) {
    return { owner: match[1], name: match[2].replace(/\.git$/, "") };
  }
  return null;
}

(function initRepoRizz() {
  // ---- 0. Inject shared navbar (replaces any per-page <nav>) ----
  function injectNavbar() {
    const existing = document.querySelector("nav");
    const p = window.location.pathname;

    // Active state derived solely from location.pathname
    const isActive = (href) => {
      if (href === "/") return p === "/";
      return p === href || p.startsWith(href + "/");
    };
    const cls = (href) =>
      "px-4 py-2 rounded-lg text-sm font-medium transition-colors " +
      (isActive(href) ? "text-lime bg-surface-elevated" : "text-gray-400 hover:text-white hover:bg-surface");

    const githubSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>';

    const nav = document.createElement("nav");
    nav.className = "fixed top-0 left-0 right-0 z-50 border-b border-border";
    nav.style.cssText = "background:rgba(7,8,9,0.85);backdrop-filter:blur(12px);";
    nav.innerHTML = `
      <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button id="logo-btn" class="relative w-8 h-8 focus:outline-none focus:ring-2 focus:ring-lime rounded-sm transition-transform hover:scale-105">
            <img src="/static/logo.png" alt="Repo Rizz Logo" class="object-contain w-full h-full">
          </button>
          <a href="/" class="flex items-center">
            <span class="text-lg font-semibold tracking-tight hover:opacity-80 transition-opacity">REPO <span class="text-lime">RIZZ</span></span>
          </a>
        </div>
        <div class="hidden md:flex items-center gap-1">
          <a href="/" class="${cls("/")}">Home</a>
          <a href="/analyze" class="${cls("/analyze")}">Repo's Rizz</a>
          <a href="/compare" class="${cls("/compare")}">Repo Battle</a>
          <a href="/contributors" class="${cls("/contributors")}">Contributors</a>
          <a href="/history" class="${cls("/history")}">History</a>
        </div>
        <div class="flex items-center gap-3">
          <a href="https://github.com/krishna19072007/repo-rizz" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-white text-sm transition-colors flex items-center gap-1">
            ${githubSvg} GitHub
          </a>
        </div>
      </div>`;
    if (existing) existing.replaceWith(nav); else document.body.prepend(nav);
  }

  injectNavbar();

  // ---- 1. Inject shared components ----
  function injectSharedComponents() {
    // Brand Modal
    if (!document.getElementById("brand-modal")) {
      const modal = document.createElement("div");
      modal.id = "brand-modal";
      modal.className = "hidden fixed inset-0 z-[100] flex items-center justify-center p-4";
      modal.innerHTML = `
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm modal-close"></div>
        <div class="relative w-full max-w-md rounded-2xl overflow-hidden border border-border bg-surface shadow-2xl p-10 flex flex-col items-center text-center z-10">
          <button class="absolute top-4 right-4 p-2 rounded-full text-gray-400 hover:text-white hover:bg-surface-elevated transition-colors modal-close">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
          <div class="relative w-32 h-32 mb-6">
            <img src="/static/logo.png" alt="Repo Rizz Logo" class="object-contain w-full h-full">
          </div>
          <h2 class="text-3xl font-bold tracking-tight mb-2 text-white">REPO <span class="text-lime">RIZZ</span></h2>
          <p class="text-sm text-gray-400 mb-6">AI-powered GitHub repository analysis and scoring engine.</p>
          <div class="w-full border-t border-border pt-6 flex justify-center space-x-6">
            <a href="https://github.com/krishna19072007/repo-rizz" target="_blank" rel="noopener noreferrer" class="text-xs font-mono tracking-wider text-gray-400 hover:text-lime transition-colors">SOURCE CODE</a>
            <a href="/about" class="text-xs font-mono tracking-wider text-gray-400 hover:text-lime transition-colors">ABOUT</a>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }

    // Footer
    if (!document.querySelector("footer.site-footer")) {
      const footer = document.createElement("footer");
      footer.className = "site-footer border-t border-border mt-auto py-8 bg-bg";
      footer.innerHTML = `
        <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <div class="flex flex-col items-center md:items-start text-center md:text-left">
            <span class="text-lg font-bold tracking-tight text-white">REPO <span class="text-lime">RIZZ</span></span>
            <p class="text-xs mt-1 text-gray-500">Advanced GitHub repository analysis for developers.</p>
            <!-- Discreet admin entry. Kept on the left, under the tagline:
                 the far-right corner of the footer sits under the floating
                 chat button and would make the link unclickable. -->
            <a href="/contributors/admin" class="mt-2 inline-flex items-center gap-1 text-[10px] font-mono tracking-widest text-gray-600 hover:text-lime transition-colors" title="Rizz Master access">
              <i data-lucide="shield" class="w-3 h-3"></i> RIZZ-MASTER?
            </a>
          </div>
          <div class="flex items-center gap-6">
            <a href="/about" class="text-sm text-gray-400 hover:text-lime transition-colors">About</a>
            <a href="/contributors" class="text-sm text-gray-400 hover:text-lime transition-colors">Contributors</a>
            <a href="/privacy" class="text-sm text-gray-400 hover:text-lime transition-colors">Privacy Policy</a>
            <a href="/login" class="text-sm text-gray-400 hover:text-lime transition-colors">Log In</a>
            <a href="https://github.com/krishna19072007/repo-rizz" target="_blank" rel="noopener noreferrer" class="text-sm text-gray-400 hover:text-lime transition-colors">GitHub</a>
          </div>
        </div>
      `;
      document.body.appendChild(footer);
    }

    // Add prefers-reduced-motion if not already present
    if (!document.getElementById("rr-reduced-motion")) {
      const style = document.createElement("style");
      style.id = "rr-reduced-motion";
      style.textContent = `
        @media (prefers-reduced-motion: reduce) {
          .reveal, .reveal-left, .reveal-right, .battle-left, .battle-right {
            opacity: 1 !important;
            transform: none !important;
            transition: none !important;
          }
          .animate-float-node-1, .animate-float-node-2, .animate-float-node-3, .animate-float-node-4,
          .radar-polygon, .radar-sweep-ring, .scanline-overlay, .pipeline-bead {
            animation: none !important;
          }
          .scroll-smooth { scroll-behavior: auto !important; }
        }
      `;
      document.head.appendChild(style);
    }

    // Remove any stale privacy buttons (they should now be links in the footer)
    document.querySelectorAll("button#privacy-btn").forEach(btn => {
      const link = document.createElement("a");
      link.href = "/privacy";
      link.className = btn.className.replace("cursor-not-allowed", "");
      link.textContent = btn.textContent;
      btn.replaceWith(link);
    });
  }

  injectSharedComponents();

  // ---- 2. Mobile hamburger menu ----
  function setupMobileNav() {
    const nav = document.querySelector("nav");
    if (!nav) return;

    // Find the nav links container (hidden on mobile)
    const navLinks = nav.querySelector('[class*="hidden"][class*="md:flex"]');
    if (!navLinks) return;

    // Create hamburger button
    const hamburger = document.createElement("button");
    hamburger.id = "mobile-nav-toggle";
    hamburger.className = "md:hidden p-2 rounded-lg text-gray-400 hover:text-white transition-colors focus:outline-none";
    hamburger.innerHTML = '<i data-lucide="menu" class="w-5 h-5"></i>';

    // Insert hamburger before the GitHub link in the right section
    const rightSection = nav.querySelector(".flex.items-center.gap-3");
    if (rightSection) {
      rightSection.prepend(hamburger);
    }

    // Make nav links toggleable on mobile
    navLinks.className = "hidden md:flex items-center gap-1";
    navLinks.id = "mobile-nav-links";

    // Create mobile overlay
    const mobileOverlay = document.createElement("div");
    mobileOverlay.id = "mobile-nav-overlay";
    mobileOverlay.className = "hidden fixed inset-0 z-40 md:hidden";
    mobileOverlay.innerHTML = `
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
      <div class="absolute top-16 left-0 right-0 border-b border-border p-4" style="background: rgba(7, 8, 9, 0.98);">
        <nav class="flex flex-col gap-1">
          ${navLinks.innerHTML}
        </nav>
      </div>
    `;
    document.body.appendChild(mobileOverlay);

    // Toggle behavior
    let isOpen = false;
    hamburger.addEventListener("click", () => {
      isOpen = !isOpen;
      if (isOpen) {
        mobileOverlay.classList.remove("hidden");
        hamburger.innerHTML = '<i data-lucide="x" class="w-5 h-5"></i>';
      } else {
        mobileOverlay.classList.add("hidden");
        hamburger.innerHTML = '<i data-lucide="menu" class="w-5 h-5"></i>';
      }
      if (typeof lucide !== "undefined") lucide.createIcons();
    });

    // Close on link click
    mobileOverlay.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        isOpen = false;
        mobileOverlay.classList.add("hidden");
        hamburger.innerHTML = '<i data-lucide="menu" class="w-5 h-5"></i>';
      });
    });

    // Close on escape
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isOpen) {
        isOpen = false;
        mobileOverlay.classList.add("hidden");
        hamburger.innerHTML = '<i data-lucide="menu" class="w-5 h-5"></i>';
      }
    });
  }

  // ---- 3. Setup mobile nav (before icon init so hamburger gets rendered)
  setupMobileNav();

  // ---- 4. Inject brand icons (Lucide removed brand icons like github) ----
  document.querySelectorAll('[data-lucide="github"]').forEach(el => {
    el.outerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>';
  });

  // ---- 5. Initialise Lucide Icons (AFTER all DOM injections) ----
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }

  // ---- 5. Brand Modal ----
  const logoBtn = document.getElementById("logo-btn");
  const brandModal = document.getElementById("brand-modal");

  if (logoBtn && brandModal) {
    logoBtn.addEventListener("click", () => {
      brandModal.classList.remove("hidden");
    });
  }

  // Close modals
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-close") && brandModal) {
      brandModal.classList.add("hidden");
    }
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && brandModal && !brandModal.classList.contains("hidden")) {
      brandModal.classList.add("hidden");
    }
  });

  // ---- 5. Input forms on homepage & demo triggering ----
  const analyzeForm = document.getElementById("analyze-form");
  const repoInput = document.getElementById("repo-input");
  const inputError = document.getElementById("input-error");
  const demoBtn = document.getElementById("demo-btn");

  if (analyzeForm && repoInput) {
    analyzeForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = repoInput.value.trim();
      const parsed = parseGitHubUrlHelper(val);
      if (!parsed) {
        if (inputError) {
          inputError.innerText = "That doesn't look like a valid public GitHub repository.";
          inputError.classList.remove("hidden");
        }
        return;
      }
      if (inputError) inputError.classList.add("hidden");
      // Analysis requires an account: gate before navigating (never calls
      // the API for a logged-out visitor).
      RR_AUTH.go(`/analyze?repo=${parsed.owner}/${parsed.name}`);
    });
  }

  if (demoBtn) {
    demoBtn.addEventListener("click", () => {
      RR_AUTH.go("/analyze?repo=krishna19072007/repo-rizz");
    });
  }

  // ---- 7. AI Chatbot ----
  function setupChatbot() {
    // Inject chatbot styles
    const chatStyle = document.createElement("style");
    chatStyle.id = "rr-chatbot-styles";
    chatStyle.textContent = `
      #chatbot-fab {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 90;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #b6ff42;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(182, 255, 66, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      #chatbot-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(182, 255, 66, 0.4); }
      #chatbot-fab:active { transform: scale(0.95); }
      #chatbot-fab svg { transition: transform 0.3s ease; }
      #chatbot-fab.open svg { transform: rotate(90deg); }

      #chatbot-panel {
        position: fixed;
        bottom: 92px;
        right: 24px;
        z-index: 90;
        width: 380px;
        max-width: calc(100vw - 32px);
        height: 520px;
        max-height: calc(100vh - 140px);
        border-radius: 20px;
        border: 1px solid #272a30;
        background: #0f1115;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        opacity: 0;
        transform: translateY(16px) scale(0.95);
        pointer-events: none;
        transition: opacity 0.25s ease, transform 0.25s ease;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
      }
      #chatbot-panel.open {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: auto;
      }

      .chat-header {
        padding: 16px 20px;
        border-bottom: 1px solid #272a30;
        display: flex;
        align-items: center;
        gap: 12px;
        background: #0f1115;
      }
      .chat-header-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #b6ff42;
        animation: chatPulse 2s ease-in-out infinite;
      }
      @keyframes chatPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }
      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        scroll-behavior: smooth;
      }
      .chat-messages::-webkit-scrollbar { width: 4px; }
      .chat-messages::-webkit-scrollbar-track { background: transparent; }
      .chat-messages::-webkit-scrollbar-thumb { background: #272a30; border-radius: 2px; }

      .chat-msg {
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 14px;
        font-size: 13px;
        line-height: 1.5;
        animation: msgIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      }
      @keyframes msgIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .chat-msg.bot {
        align-self: flex-start;
        background: #181b21;
        color: #e5e7eb;
        border-bottom-left-radius: 4px;
        border: 1px solid #272a30;
      }
      .chat-msg.user {
        align-self: flex-end;
        background: #b6ff42;
        color: #070809;
        border-bottom-right-radius: 4px;
        font-weight: 500;
      }
      .chat-msg a {
        color: #b6ff42;
        text-decoration: underline;
        text-underline-offset: 2px;
      }
      .chat-msg.user a { color: #070809; }

      .chat-typing {
        display: flex;
        gap: 4px;
        padding: 12px 14px;
        align-self: flex-start;
        background: #181b21;
        border-radius: 14px;
        border-bottom-left-radius: 4px;
        border: 1px solid #272a30;
      }
      .chat-typing span {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #6b7280;
        animation: typingBounce 1.2s ease-in-out infinite;
      }
      .chat-typing span:nth-child(2) { animation-delay: 0.15s; }
      .chat-typing span:nth-child(3) { animation-delay: 0.3s; }
      @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-4px); }
      }

      .chat-quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 0 16px 12px;
      }
      .chat-quick-btn {
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid #272a30;
        background: #181b21;
        color: #9ca3af;
        font-size: 11px;
        font-family: monospace;
        cursor: pointer;
        transition: all 0.15s ease;
        white-space: nowrap;
      }
      .chat-quick-btn:hover { border-color: #b6ff42; color: #b6ff42; background: rgba(182,255,66,0.05); }

      .chat-input-area {
        padding: 12px 16px;
        border-top: 1px solid #272a30;
        display: flex;
        gap: 8px;
        background: #0f1115;
      }
      .chat-input-area input {
        flex: 1;
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid #272a30;
        background: #181b21;
        color: #fff;
        font-size: 13px;
        font-family: monospace;
        outline: none;
        transition: border-color 0.2s;
      }
      .chat-input-area input:focus { border-color: #b6ff42; }
      .chat-input-area input::placeholder { color: #4b5563; }
      .chat-input-area button {
        padding: 10px 14px;
        border-radius: 10px;
        border: none;
        background: #b6ff42;
        color: #070809;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.15s;
        display: flex;
        align-items: center;
      }
      .chat-input-area button:hover { transform: scale(1.05); }
      .chat-input-area button:active { transform: scale(0.95); }

      @media (prefers-reduced-motion: reduce) {
        .chat-msg, #chatbot-panel, #chatbot-fab { animation: none !important; transition: none !important; }
        .chat-typing span { animation: none !important; }
        .chat-header-dot { animation: none !important; }
      }
    `;
    document.head.appendChild(chatStyle);

    // Inject chatbot HTML
    const fab = document.createElement("button");
    fab.id = "chatbot-fab";
    fab.setAttribute("aria-label", "Open chat assistant");
    fab.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#070809" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>`;

    const panel = document.createElement("div");
    panel.id = "chatbot-panel";
    panel.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-dot"></div>
        <div>
          <p style="font-size:13px;font-weight:700;color:#fff;">RIZZ BOT</p>
          <p style="font-size:10px;color:#6b7280;font-family:monospace;">AI Assistant · Always online</p>
        </div>
      </div>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="chat-quick-actions" id="chat-quick-actions"></div>
      <div class="chat-input-area">
        <input type="text" id="chat-input" placeholder="Ask about Repo Rizz..." autocomplete="off">
        <button id="chat-send" aria-label="Send message">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#070809" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>
        </button>
      </div>
    `;
    document.body.appendChild(fab);
    document.body.appendChild(panel);

    // ---- Knowledge Base ----
    const KB = [
      {
        keywords: ["what is", "what does", "about repo rizz", "tell me about"],
        response: `Repo Rizz is an AI-powered GitHub repository analysis engine. It inspects a public repo's documentation, code quality, architecture, and security — then generates a <strong>Resume Readiness Score</strong> to help you understand how strong your project looks to recruiters and faculty.`
      },
      {
        keywords: ["how does it work", "how to use", "getting started", "analyze"],
        response: `Just paste a GitHub repository link and hit <strong>Analyze</strong>. Repo Rizz fetches real data via the GitHub API, runs it through 4 analysis dimensions (Documentation, Code Quality, Architecture, Security), calculates scores, and generates AI-powered insights — all in seconds.<br><br><a href="/analyze">Try it now →</a>`
      },
      {
        keywords: ["score", "readiness", "resume", "rating"],
        response: `The <strong>Resume Readiness Score</strong> (0–100) combines all 4 dimensions into a single verdict:<br>• <span style="color:#b6ff42">80+ READY</span> — Your repo is polished and presentation-ready<br>• <span style="color:#8b5cf6">60–79 ALMOST READY</span> — Strong foundation, minor gaps<br>• <span style="color:#ff5c5c">Below 60 NEEDS WORK</span> — Several areas need improvement`
      },
      {
        keywords: ["dimension", "documentation", "code quality", "architecture", "security"],
        response: `Repo Rizz evaluates 4 engineering dimensions:<br>• <strong>Documentation</strong> — README quality, install instructions, examples<br>• <strong>Code Quality</strong> — Linting, formatting, CI/CD setup<br>• <strong>Architecture</strong> — Module separation, project structure<br>• <strong>Security</strong> — Secrets detection, dependency audit, security policies`
      },
      {
        keywords: ["history", "past analysis", "previous"],
        response: `Your analysis history is saved locally in your browser. Visit the <a href="/history">History</a> page to see all past analyses, search by repo name, sort by score, or delete entries.`
      },
      {
        keywords: ["compare", "battle", "vs", "versus"],
        response: `Use <a href="/compare">Repo Battle</a> to compare two repositories side-by-side. It evaluates both across all dimensions and declares a winner based on Resume Readiness Score.`
      },
      {
        keywords: ["private repo", "private", "non-public"],
        response: `Repo Rizz currently only supports <strong>public</strong> GitHub repositories. Private repos require authentication tokens which aren't supported yet. We're considering adding this in a future update!`
      },
      {
        keywords: ["free", "cost", "price", "pay"],
        response: `Repo Rizz is <strong>100% free</strong> and open source! You can check out the source code on <a href="https://github.com/krishna19072007/repo-rizz" target="_blank">GitHub</a>.`
      },
      {
        keywords: ["ai", "gemini", "artificial intelligence", "machine learning"],
        response: `Repo Rizz uses <strong>Gemini AI</strong> to interpret analysis findings and generate contextual insights. However, the core scoring logic is deterministic — scores are based on real repository signals, not AI guesses.`
      },
      {
        keywords: ["tech stack", "built with", "technology", "framework"],
        response: `Repo Rizz is built with:<br>• <strong>Frontend</strong> — Vanilla HTML/CSS/JS with Tailwind CSS<br>• <strong>Backend</strong> — Python FastAPI<br>• <strong>AI</strong> — Google Gemini for insights<br>• <strong>Data</strong> — GitHub REST API for repo metadata`
      },
      {
        keywords: ["hello", "hi", "hey", "sup", "greetings"],
        response: `Hey! 👋 I'm Rizz Bot, your Repo Rizz assistant. I can help you understand how the analysis works, explain scores, or guide you to the right feature. What would you like to know?`
      },
      {
        keywords: ["thank", "thanks", "appreciate"],
        response: `You're welcome! 😊 Feel free to ask anything else about Repo Rizz. Happy analyzing!`
      },
      {
        keywords: ["bug", "issue", "problem", "error", "broken"],
        response: `Sorry to hear that! If you're experiencing a bug, please open an issue on <a href="https://github.com/krishna19072007/repo-rizz/issues" target="_blank">GitHub Issues</a> with details about what happened. We'll look into it!`
      }
    ];

    // Context-aware responses (for analyze page)
    const contextResponses = {
      analyze: [
        {
          keywords: ["my score", "this score", "my result", "interpret", "explain score", "what does my"],
          response: `Your Resume Readiness Score is calculated from 4 weighted dimensions. Scroll down to the <strong>Dimension Breakdown</strong> section to see individual scores. The <strong>Rizz Verdict</strong> gives you a plain-language interpretation. Need help understanding a specific dimension?`
        }
      ]
    };

    function getSmartResponse(input) {
      const lower = input.toLowerCase().trim();

      // Check context-specific responses first
      const isAnalyzePage = window.location.pathname === "/analyze" || window.location.pathname.startsWith("/analyze");
      if (isAnalyzePage && contextResponses.analyze) {
        for (const entry of contextResponses.analyze) {
          if (entry.keywords.some(kw => lower.includes(kw))) {
            return entry.response;
          }
        }
      }

      // Check knowledge base
      for (const entry of KB) {
        if (entry.keywords.some(kw => lower.includes(kw))) {
          return entry.response;
        }
      }

      // Fuzzy match: check if any individual word matches
      const words = lower.split(/\s+/);
      for (const entry of KB) {
        for (const word of words) {
          if (word.length > 3 && entry.keywords.some(kw => kw.includes(word) || word.includes(kw))) {
            return entry.response;
          }
        }
      }

      // Default
      return `I'm not sure about that! Try asking about:<br>• How Repo Rizz works<br>• What the scores mean<br>• How to analyze a repo<br>• Compare repositories<br>• Or type <strong>"features"</strong> for a full overview`;
    }

    // ---- UI Logic ----
    const messages = document.getElementById("chat-messages");
    const quickActions = document.getElementById("chat-quick-actions");
    const chatInput = document.getElementById("chat-input");
    const chatSend = document.getElementById("chat-send");
    let chatOpen = false;
    let hasGreeted = false;

    function addMessage(text, type) {
      const div = document.createElement("div");
      div.className = `chat-msg ${type}`;
      div.innerHTML = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function showTyping() {
      const div = document.createElement("div");
      div.className = "chat-typing";
      div.id = "chat-typing";
      div.innerHTML = "<span></span><span></span><span></span>";
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function removeTyping() {
      const el = document.getElementById("chat-typing");
      if (el) el.remove();
    }

    function showQuickActions() {
      const isAnalyzePage = window.location.pathname === "/analyze" || window.location.pathname.startsWith("/analyze");
      const actions = isAnalyzePage
        ? ["Explain my score", "What are dimensions?", "How to improve?", "Compare repos"]
        : ["What is Repo Rizz?", "How does it work?", "It's free!", "Compare repos"];

      quickActions.innerHTML = actions.map(a =>
        `<button class="chat-quick-btn" data-msg="${a}">${a}</button>`
      ).join("");

      quickActions.querySelectorAll(".chat-quick-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          sendMessage(btn.getAttribute("data-msg"));
        });
      });
    }

    function sendMessage(text) {
      if (!text || !text.trim()) return;
      addMessage(text, "user");
      chatInput.value = "";
      quickActions.innerHTML = "";

      // Typing delay for realism
      showTyping();
      const delay = 400 + Math.random() * 600;
      setTimeout(() => {
        removeTyping();
        const response = getSmartResponse(text);
        addMessage(response, "bot");
        showQuickActions();
      }, delay);
    }

    // Greeting
    function greet() {
      if (hasGreeted) return;
      hasGreeted = true;
      const hour = new Date().getHours();
      const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
      addMessage(`${greeting}! 👋 I'm <strong>Rizz Bot</strong>, your Repo Rizz assistant. Ask me anything about the platform, or try a quick action below.`, "bot");
      showQuickActions();
    }

    // Toggle
    fab.addEventListener("click", () => {
      chatOpen = !chatOpen;
      if (chatOpen) {
        panel.classList.add("open");
        fab.classList.add("open");
        fab.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#070809" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
        chatInput.focus();
        greet();
      } else {
        panel.classList.remove("open");
        fab.classList.remove("open");
        fab.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#070809" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>`;
      }
    });

    // Send
    chatSend.addEventListener("click", () => sendMessage(chatInput.value));
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(chatInput.value);
      }
    });

    // Escape closes
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && chatOpen) {
        chatOpen = false;
        panel.classList.remove("open");
        fab.classList.remove("open");
        fab.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#070809" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>`;
      }
    });
  }

  setupChatbot();
})();

