// Shared Frontend Script for Repo Rizz

document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialise Lucide Icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  // 2. Brand Modal Toggle Behavior
  const logoBtn = document.getElementById("logo-btn");
  const brandModal = document.getElementById("brand-modal");

  if (logoBtn && brandModal) {
    logoBtn.addEventListener("click", () => {
      brandModal.classList.remove("hidden");
    });
  }

  // Close modals
  const modalCloses = document.querySelectorAll(".modal-close");
  modalCloses.forEach(btn => {
    btn.addEventListener("click", () => {
      if (brandModal) brandModal.classList.add("hidden");
    });
  });

  // Close modal on Escape key
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && brandModal && !brandModal.classList.contains("hidden")) {
      brandModal.classList.add("hidden");
    }
  });

  // 3. Privacy Policy Coming Soon Dialog
  const privacyBtns = document.querySelectorAll("#privacy-btn");
  privacyBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      alert("Privacy Policy — Coming Soon");
    });
  });

  // 4. Input forms on homepage & demo triggering
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
      window.location.href = `/analyze?repo=${parsed.owner}/${parsed.name}`;
    });
  }

  if (demoBtn) {
    demoBtn.addEventListener("click", () => {
      window.location.href = "/analyze?repo=krishna19072007/repo-rizz";
    });
  }

  // Helper parsing function matching backend
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
});
