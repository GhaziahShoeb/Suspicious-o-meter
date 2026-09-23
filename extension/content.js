// ---- Config ----
const SCAN_ENDPOINT = "http://127.0.0.1:8000/scan";
const DEBOUNCE_MS = 800;

let lastScannedHash = null;
let debounceTimer = null;

// ---- Detection ----
function isJobPostingPage() {
  const url = window.location.href;
  return url.includes("linkedin.com/jobs") || url.includes("indeed.com/viewjob");
}

function isGmailPage() {
  return window.location.href.includes("mail.google.com");
}

// ---- Extraction (site-specific selectors, with a generic fallback) ----
function extractPostingText() {
  if (isGmailPage()) {
    const emailBody = document.querySelector(".a3s, .ii.gt");
    if (emailBody && emailBody.innerText.length > 30) {
      return emailBody.innerText.trim();
    }
    return null; // no email open yet
  }

  const linkedinBox = document.querySelector(".jobs-description__content, .jobs-box__html-content");
  if (linkedinBox && linkedinBox.innerText.length > 50) {
    return linkedinBox.innerText.trim();
  }

  const indeedBox = document.querySelector("#jobDescriptionText, .jobsearch-jobDescriptionText");
  if (indeedBox && indeedBox.innerText.length > 50) {
    return indeedBox.innerText.trim();
  }

  // Generic fallback - messy but non-empty
  return document.body.innerText.slice(0, 8000).trim();
}

// ---- Simple string hash (for client-side dedup, not security) ----
function hashText(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = (hash << 5) - hash + text.charCodeAt(i);
    hash |= 0;
  }
  return hash.toString();
}

// ---- Respond to popup asking for extracted text ----
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "getPostingText") {
    sendResponse({ text: extractPostingText() });
  }
  return true;
});

// ---- Floating banner ----
function showBanner(verdict, score) {
  const existing = document.getElementById("suspicious-o-meter-banner");
  if (existing) existing.remove(); // replace, don't stack duplicates

  const banner = document.createElement("div");
  banner.id = "suspicious-o-meter-banner";
  banner.style.cssText = `
    position: fixed; top: 10px; right: 10px; z-index: 999999;
    background: ${score >= 50 ? "#fde2e2" : score >= 20 ? "#fff4cc" : "#e2f7e2"};
    border: 1px solid #999; border-radius: 8px; padding: 10px 14px;
    font-family: sans-serif; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  `;
  banner.textContent = `Suspicious-o-meter: ${verdict} (${score}/100)`;
  document.body.appendChild(banner);
}
let currentBannerData = null;

function ensureBannerPersists() {
  if (!currentBannerData) return;
  if (!document.getElementById("suspicious-o-meter-banner")) {
    showBanner(currentBannerData.verdict, currentBannerData.score);
  }
}

setInterval(ensureBannerPersists, 2000); // check every 2 seconds

// ---- Run a scan (debounced + deduped) ----
function scheduleScan() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runScan, DEBOUNCE_MS);
}

function runScan() {
  if (!isJobPostingPage() && !isGmailPage()) return;

  const text = extractPostingText();
  if (!text) return; // nothing to scan yet (e.g. Gmail with no email open)

  const currentHash = hashText(text);
  if (currentHash === lastScannedHash) return; // already scanned this exact content
  lastScannedHash = currentHash;

  console.log("Suspicious-o-meter: scanning content (first 300 chars):", text.slice(0, 300));

fetch(SCAN_ENDPOINT, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ url: window.location.href, text })
})
  .then(res => {
    if (!res.ok) {
      console.log("Suspicious-o-meter: request failed or rate limited, status:", res.status);
      return null;
    }
    return res.json();
  })
  .then(data => {
    if (!data) return;
    chrome.runtime.sendMessage({ action: "updateBadge", score: data.suspicion_score });
    showBanner(data.verdict, data.suspicion_score);
  })
  .catch(err => console.log("Suspicious-o-meter: scan failed", err));
}

// ---- Initial run ----
scheduleScan();

// ---- MutationObserver: re-scan when Gmail (or LinkedIn's SPA nav) changes content ----
const observer = new MutationObserver(() => {
  scheduleScan();
});
observer.observe(document.body, { childList: true, subtree: true });