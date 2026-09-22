// ---- Config ----
const SCAN_ENDPOINT = "http://127.0.0.1:8000/scan";
const DEBOUNCE_MS = 1000;

let lastScannedHash = null;
let debounceTimer = null;
let shadowHost = null;

// ---- Detection ----
function isJobPostingPage() {
  const url = window.location.href;
  return url.includes("linkedin.com/jobs") || url.includes("indeed.com/viewjob");
}

function isGmailPage() {
  return window.location.href.includes("mail.google.com");
}

// ---- Extraction (site-specific selectors with user privacy preserved) ----
function extractPostingText() {
  if (isGmailPage()) {
    const emailBody = document.querySelector(".a3s, .ii.gt");
    if (emailBody && emailBody.innerText.length > 30) {
      return emailBody.innerText.trim();
    }
    return null;
  }

  const linkedinBox = document.querySelector(".jobs-description__content, .jobs-box__html-content");
  if (linkedinBox && linkedinBox.innerText.length > 50) {
    return linkedinBox.innerText.trim();
  }

  const indeedBox = document.querySelector("#jobDescriptionText, .jobsearch-jobDescriptionText");
  if (indeedBox && indeedBox.innerText.length > 50) {
    return indeedBox.innerText.trim();
  }

  if (isJobPostingPage()) {
    return document.body.innerText.slice(0, 8000).trim();
  }

  return null;
}

// ---- Simple string hash (for client-side dedup) ----
function hashText(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = (hash << 5) - hash + text.charCodeAt(i);
    hash |= 0;
  }
  return hash.toString();
}

// ---- Closed Shadow DOM Security Banner (Tamper-Proof) ----
function showBanner(verdict, score) {
  if (shadowHost) {
    shadowHost.remove();
  }

  shadowHost = document.createElement("div");
  shadowHost.id = "som-security-root-" + Math.random().toString(36).slice(2, 7);

  // Attach a closed shadow root so host scripts cannot access or alter its children
  const shadow = shadowHost.attachShadow({ mode: "closed" });

  const container = document.createElement("div");
  container.style.cssText = `
    position: fixed;
    top: 14px;
    right: 14px;
    z-index: 2147483647;
    background: ${score >= 50 ? "#fef2f2" : score >= 20 ? "#fffbeb" : "#f0fdf4"};
    color: ${score >= 50 ? "#991b1b" : score >= 20 ? "#92400e" : "#166534"};
    border: 1px solid ${score >= 50 ? "#f87171" : score >= 20 ? "#fcd34d" : "#86efac"};
    border-radius: 8px;
    padding: 10px 16px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 8px;
    pointer-events: auto;
  `;

  const icon = document.createElement("span");
  icon.textContent = score >= 50 ? "🚨" : score >= 20 ? "⚠️" : "🛡️";

  const text = document.createElement("span");
  text.textContent = `Suspicious-o-meter: ${verdict} (${score}/100)`;

  const closeBtn = document.createElement("button");
  closeBtn.textContent = "×";
  closeBtn.style.cssText = `
    background: none;
    border: none;
    color: inherit;
    font-size: 16px;
    cursor: pointer;
    padding: 0 0 0 6px;
    line-height: 1;
  `;
  closeBtn.onclick = () => shadowHost.remove();

  container.appendChild(icon);
  container.appendChild(text);
  container.appendChild(closeBtn);
  shadow.appendChild(container);

  document.documentElement.appendChild(shadowHost);
}

// ---- Respond to popup asking for extracted text ----
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "getPostingText") {
    sendResponse({ text: extractPostingText() });
  }
  return true;
});

// ---- Run automatic scan (Only on Job Posting Pages, never auto on Gmail) ----
function scheduleScan() {
  if (!isJobPostingPage()) return;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runScan, DEBOUNCE_MS);
}

function runScan() {
  if (!isJobPostingPage()) return;

  const text = extractPostingText();
  if (!text || text.length < 50) return;

  const currentHash = hashText(text);
  if (currentHash === lastScannedHash) return;
  lastScannedHash = currentHash;

  fetch(SCAN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: window.location.href, text })
  })
    .then(res => {
      if (res.status === 429) {
        console.warn("Suspicious-o-meter: Rate limit reached (10 scans/min).");
        return null;
      }
      if (!res.ok) {
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data || data.verdict === "ERROR") return;
      chrome.runtime.sendMessage({ action: "updateBadge", score: data.suspicion_score });
      showBanner(data.verdict, data.suspicion_score);
    })
    .catch(() => {
      // Backend not running or unreachable
    });
}

// Auto-run only on initial load for job boards
if (isJobPostingPage()) {
  scheduleScan();

  // Watch for job board SPA navigation
  const observer = new MutationObserver(() => {
    scheduleScan();
  });
  observer.observe(document.body, { childList: true, subtree: true });
}